"""
FastAPI integration for Yargı MCP Server

This module demonstrates how to integrate the Yargı MCP server
with a FastAPI application, providing additional REST API endpoints
alongside the MCP functionality.

Usage:
    uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import the main MCP app
from mcp_server_main import app as mcp_server
from asgi_app import custom_middleware

# Create MCP ASGI app
mcp_asgi_app = mcp_server.http_app(path="/mcp")

# Create FastAPI app with MCP lifespan
app = FastAPI(
    title="Yargı MCP API",
    description="Turkish Legal Database MCP Server with REST API",
    version="0.1.0",
    lifespan=mcp_asgi_app.lifespan
)

# Add CORS middleware
cors_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount MCP server
app.mount("/mcp-server", mcp_asgi_app)

# Response models
class ToolInfo(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

class ServerInfo(BaseModel):
    name: str
    version: str
    description: str
    tools_count: int
    databases: List[str]
    mcp_endpoint: str
    api_docs: str

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    uptime_seconds: Optional[float] = None
    tools_operational: bool

# Track server start time
SERVER_START_TIME = datetime.now()

@app.get("/", response_model=ServerInfo)
async def root():
    """Get server information"""
    return ServerInfo(
        name="Yargı MCP Server",
        version="0.1.0",
        description="MCP server for Turkish legal databases",
        tools_count=len(mcp_server._tool_manager.tools),
        databases=[
            "Yargıtay (Court of Cassation)",
            "Danıştay (Council of State)",
            "Emsal (Precedent)",
            "Uyuşmazlık Mahkemesi (Court of Jurisdictional Disputes)",
            "Anayasa Mahkemesi (Constitutional Court)",
            "Kamu İhale Kurulu (Public Procurement Authority)",
            "Rekabet Kurumu (Competition Authority)",
            "Bedesten API (Multiple courts)"
        ],
        mcp_endpoint="/mcp-server/mcp/",
        api_docs="/docs"
    )

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    uptime = (datetime.now() - SERVER_START_TIME).total_seconds()
    
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now(),
        uptime_seconds=uptime,
        tools_operational=len(mcp_server._tool_manager.tools) > 0
    )

@app.get("/api/tools", response_model=List[ToolInfo])
async def list_tools(
    search: Optional[str] = Query(None, description="Search tools by name or description"),
    database: Optional[str] = Query(None, description="Filter by database name")
):
    """List all available MCP tools"""
    tools = []
    
    for tool in mcp_server._tool_manager.tools.values():
        # Apply filters if provided
        if search and search.lower() not in tool.name.lower() and search.lower() not in tool.description.lower():
            continue
            
        if database:
            db_lower = database.lower()
            if db_lower not in tool.name.lower() and db_lower not in tool.description.lower():
                continue
        
        # Extract parameter schema
        params = {}
        if hasattr(tool, 'schema') and tool.schema:
            if hasattr(tool.schema, 'parameters'):
                params = tool.schema.parameters
            elif hasattr(tool.schema, '__annotations__'):
                params = {k: str(v) for k, v in tool.schema.__annotations__.items()}
        
        tools.append(ToolInfo(
            name=tool.name,
            description=tool.description,
            parameters=params
        ))
    
    return tools

@app.get("/api/tools/{tool_name}", response_model=ToolInfo)
async def get_tool(tool_name: str):
    """Get detailed information about a specific tool"""
    tool = mcp_server._tool_manager.tools.get(tool_name)
    
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    # Extract parameter schema
    params = {}
    if hasattr(tool, 'schema') and tool.schema:
        if hasattr(tool.schema, 'parameters'):
            params = tool.schema.parameters
        elif hasattr(tool.schema, '__annotations__'):
            params = {k: str(v) for k, v in tool.schema.__annotations__.items()}
    
    return ToolInfo(
        name=tool.name,
        description=tool.description,
        parameters=params
    )

@app.get("/api/databases")
async def list_databases():
    """List all supported legal databases"""
    databases = {
        "yargitay": {
            "name": "Yargıtay (Court of Cassation)",
            "description": "Supreme court for civil and criminal cases",
            "tools": ["search_yargitay_detailed", "get_yargitay_document_markdown", 
                     "search_yargitay_bedesten", "get_yargitay_bedesten_document_markdown"],
            "chambers": 52
        },
        "danistay": {
            "name": "Danıştay (Council of State)",
            "description": "Supreme administrative court",
            "tools": ["search_danistay_by_keyword", "search_danistay_detailed", 
                     "get_danistay_document_markdown", "search_danistay_bedesten", 
                     "get_danistay_bedesten_document_markdown"],
            "chambers": 27
        },
        "emsal": {
            "name": "Emsal (Precedent)",
            "description": "Precedent decisions from various courts",
            "tools": ["search_emsal_detailed_decisions", "get_emsal_document_markdown"]
        },
        "uyusmazlik": {
            "name": "Uyuşmazlık Mahkemesi",
            "description": "Court of Jurisdictional Disputes",
            "tools": ["search_uyusmazlik_decisions", "get_uyusmazlik_document_markdown_from_url"]
        },
        "anayasa": {
            "name": "Anayasa Mahkemesi (Constitutional Court)",
            "description": "Constitutional review and individual applications",
            "tools": ["search_anayasa_norm_denetimi_decisions", 
                     "get_anayasa_norm_denetimi_document_markdown",
                     "search_anayasa_bireysel_basvuru_report", 
                     "get_anayasa_bireysel_basvuru_document_markdown"]
        },
        "kik": {
            "name": "Kamu İhale Kurulu",
            "description": "Public Procurement Authority",
            "tools": ["search_kik_decisions", "get_kik_document_markdown"]
        },
        "rekabet": {
            "name": "Rekabet Kurumu",
            "description": "Competition Authority",
            "tools": ["search_rekabet_kurumu_decisions", "get_rekabet_kurumu_document"]
        },
        "bedesten": {
            "name": "Bedesten API",
            "description": "Unified API for multiple courts",
            "tools": ["search_yerel_hukuk_bedesten", "get_yerel_hukuk_bedesten_document_markdown",
                     "search_istinaf_hukuk_bedesten", "get_istinaf_hukuk_bedesten_document_markdown",
                     "search_kyb_bedesten", "get_kyb_bedesten_document_markdown"]
        }
    }
    
    return JSONResponse(content=databases)

@app.get("/api/stats")
async def get_statistics():
    """Get server statistics"""
    uptime = (datetime.now() - SERVER_START_TIME).total_seconds()
    
    # Count tools by database
    tool_counts = {}
    for tool in mcp_server._tool_manager.tools.values():
        for db in ["yargitay", "danistay", "emsal", "uyusmazlik", "anayasa", "kik", "rekabet", "bedesten"]:
            if db in tool.name.lower():
                tool_counts[db] = tool_counts.get(db, 0) + 1
                break
    
    return JSONResponse({
        "server": {
            "uptime_seconds": uptime,
            "start_time": SERVER_START_TIME.isoformat(),
            "version": "0.1.0"
        },
        "tools": {
            "total": len(mcp_server._tool_manager.tools),
            "by_database": tool_counts
        },
        "capabilities": {
            "total_chambers": 79,  # 52 Yargıtay + 27 Danıştay
            "date_filtering": True,
            "exact_phrase_search": True,
            "dual_api_support": True
        }
    })

# Add a simple authentication example (optional)
# Uncomment to enable basic token authentication
"""
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    expected_token = os.getenv("API_TOKEN")
    
    if expected_token and token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    return token

# Then add Depends(verify_token) to any endpoint that needs protection
# Example: async def list_tools(..., token: str = Depends(verify_token)):
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)