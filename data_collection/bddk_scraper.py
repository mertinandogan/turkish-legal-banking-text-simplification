"""
BDDK Document Scraper

Collects banking regulation documents from BDDK (Banking Regulation and 
Supervision Agency of Turkey) using the existing bddk_mcp_module client.
Saves raw documents in Markdown format for downstream processing.
"""

import asyncio
import io
import json
import logging
import os
import sys
import argparse
import re
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

import httpx
import yaml
from bs4 import BeautifulSoup
from pypdf import PdfReader

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bddk_mcp_module.client import BddkApiClient

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def load_config(config_path: str = "configs/default.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


async def scrape_bddk_documents(
    doc_id_start: int = 1,
    doc_id_end: int = 500,
    output_dir: str = "data/raw",
    request_delay: float = 1.0,
    request_timeout: float = 60.0,
    max_concurrent: int = 3,
) -> dict:
    """
    Scrape BDDK documents by iterating through document IDs.
    
    Args:
        doc_id_start: Starting document ID
        doc_id_end: Ending document ID (inclusive)
        output_dir: Directory to save raw documents
        request_delay: Delay between requests in seconds
        request_timeout: Request timeout in seconds
        max_concurrent: Maximum concurrent requests
        
    Returns:
        Dictionary with scraping statistics
    """
    os.makedirs(output_dir, exist_ok=True)
    
    client = BddkApiClient(request_timeout=request_timeout)
    semaphore = asyncio.Semaphore(max_concurrent)
    
    stats = {
        "total_attempted": 0,
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "failed_ids": [],
    }
    
    async def fetch_document(doc_id: int):
        """Fetch a single document with rate limiting."""
        async with semaphore:
            stats["total_attempted"] += 1
            
            # Skip if already downloaded
            output_file = os.path.join(output_dir, f"bddk_{doc_id}.md")
            metadata_file = os.path.join(output_dir, f"bddk_{doc_id}.json")
            
            if os.path.exists(output_file):
                logger.debug(f"Document {doc_id} already exists, skipping")
                stats["skipped"] += 1
                return
            
            try:
                # Fetch all pages of the document
                full_content = []
                page = 1
                
                while True:
                    result = await client.get_document_markdown(
                        document_id=str(doc_id),
                        page_number=page
                    )
                    
                    if not result.markdown_content.strip():
                        break
                    
                    full_content.append(result.markdown_content)
                    
                    if page >= result.total_pages:
                        break
                    page += 1
                
                if full_content:
                    # Save content
                    content = "\n".join(full_content)
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(content)
                    
                    # Save metadata
                    metadata = {
                        "document_id": str(doc_id),
                        "total_pages": result.total_pages,
                        "content_length": len(content),
                        "source_url": f"https://www.bddk.org.tr/Mevzuat/DokumanGetir/{doc_id}",
                    }
                    with open(metadata_file, "w", encoding="utf-8") as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)
                    
                    stats["successful"] += 1
                    logger.info(
                        f"✅ Document {doc_id}: {len(content)} chars, "
                        f"{result.total_pages} pages"
                    )
                else:
                    stats["failed"] += 1
                    stats["failed_ids"].append(doc_id)
                    logger.warning(f"⚠️ Document {doc_id}: empty content")
                    
            except Exception as e:
                stats["failed"] += 1
                stats["failed_ids"].append(doc_id)
                logger.error(f"❌ Document {doc_id}: {str(e)[:100]}")
            
            # Rate limiting
            await asyncio.sleep(request_delay)
    
    # Create tasks for all document IDs
    logger.info(
        f"Starting BDDK scrape: IDs {doc_id_start}-{doc_id_end} "
        f"({doc_id_end - doc_id_start + 1} documents)"
    )
    
    tasks = [
        fetch_document(doc_id)
        for doc_id in range(doc_id_start, doc_id_end + 1)
    ]
    
    await asyncio.gather(*tasks)
    
    # Cleanup
    await client.close_client_session()
    
    # Save stats
    stats_file = os.path.join(output_dir, "_scrape_stats.json")
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    logger.info(
        f"\n📊 Scraping complete:\n"
        f"   Attempted: {stats['total_attempted']}\n"
        f"   Successful: {stats['successful']}\n"
        f"   Failed: {stats['failed']}\n"
        f"   Skipped: {stats['skipped']}"
    )
    
    return stats


async def search_and_scrape(
    keywords: list[str],
    output_dir: str = "data/raw",
    request_delay: float = 1.0,
    request_timeout: float = 60.0,
) -> dict:
    """
    Search BDDK for specific keywords and scrape found documents.
    Useful for targeted collection of banking regulation documents.
    
    Args:
        keywords: List of search keywords
        output_dir: Output directory
        request_delay: Delay between requests
        request_timeout: Request timeout
        
    Returns:
        Dictionary with scraping statistics
    """
    from bddk_mcp_module.models import BddkSearchRequest
    
    os.makedirs(output_dir, exist_ok=True)
    client = BddkApiClient(request_timeout=request_timeout)
    
    all_doc_ids = set()
    
    for keyword in keywords:
        logger.info(f"Searching BDDK for: '{keyword}'")
        try:
            request = BddkSearchRequest(
                keywords=keyword,
                page=1,
                pageSize=50
            )
            result = await client.search_decisions(request)
            
            for decision in result.decisions:
                all_doc_ids.add(int(decision.document_id))
                logger.info(
                    f"  Found: {decision.title[:80]} (ID: {decision.document_id})"
                )
                
        except Exception as e:
            logger.error(f"Search failed for '{keyword}': {e}")
        
        await asyncio.sleep(request_delay)
    
    logger.info(f"Found {len(all_doc_ids)} unique documents from keyword search")
    
    # Now scrape each found document
    if all_doc_ids:
        # Use the main scraper for individual IDs
        for doc_id in sorted(all_doc_ids):
            try:
                await scrape_bddk_documents(
                    doc_id_start=doc_id,
                    doc_id_end=doc_id,
                    output_dir=output_dir,
                    request_delay=request_delay,
                    request_timeout=request_timeout,
                )
            except Exception as e:
                logger.error(f"Failed to scrape document {doc_id}: {e}")
    
    await client.close_client_session()
    
    return {"found_documents": len(all_doc_ids), "doc_ids": sorted(all_doc_ids)}


def _extract_mevzuat_id(source_url: str) -> str:
    """Extract a stable ID from mevzuat.gov.tr URL."""
    parsed = urlparse(source_url)
    qs = parse_qs(parsed.query)
    mevzuat_no = qs.get("MevzuatNo", [""])[0].strip()
    if mevzuat_no:
        return mevzuat_no

    # Fallback: sanitize full URL if query param is missing
    sanitized = re.sub(r"[^a-zA-Z0-9]+", "_", source_url).strip("_")
    return sanitized[:80] or "external_source"


async def scrape_direct_urls(
    source_urls: list[str],
    output_dir: str = "data/raw",
    request_timeout: float = 60.0,
) -> dict:
    """
    Scrape direct regulation URLs and save as markdown/text for dataset inclusion.
    """
    os.makedirs(output_dir, exist_ok=True)
    stats = {"total_attempted": 0, "successful": 0, "failed": 0, "failed_urls": []}

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    async with httpx.AsyncClient(timeout=request_timeout, follow_redirects=True, headers=headers) as client:
        for source_url in source_urls:
            stats["total_attempted"] += 1
            source_id = _extract_mevzuat_id(source_url)
            output_file = os.path.join(output_dir, f"bddk_{source_id}.md")
            metadata_file = os.path.join(output_dir, f"bddk_{source_id}.json")

            try:
                response = await client.get(source_url)
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                if "pdf" in content_type or source_url.lower().endswith(".pdf"):
                    pdf_reader = PdfReader(io.BytesIO(response.content))
                    text_content = "\n".join(page.extract_text() or "" for page in pdf_reader.pages).strip()
                else:
                    soup = BeautifulSoup(response.text, "html.parser")
                    text_content = soup.get_text("\n", strip=True)

                if not text_content:
                    raise ValueError("empty page content")

                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(text_content)

                metadata = {
                    "document_id": source_id,
                    "source_url": source_url,
                    "content_length": len(text_content),
                    "source_type": "direct_url",
                }
                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)

                stats["successful"] += 1
                logger.info("✅ Direct source %s saved (%d chars)", source_id, len(text_content))
            except Exception as e:
                stats["failed"] += 1
                stats["failed_urls"].append(source_url)
                logger.error("❌ Direct source failed %s: %s", source_url, str(e)[:140])

    return stats


def main():
    """CLI entry point for BDDK document scraping."""
    parser = argparse.ArgumentParser(
        description="Scrape BDDK banking regulation documents"
    )
    parser.add_argument(
        "--config", default="configs/default.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--mode", choices=["range", "search", "test", "urls"],
        default="range",
        help="Scraping mode: range, search, test, urls (direct configured URLs)"
    )
    parser.add_argument(
        "--start", type=int, default=None,
        help="Starting document ID (range mode)"
    )
    parser.add_argument(
        "--end", type=int, default=None,
        help="Ending document ID (range mode)"
    )
    parser.add_argument(
        "--keywords", nargs="+", default=None,
        help="Search keywords (search mode)"
    )
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    bddk_config = config["data_collection"]["bddk"]
    
    if args.mode == "test":
        # Quick test with a few documents
        logger.info("🧪 Running test mode (IDs 300-310)")
        asyncio.run(scrape_bddk_documents(
            doc_id_start=300,
            doc_id_end=310,
            output_dir=bddk_config["raw_output_dir"],
            request_delay=bddk_config["request_delay_seconds"],
            request_timeout=bddk_config["request_timeout_seconds"],
        ))
    elif args.mode == "search":
        keywords = args.keywords or [
            "sermaye yeterliliği",
            "kredi riski",
            "likidite oranı",
            "bankacılık düzenlemesi",
            "mevduat sigortası",
        ]
        asyncio.run(search_and_scrape(
            keywords=keywords,
            output_dir=bddk_config["raw_output_dir"],
            request_delay=bddk_config["request_delay_seconds"],
            request_timeout=bddk_config["request_timeout_seconds"],
        ))
    elif args.mode == "urls":
        direct_urls = bddk_config.get("direct_source_urls", [])
        if not direct_urls:
            logger.warning("No direct_source_urls configured in config file.")
            return
        asyncio.run(scrape_direct_urls(
            source_urls=direct_urls,
            output_dir=bddk_config["raw_output_dir"],
            request_timeout=bddk_config["request_timeout_seconds"],
        ))
    else:
        # Range mode
        start = args.start or bddk_config["doc_id_start"]
        end = args.end or bddk_config["doc_id_end"]
        asyncio.run(scrape_bddk_documents(
            doc_id_start=start,
            doc_id_end=end,
            output_dir=bddk_config["raw_output_dir"],
            request_delay=bddk_config["request_delay_seconds"],
            request_timeout=bddk_config["request_timeout_seconds"],
            max_concurrent=bddk_config["max_concurrent_requests"],
        ))


if __name__ == "__main__":
    main()
