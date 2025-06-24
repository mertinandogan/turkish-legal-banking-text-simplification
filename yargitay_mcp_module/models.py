# yargitay_mcp_module/models.py

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any, Literal

# Yargıtay Chamber/Board Options
YargitayBirimEnum = Literal[
    "",  # Empty string for "All" chambers
    # Hukuk (Civil) Chambers
    "Hukuk Genel Kurulu",
    "1. Hukuk Dairesi", "2. Hukuk Dairesi", "3. Hukuk Dairesi", "4. Hukuk Dairesi",
    "5. Hukuk Dairesi", "6. Hukuk Dairesi", "7. Hukuk Dairesi", "8. Hukuk Dairesi",
    "9. Hukuk Dairesi", "10. Hukuk Dairesi", "11. Hukuk Dairesi", "12. Hukuk Dairesi",
    "13. Hukuk Dairesi", "14. Hukuk Dairesi", "15. Hukuk Dairesi", "16. Hukuk Dairesi",
    "17. Hukuk Dairesi", "18. Hukuk Dairesi", "19. Hukuk Dairesi", "20. Hukuk Dairesi",
    "21. Hukuk Dairesi", "22. Hukuk Dairesi", "23. Hukuk Dairesi",
    "Hukuk Daireleri Başkanlar Kurulu",
    # Ceza (Criminal) Chambers
    "Ceza Genel Kurulu", 
    "1. Ceza Dairesi", "2. Ceza Dairesi", "3. Ceza Dairesi", "4. Ceza Dairesi",
    "5. Ceza Dairesi", "6. Ceza Dairesi", "7. Ceza Dairesi", "8. Ceza Dairesi",
    "9. Ceza Dairesi", "10. Ceza Dairesi", "11. Ceza Dairesi", "12. Ceza Dairesi",
    "13. Ceza Dairesi", "14. Ceza Dairesi", "15. Ceza Dairesi", "16. Ceza Dairesi",
    "17. Ceza Dairesi", "18. Ceza Dairesi", "19. Ceza Dairesi", "20. Ceza Dairesi",
    "21. Ceza Dairesi", "22. Ceza Dairesi", "23. Ceza Dairesi",
    "Ceza Daireleri Başkanlar Kurulu",
    # General Assembly
    "Büyük Genel Kurulu"
]

class YargitayDetailedSearchRequest(BaseModel):
    """
    Model for the 'data' object sent in the request payload
    to Yargitay's detailed search endpoint (e.g., /aramadetaylist).
    Based on the payload provided by the user.
    """
    arananKelime: Optional[str] = Field("", description="Keyword to search for.")
    # Department/Board selection - Complete Yargıtay chamber hierarchy
    birimYrgKurulDaire: YargitayBirimEnum = Field("", description="""
        Yargıtay chamber/board selection. Options include:
        - Empty string ('') for ALL chambers
        - Civil: 'Hukuk Genel Kurulu', '1. Hukuk Dairesi' through '23. Hukuk Dairesi', 'Hukuk Daireleri Başkanlar Kurulu'
        - Criminal: 'Ceza Genel Kurulu', '1. Ceza Dairesi' through '23. Ceza Dairesi', 'Ceza Daireleri Başkanlar Kurulu'
        - General: 'Büyük Genel Kurulu'
        Total: 49 possible values (including empty string for all chambers)
    """)
    birimYrgHukukDaire: Optional[str] = Field("", description="Legacy field - use birimYrgKurulDaire instead")
    birimYrgCezaDaire: Optional[str] = Field("", description="Legacy field - use birimYrgKurulDaire instead")
    
    esasYil: Optional[str] = Field("", description="Case year for 'Esas No'.")
    esasIlkSiraNo: Optional[str] = Field("", description="Starting sequence number for 'Esas No'.")
    esasSonSiraNo: Optional[str] = Field("", description="Ending sequence number for 'Esas No'.")
    
    kararYil: Optional[str] = Field("", description="Decision year for 'Karar No'.")
    kararIlkSiraNo: Optional[str] = Field("", description="Starting sequence number for 'Karar No'.")
    kararSonSiraNo: Optional[str] = Field("", description="Ending sequence number for 'Karar No'.")
    
    baslangicTarihi: Optional[str] = Field("", description="Start date for decision search (DD.MM.YYYY).")
    bitisTarihi: Optional[str] = Field("", description="End date for decision search (DD.MM.YYYY).")
    
    siralama: Optional[str] = Field("3", description="Sorting criteria (1: Esas No, 2: Karar No, 3: Karar Tarihi).") # Default to 'Karar Tarihine Göre'
    siralamaDirection: Optional[str] = Field("desc", description="Sorting direction ('asc' or 'desc').") # Default to 'Büyükten Küçüğe'
    
    pageSize: int = Field(10, ge=1, le=100, description="Number of results per page.")
    pageNumber: int = Field(1, ge=1, description="Page number to retrieve.")

class YargitayApiDecisionEntry(BaseModel):
    """Model for an individual decision entry from the Yargitay API search response."""
    id: str # Unique system ID of the decision
    daire: Optional[str] = Field(None, description="The chamber that made the decision.")
    esasNo: Optional[str] = Field(None, alias="esasNo", description="Case registry number ('Esas No').")
    kararNo: Optional[str] = Field(None, alias="kararNo", description="Decision number ('Karar No').")
    kararTarihi: Optional[str] = Field(None, alias="kararTarihi", description="Date of the decision.")
    arananKelime: Optional[str] = Field(None, alias="arananKelime", description="Matched keyword in the search result item.")
    # 'index' and 'siraNo' from API response are not critical for MCP tool, so omitted for brevity
    
    # This field will be populated by the client after fetching the search list
    document_url: Optional[HttpUrl] = Field(None, description="Direct URL to the decision document.")

    class Config:
        populate_by_name = True # To allow populating by alias from API response


class YargitayApiResponseInnerData(BaseModel):
    """Model for the inner 'data' object in the Yargitay API search response."""
    data: List[YargitayApiDecisionEntry]
    # draw: Optional[int] = None # Typically used by DataTables, not essential for MCP
    recordsTotal: int # Total number of records matching the query
    recordsFiltered: int # Total number of records after filtering (usually same as recordsTotal)

class YargitayApiSearchResponse(BaseModel):
    """Model for the complete search response from the Yargitay API."""
    data: YargitayApiResponseInnerData
    # metadata: Optional[Dict[str, Any]] = None # Optional metadata from API

class YargitayDocumentMarkdown(BaseModel):
    """Model for a Yargitay decision document, containing only Markdown content."""
    id: str = Field(..., description="The unique ID of the document.")
    markdown_content: Optional[str] = Field(None, description="The decision content converted to Markdown.")
    source_url: HttpUrl = Field(..., description="The source URL of the original document.")

class CompactYargitaySearchResult(BaseModel):
    """A more compact search result model for the MCP tool to return."""
    decisions: List[YargitayApiDecisionEntry]
    total_records: int
    requested_page: int
    page_size: int