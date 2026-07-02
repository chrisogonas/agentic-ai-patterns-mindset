from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

from openai import OpenAI


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class Category(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    REFUND = "refund"
    GENERAL = "general"
    ESCALATE = "escalate"


class DifficultyLevel(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


@dataclass
class RoutingDecision:
    category: Category
    confidence: float
    reasoning: str


HANDLER_PROMPTS = {
    Category.BILLING: """You are a billing specialist. You have access to the customer's account details. Be precise about amounts and dates. If you need to make changes, confirm with the customer first.""",
    Category.TECHNICAL: """You are a technical support engineer. Walk through troubleshooting steps methodically. Ask clarifying questions about the customer's setup. Never guess at solutions — if you're unsure, escalate.""",
    Category.REFUND: """You are a customer retention specialist handling refund requests. Be empathetic. Follow the refund policy strictly: full refund within 30 days, prorated after. Always confirm the refund amount before processing.""",
    Category.GENERAL: """You are a helpful product specialist. Answer questions about features, pricing, and availability. Be friendly and informative.""",
}


MODEL_MAP = {
    DifficultyLevel.SIMPLE: "gpt-4o-mini",
    DifficultyLevel.MODERATE: "gpt-4o",
    DifficultyLevel.COMPLEX: "o1",
}


def classify_request(message: str) -> Category:
    """Route step: classify the customer message into a specialist category."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """Classify the customer message into exactly one category:
- billing: payment issues, invoice questions, subscription changes
- technical: bugs, errors, how-to questions, feature usage
- refund: refund requests, cancellation with refund
- general: product info, feature requests, feedback
- escalate: threats, legal mentions, repeated complaints, urgent safety

Respond with ONLY the category name, nothing else.""",
            },
            {"role": "user", "content": message},
        ],
        temperature=0,
    )

    category_str = response.choices[0].message.content.strip().lower()
    try:
        return Category(category_str)
    except ValueError:
        return Category.GENERAL


def handle_request(message: str, category: Category) -> str:
    """Route to the appropriate handler based on the category."""
    if category == Category.ESCALATE:
        return "[ESCALATED] This message has been flagged for human review."

    system_prompt = HANDLER_PROMPTS[category]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content


def customer_service_router(message: str) -> dict[str, Any]:
    """Run the full content-based routing pipeline."""
    category = classify_request(message)
    response = handle_request(message, category)
    return {"category": category.value, "response": response}


def classify_with_confidence(message: str) -> RoutingDecision:
    """Classify with a confidence score and a short explanation."""
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Classify the customer message. Be precise."},
            {"role": "user", "content": message},
        ],
        response_format=RoutingDecision,
        temperature=0,
    )
    return response.choices[0].message.parsed


def confident_router(message: str) -> dict[str, Any]:
    """Route with a confidence threshold so low-confidence requests fall back safely."""
    decision = classify_with_confidence(message)
    if decision.confidence < 0.7:
        return {"category": Category.GENERAL.value, "response": handle_request(message, Category.GENERAL)}
    return {"category": decision.category.value, "response": handle_request(message, decision.category)}


def assess_difficulty(query: str) -> DifficultyLevel:
    """Classify the query difficulty to select the right model."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """Assess the difficulty of answering this query:
- simple: factual recall, definitions, straightforward questions
- moderate: requires analysis, comparison, or multi-step reasoning
- complex: requires deep reasoning, nuanced judgment, or creative problem-solving

Respond with ONLY the difficulty level.""",
            },
            {"role": "user", "content": query},
        ],
        temperature=0,
    )
    level = response.choices[0].message.content.strip().lower()
    try:
        return DifficultyLevel(level)
    except ValueError:
        return DifficultyLevel.MODERATE


def model_routed_response(query: str) -> str:
    """Route the response generation to a model tier based on the query difficulty."""
    difficulty = assess_difficulty(query)
    model = MODEL_MAP[difficulty]
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": query}],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    sample_message = "I was charged twice this month and need help with my subscription."
    print(customer_service_router(sample_message))
