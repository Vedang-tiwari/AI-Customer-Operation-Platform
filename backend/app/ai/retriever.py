from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.knowledge import KnowledgeDocument, DocumentChunk
from app.ai.embeddings import generate_embedding, cosine_similarity
from app.core.config import settings
from app.core.logging import logger


def retrieve_relevant_chunks(
    db: Session,
    organization_id: str,
    query: str,
    top_k: int = 4,
    min_similarity_threshold: float = 0.15
) -> List[Dict[str, Any]]:
    """
    Retrieves the most semantically relevant document chunks for a ticket query.
    Enforces strict organization-level scoping to ensure cross-tenant data isolation.
    """
    query_vector = generate_embedding(query, dimension=settings.EMBEDDING_DIMENSION)

    # Fetch all chunks belonging to indexed documents of the specific organization
    stmt = (
        select(DocumentChunk, KnowledgeDocument.title)
        .join(KnowledgeDocument, DocumentChunk.document_id == KnowledgeDocument.id)
        .where(
            KnowledgeDocument.organization_id == organization_id,
            KnowledgeDocument.status == "indexed"
        )
    )
    results = db.execute(stmt).all()

    scored_chunks = []
    for chunk, doc_title in results:
        if not chunk.embedding:
            continue
        sim = cosine_similarity(query_vector, chunk.embedding)
        if sim >= min_similarity_threshold:
            scored_chunks.append({
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "document_title": doc_title,
                "content": chunk.content,
                "similarity": round(float(sim), 4)
            })

    # Sort descending by similarity score
    scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
    return scored_chunks[:top_k]
