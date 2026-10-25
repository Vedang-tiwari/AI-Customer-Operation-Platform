from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.knowledge import KnowledgeDocument
from app.models.organization import Organization
from app.models.user import User
from app.schemas.knowledge import (
    DocumentCreate,
    KnowledgeDocumentResponse,
    SearchQuery,
    SearchResult
)
from app.services.knowledge_service import ingest_document
from app.ai.retriever import retrieve_relevant_chunks
from app.api.dependencies import get_current_user, get_current_organization, require_roles

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base & RAG"])


@router.post("/documents", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_document(
    doc_in: DocumentCreate,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Upload and ingest a knowledge document (chunking & vector embedding)."""
    doc = ingest_document(
        db=db,
        organization_id=org.id,
        doc_in=doc_in,
        actor_id=current_user.id,
        actor_email=current_user.email
    )
    return doc


@router.get("/documents", response_model=List[KnowledgeDocumentResponse])
def list_knowledge_documents(
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """List knowledge documents in the caller's organization."""
    docs = db.scalars(
        select(KnowledgeDocument).where(KnowledgeDocument.organization_id == org.id).order_by(KnowledgeDocument.created_at.desc())
    ).all()
    return docs


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentResponse)
def get_knowledge_document(
    document_id: str,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Retrieve document details and processing status."""
    doc = db.scalar(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.organization_id == org.id
        )
    )
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.post("/search", response_model=List[SearchResult])
def search_knowledge(
    search_in: SearchQuery,
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Test semantic vector retrieval for a query within the tenant organization."""
    chunks = retrieve_relevant_chunks(
        db=db,
        organization_id=org.id,
        query=search_in.query,
        top_k=search_in.top_k,
        min_similarity_threshold=0.05
    )
    return chunks
