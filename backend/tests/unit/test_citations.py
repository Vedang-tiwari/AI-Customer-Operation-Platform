import pytest
from app.ai.generator import validate_citations, generate_grounded_draft


def test_citation_validation_with_real_chunks():
    retrieved = [
        {"chunk_id": "chunk-101", "content": "Refunds within 30 days are permitted.", "similarity": 0.88},
        {"chunk_id": "chunk-102", "content": "Duplicate charges refunded in 2 days.", "similarity": 0.75}
    ]
    body = "According to policy [chunk-101], refunds are permitted."
    citations = validate_citations(body, retrieved)
    assert len(citations) == 1
    assert citations[0]["chunk_id"] == "chunk-101"


def test_hallucinated_citation_rejected():
    retrieved = [
        {"chunk_id": "chunk-101", "content": "Refunds within 30 days are permitted.", "similarity": 0.88}
    ]
    # Body claims chunk-999 which does NOT exist in retrieved documents
    body = "According to policy [chunk-999], everything is free."
    citations = validate_citations(body, retrieved)
    chunk_ids = [c["chunk_id"] for c in citations]
    assert "chunk-999" not in chunk_ids


def test_uncertainty_generation_when_no_knowledge_retrieved():
    body, citations, confidence, model = generate_grounded_draft(
        subject="Obscure question",
        description="Can I pay in Martian cryptocurrency?",
        retrieved_chunks=[]
    )
    assert "specialist" in body.lower() or "escalated" in body.lower()
    assert citations == []
    assert confidence < 0.50
    assert "uncertainty" in model
