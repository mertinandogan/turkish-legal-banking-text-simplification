# bedesten_mcp_module/models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal, Union

# Import YargitayBirimEnum for chamber filtering
from yargitay_mcp_module.models import YargitayBirimEnum

# Danıştay Chamber/Board Options
DanistayBirimEnum = Literal[
    "",  # Empty string for "All" chambers
    # Main Councils
    "Büyük Gen.Kur.",  # Grand General Assembly
    "İdare Dava Daireleri Kurulu",  # Administrative Cases Chambers Council
    "Vergi Dava Daireleri Kurulu",  # Tax Cases Chambers Council
    "İçtihatları Birleştirme Kurulu",  # Precedents Unification Council
    "İdari İşler Kurulu",  # Administrative Affairs Council
    "Başkanlar Kurulu",  # Presidents Council
    # Chambers
    "1. Daire", "2. Daire", "3. Daire", "4. Daire", "5. Daire",
    "6. Daire", "7. Daire", "8. Daire", "9. Daire", "10. Daire",
    "11. Daire", "12. Daire", "13. Daire", "14. Daire", "15. Daire",
    "16. Daire", "17. Daire",
    # Military High Administrative Court
    "Askeri Yüksek İdare Mahkemesi",
    "Askeri Yüksek İdare Mahkemesi Daireler Kurulu",
    "Askeri Yüksek İdare Mahkemesi Başsavcılığı",
    "Askeri Yüksek İdare Mahkemesi 1. Daire",
    "Askeri Yüksek İdare Mahkemesi 2. Daire", 
    "Askeri Yüksek İdare Mahkemesi 3. Daire"
]

# Search Request Models
class BedestenSearchData(BaseModel):
    pageSize: int
    pageNumber: int  
    itemTypeList: List[str]
    phrase: str
    birimAdi: Optional[Union[YargitayBirimEnum, DanistayBirimEnum]] = Field(None, description="""
        Chamber/Board filter (optional). Available options depend on itemTypeList:
        
        For YARGITAYKARARI (52 options):
        - None/null for ALL chambers
        - 'Hukuk Genel Kurulu', '1. Hukuk Dairesi' through '23. Hukuk Dairesi'
        - 'Ceza Genel Kurulu', '1. Ceza Dairesi' through '23. Ceza Dairesi'  
        - 'Hukuk Daireleri Başkanlar Kurulu', 'Ceza Daireleri Başkanlar Kurulu'
        - 'Büyük Genel Kurulu'
        
        For DANISTAYKARAR (27 options):
        - None/null for ALL chambers
        - 'Büyük Gen.Kur.', 'İdare Dava Daireleri Kurulu', 'Vergi Dava Daireleri Kurulu'
        - '1. Daire' through '17. Daire'
        - 'İçtihatları Birleştirme Kurulu', 'İdari İşler Kurulu', 'Başkanlar Kurulu'
        - Military courts: 'Askeri Yüksek İdare Mahkemesi' variants
    """)
    sortFields: List[str] = ["KARAR_TARIHI"]
    sortDirection: str = "desc"

class BedestenSearchRequest(BaseModel):
    data: BedestenSearchData
    applicationName: str = "UyapMevzuat"
    paging: bool = True

# Search Response Models
class BedestenItemType(BaseModel):
    name: str
    description: str

class BedestenDecisionEntry(BaseModel):
    documentId: str
    itemType: BedestenItemType
    birimId: Optional[str] = None
    birimAdi: Optional[str]
    esasNoYil: int
    esasNoSira: int
    kararNoYil: int
    kararNoSira: int
    kararTuru: Optional[str] = None
    kararTarihi: str
    kararTarihiStr: str
    kesinlesmeDurumu: Optional[str] = None
    kararNo: str
    esasNo: str

class BedestenSearchDataResponse(BaseModel):
    emsalKararList: List[BedestenDecisionEntry]
    total: int
    start: int

class BedestenSearchResponse(BaseModel):
    data: BedestenSearchDataResponse
    metadata: Dict[str, Any]

# Document Request/Response Models
class BedestenDocumentRequestData(BaseModel):
    documentId: str

class BedestenDocumentRequest(BaseModel):
    data: BedestenDocumentRequestData
    applicationName: str = "UyapMevzuat"

class BedestenDocumentData(BaseModel):
    content: str  # Base64 encoded HTML or PDF
    mimeType: str
    version: int

class BedestenDocumentResponse(BaseModel):
    data: BedestenDocumentData
    metadata: Dict[str, Any]

class BedestenDocumentMarkdown(BaseModel):
    documentId: str = Field(..., description="The document ID from Bedesten")
    markdown_content: Optional[str] = Field(None, description="The decision content converted to Markdown")
    source_url: str = Field(..., description="The source URL of the document")
    mime_type: Optional[str] = Field(None, description="Original content type (text/html or application/pdf)")