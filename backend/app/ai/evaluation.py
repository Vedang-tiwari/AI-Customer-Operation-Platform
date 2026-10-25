import json
import time
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict

from app.ai.classifier import classify_ticket
from app.ai.embeddings import generate_embedding, cosine_similarity
from app.core.logging import logger


def evaluate_classification(cases_file: str) -> Dict[str, Any]:
    """
    Evaluates classification precision, recall, and macro F1 across labeled test cases.
    """
    path = Path(cases_file)
    if not path.exists():
        raise FileNotFoundError(f"Evaluation cases file not found: {cases_file}")

    total_cases = 0
    correct_category = 0
    correct_priority = 0
    correct_sentiment = 0

    category_tp = defaultdict(int)
    category_fp = defaultdict(int)
    category_fn = defaultdict(int)

    latencies = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            case = json.loads(line)
            total_cases += 1

            start_t = time.perf_counter()
            pred = classify_ticket(case["subject"], case["description"])
            elapsed_ms = (time.perf_counter() - start_t) * 1000
            latencies.append(elapsed_ms)

            expected_cat = case["expected_category"]
            pred_cat = pred.category

            if pred_cat == expected_cat:
                correct_category += 1
                category_tp[expected_cat] += 1
            else:
                category_fp[pred_cat] += 1
                category_fn[expected_cat] += 1

            if pred.priority == case.get("expected_priority"):
                correct_priority += 1
            if pred.sentiment == case.get("expected_sentiment"):
                correct_sentiment += 1

    # Compute Macro F1 across all evaluated categories
    all_categories = set(list(category_tp.keys()) + list(category_fn.keys()) + list(category_fp.keys()))
    f1_scores = []
    category_metrics = {}

    for cat in all_categories:
        tp = category_tp[cat]
        fp = category_fp[cat]
        fn = category_fn[cat]
        prec = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        f1_scores.append(f1)
        category_metrics[cat] = {
            "precision": round(prec, 3),
            "recall": round(rec, 3),
            "f1": round(f1, 3)
        }

    macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    return {
        "total_test_cases": total_cases,
        "category_accuracy": round(correct_category / total_cases, 3) if total_cases else 0.0,
        "priority_accuracy": round(correct_priority / total_cases, 3) if total_cases else 0.0,
        "sentiment_accuracy": round(correct_sentiment / total_cases, 3) if total_cases else 0.0,
        "macro_f1": round(macro_f1, 3),
        "average_latency_ms": round(avg_latency, 2),
        "category_metrics": category_metrics
    }


def evaluate_rag_retrieval(cases_file: str) -> Dict[str, Any]:
    """
    Evaluates semantic retrieval Recall@k against labeled RAG evaluation queries.
    """
    path = Path(cases_file)
    if not path.exists():
        raise FileNotFoundError(f"Evaluation cases file not found: {cases_file}")

    total_queries = 0
    hits_at_k = 0

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            case = json.loads(line)
            total_queries += 1

            query = case["query"]
            expected_keyword = case["expected_keyword"].lower()
            corpus = case["corpus"]

            # Score each chunk in the sample corpus
            q_vec = generate_embedding(query)
            scored = []
            for doc in corpus:
                c_vec = generate_embedding(doc["content"])
                sim = cosine_similarity(q_vec, c_vec)
                scored.append((sim, doc["content"].lower()))

            scored.sort(key=lambda x: x[0], reverse=True)
            top_k_contents = [item[1] for item in scored[:case.get("k", 3)]]

            if any(expected_keyword in content for content in top_k_contents):
                hits_at_k += 1

    recall_at_k = (hits_at_k / total_queries) if total_queries else 0.0
    return {
        "total_queries": total_queries,
        "recall_at_k": round(recall_at_k, 3),
        "hit_rate_percentage": round(recall_at_k * 100, 1)
    }


if __name__ == "__main__":
    import sys
    print("--- Running Evaluation Benchmark ---")
    cls_report = evaluate_classification("evaluation/classification_cases.jsonl")
    print("Classification Metrics:", json.dumps(cls_report, indent=2))
    rag_report = evaluate_rag_retrieval("evaluation/rag_cases.jsonl")
    print("RAG Retrieval Metrics:", json.dumps(rag_report, indent=2))
