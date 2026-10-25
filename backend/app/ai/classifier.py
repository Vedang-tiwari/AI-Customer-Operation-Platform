import json
import re
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.ai.prompts import CLASSIFICATION_SYSTEM_PROMPT


class ClassificationResult(BaseModel):
    category: str = Field(..., pattern="^(billing|technical|security|account|general)$")
    priority: str = Field(..., pattern="^(urgent|high|normal|low)$")
    sentiment: str = Field(..., pattern="^(positive|neutral|negative|frustrated)$")
    intent: str
    needs_human_review: bool = True
    confidence: float = 0.85
    model_version: str = "deterministic-v1"


def rule_based_classify(subject: str, description: str) -> ClassificationResult:
    """
    Deterministic rule-based classification fallback ensuring zero-dependency,
    instant, and consistent classification.
    """
    text = f"{subject} {description}".lower()

    # Determine Category
    if any(k in text for k in ["breach", "vulnerability", "hack", "exploit", "compromised", "unauthorized access", "2fa bypass"]):
        category = "security"
        priority = "urgent"
        intent = "security_incident"
    elif any(k in text for k in ["charge", "refund", "invoice", "payment", "billing", "receipt", "subscription", "pricing", "tax", "credit card"]):
        category = "billing"
        priority = "high" if "double" in text or "charged twice" in text or "incorrect" in text else "normal"
        intent = "duplicate_charge" if ("double" in text or "charged twice" in text) else "refund_request" if "refund" in text else "billing_inquiry"
    elif any(k in text for k in ["bug", "error", "crash", "timeout", "api", "latency", "exception", "failed to connect", "integration", "code 500"]):
        category = "technical"
        priority = "high" if ("production" in text or "outage" in text or "down" in text) else "normal"
        intent = "api_error" if "api" in text else "system_issue"
    elif any(k in text for k in ["password", "reset", "login", "profile", "account", "email address", "delete account", "sso"]):
        category = "account"
        priority = "normal"
        intent = "login_issue" if "login" in text or "password" in text else "account_management"
    else:
        category = "general"
        priority = "normal"
        intent = "general_inquiry"

    # Determine Priority overrides
    if any(k in text for k in ["urgent", "asap", "immediately", "critical", "emergency", "production down", "sev 1"]):
        priority = "urgent"

    # Determine Sentiment
    if any(k in text for k in ["furious", "unacceptable", "terrible", "worst", "ridiculous", "frustrated", "disappointed", "angry", "screwed", "money back now"]):
        sentiment = "frustrated"
    elif any(k in text for k in ["not working", "problem", "issue", "cannot", "failed", "error", "broken", "bad"]):
        sentiment = "negative"
    elif any(k in text for k in ["thank you", "great", "appreciate", "helpful", "good", "awesome", "solved"]):
        sentiment = "positive"
    else:
        sentiment = "neutral"

    return ClassificationResult(
        category=category,
        priority=priority,
        sentiment=sentiment,
        intent=intent,
        needs_human_review=True,
        confidence=0.92,
        model_version="heuristic-rule-engine-v1"
    )


async def classify_ticket_async(subject: str, description: str) -> ClassificationResult:
    """
    Classifies ticket using configured LLM provider (or fallback rule engine).
    """
    if settings.LLM_PROVIDER == "mock" or not (settings.LLM_API_KEY or settings.GEMINI_API_KEY):
        return rule_based_classify(subject, description)

    # If Gemini API key is provided
    if settings.GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            prompt = f"{CLASSIFICATION_SYSTEM_PROMPT}\n\nSubject: {subject}\nDescription: {description}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"response_mime_type": "application/json"}
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(raw_text)
                    return ClassificationResult(
                        category=parsed.get("category", "general"),
                        priority=parsed.get("priority", "normal"),
                        sentiment=parsed.get("sentiment", "neutral"),
                        intent=parsed.get("intent", "general_inquiry"),
                        needs_human_review=parsed.get("needs_human_review", True),
                        confidence=0.95,
                        model_version="gemini-1.5-flash"
                    )
        except Exception as e:
            logger.warning(f"Gemini classification failed, falling back to rule engine: {e}")

    # Fallback to deterministic rule engine
    return rule_based_classify(subject, description)


def classify_ticket(subject: str, description: str) -> ClassificationResult:
    """Synchronous classification entrypoint."""
    return rule_based_classify(subject, description)
