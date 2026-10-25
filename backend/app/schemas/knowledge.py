from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
    title: str
    content: str
    file_type: str = "text/plain"
    doc_metadata: Optional[Dict[str, Any]] = None


class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    content: str
    token_count: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class KnowledgeDocumentResponse(BaseModel):
    id: str
    organization_id: str
    title: str
    file_type: str
    version: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    chunks: Optional[List[DocumentChunkResponse]] = None
    model_config = ConfigDict(from_attributes=True)


class SearchQuery(BaseModel):
    query: str
    top_k: int = 5


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    content: str
    similarity: float
