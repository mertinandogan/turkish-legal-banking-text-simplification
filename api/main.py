"""
Banking Regulation Simplification — Web API

FastAPI backend serving the NLP pipeline through a RESTful API.
Provides endpoints for text simplification, dataset stats, and model comparison.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.baseline.textrank_summarizer import TextRankSummarizer
from models.baseline.tfidf_summarizer import TfidfSummarizer
from evaluation.hallucination_detector import detect_hallucinations
from evaluation.faithfulness_checker import compute_tfidf_similarity
from data_collection.paragraph_extractor import compute_jargon_density, compute_complexity_score

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- App Setup ---
app = FastAPI(
    title="Banking Regulation Simplifier",
    description="Türk Bankacılık Düzenlemelerini Yapay Zeka ile Sadeleştirme Sistemi",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files & templates
STATIC_DIR = PROJECT_ROOT / "web" / "static"
TEMPLATES_DIR = PROJECT_ROOT / "web" / "templates"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# --- Models (lazy init) ---
_textrank = None
_tfidf = None


def get_textrank():
    global _textrank
    if _textrank is None:
        _textrank = TextRankSummarizer(num_sentences=3)
    return _textrank


def get_tfidf():
    global _tfidf
    if _tfidf is None:
        _tfidf = TfidfSummarizer(num_sentences=3)
    return _tfidf


# --- Request/Response Models ---
class SimplifyRequest(BaseModel):
    text: str = Field(..., min_length=30, description="Sadeleştirilecek karmaşık metin")
    models: list[str] = Field(
        default=["textrank", "tfidf"],
        description="Kullanılacak modeller"
    )


class SimplifyResult(BaseModel):
    model: str
    simplified: str
    original_length: int
    simplified_length: int
    compression_ratio: float
    hallucination_score: float
    faithfulness_score: float
    term_preservation_rate: float


class TextAnalysis(BaseModel):
    text: str
    char_count: int
    word_count: int
    sentence_count: int
    jargon_density: float
    complexity_score: float
    complexity_level: str


# --- API Routes ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main web interface."""
    return templates.TemplateResponse(request, "index.html")


@app.post("/api/simplify")
async def simplify_text(req: SimplifyRequest):
    """Simplify banking regulation text using selected models."""
    results = []

    for model_name in req.models:
        if model_name == "textrank":
            summarizer = get_textrank()
            simplified = summarizer.summarize(req.text)
        elif model_name == "tfidf":
            summarizer = get_tfidf()
            simplified = summarizer.summarize(req.text)
        else:
            continue

        # Evaluate
        hall = detect_hallucinations(req.text, simplified)
        faith_sim = compute_tfidf_similarity(req.text, simplified)

        results.append(SimplifyResult(
            model=model_name,
            simplified=simplified,
            original_length=len(req.text),
            simplified_length=len(simplified),
            compression_ratio=round(len(simplified) / max(len(req.text), 1), 3),
            hallucination_score=hall["hallucination_score"],
            faithfulness_score=round(faith_sim, 4),
            term_preservation_rate=hall["term_preservation"]["preservation_rate"],
        ))

    return {"results": results}


@app.post("/api/analyze")
async def analyze_text(req: SimplifyRequest):
    """Analyze the complexity of a banking regulation text."""
    import re
    text = req.text
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]

    density = compute_jargon_density(text)
    complexity = compute_complexity_score(text)

    if complexity >= 3:
        level = "Çok Karmaşık"
    elif complexity >= 1.5:
        level = "Karmaşık"
    elif complexity >= 0.5:
        level = "Orta"
    else:
        level = "Basit"

    return TextAnalysis(
        text=text,
        char_count=len(text),
        word_count=len(text.split()),
        sentence_count=len(sentences),
        jargon_density=round(density, 4),
        complexity_score=round(complexity, 2),
        complexity_level=level,
    )


@app.get("/api/stats")
async def get_dataset_stats():
    """Get current dataset statistics."""
    data_dir = PROJECT_ROOT / "data"

    # Raw documents
    raw_dir = data_dir / "raw"
    raw_count = len(list(raw_dir.glob("bddk_*.md"))) if raw_dir.exists() else 0

    # Paragraphs
    para_file = data_dir / "paragraphs" / "complex_paragraphs.jsonl"
    para_count = 0
    avg_jargon = 0
    avg_complexity = 0
    if para_file.exists():
        with open(para_file) as f:
            paragraphs = [json.loads(line) for line in f if line.strip()]
        para_count = len(paragraphs)
        if paragraphs:
            avg_jargon = sum(p["metadata"]["jargon_density"] for p in paragraphs) / len(paragraphs)
            avg_complexity = sum(p["metadata"]["complexity_score"] for p in paragraphs) / len(paragraphs)

    # Parallel dataset
    parallel_dir = data_dir / "parallel"
    train_count = _count_jsonl(parallel_dir / "train.jsonl")
    val_count = _count_jsonl(parallel_dir / "val.jsonl")
    test_count = _count_jsonl(parallel_dir / "test_gold.jsonl")

    # Results
    results_dir = PROJECT_ROOT / "results"
    baseline_scores = _load_json(results_dir / "baseline_scores.json")
    neural_scores = _load_json(results_dir / "neural_scores.json")

    return {
        "data": {
            "raw_documents": raw_count,
            "extracted_paragraphs": para_count,
            "avg_jargon_density": round(avg_jargon, 4),
            "avg_complexity_score": round(avg_complexity, 2),
            "train_pairs": train_count,
            "val_pairs": val_count,
            "test_pairs": test_count,
        },
        "models": {
            "baseline": baseline_scores,
            "neural": neural_scores,
        }
    }


@app.get("/api/paragraphs")
async def get_paragraphs(limit: int = 20, offset: int = 0):
    """Get extracted paragraphs from the dataset."""
    para_file = PROJECT_ROOT / "data" / "paragraphs" / "complex_paragraphs.jsonl"
    if not para_file.exists():
        return {"paragraphs": [], "total": 0}

    with open(para_file) as f:
        all_paras = [json.loads(line) for line in f if line.strip()]

    total = len(all_paras)
    paras = all_paras[offset:offset + limit]

    return {"paragraphs": paras, "total": total, "offset": offset, "limit": limit}


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    with open(path) as f:
        return sum(1 for line in f if line.strip())


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)
