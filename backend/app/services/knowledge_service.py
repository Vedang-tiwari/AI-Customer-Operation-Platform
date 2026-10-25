import re
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.schemas.knowledge import DocumentCreate
from app.ai.embeddings import generate_embedding
from app.services.audit_service import record_audit_event
from app.core.config import settings
from app.core.logging import logger


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """
    Splits text into overlapping semantic passages.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    
    current_chunk = ""
    for p in paragraphs:
        if len(current_chunk) + len(p) <= chunk_size:
            current_chunk = f"{current_chunk}\n\n{p}".strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # If paragraph itself is longer than chunk_size, split by sentences
            if len(p) > chunk_size:
                sentences = re.split(r"(?<=[.!?]) +", p)
                sub_chunk = ""
                for s in sentences:
                    if len(sub_chunk) + len(s) <= chunk_size:
                        sub_chunk = f"{sub_chunk} {s}".strip()
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                        sub_chunk = s
                if sub_chunk:
                    chunks.append(sub_chunk)
                current_chunk = ""
            else:
                current_chunk = p

    if current_chunk:
        chunks.append(current_chunk)

    return chunks if chunks else [text]


def ingest_document(
    db: Session,
    organization_id: str,
    doc_in: DocumentCreate,
    actor_id: Optional[str] = None,
    actor_email: Optional[str] = None
) -> KnowledgeDocument:
    """
    Ingests and indexes a knowledge document into chunks with vector embeddings.
    Strictly scoped to the organization.
    """
    document = KnowledgeDocument(
        organization_id=organization_id,
        title=doc_in.title,
        file_type=doc_in.file_type,
        status="processing",
        doc_metadata=doc_in.doc_metadata or {}
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        raw_chunks = chunk_text(doc_in.content)
        for idx, text_passage in enumerate(raw_chunks):
            embedding = generate_embedding(text_passage, dimension=settings.EMBEDDING_DIMENSION)
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=idx,
                content=text_passage,
                embedding=embedding,
                token_count=len(text_passage.split()),
                chunk_metadata={"source_title": document.title}
            )
            db.add(chunk)

        document.status = "indexed"
        db.commit()
        db.refresh(document)

        record_audit_event(
            db=db,
            organization_id=organization_id,
            action="document.indexed",
            target_type="document",
            target_id=document.id,
            actor_id=actor_id,
            actor_email=actor_email,
            details={"title": document.title, "chunk_count": len(raw_chunks)}
        )

    except Exception as e:
        logger.error(f"Failed to index document: {e}")
        document.status = "failed"
        document.error_message = str(e)
        db.commit()

    return document
