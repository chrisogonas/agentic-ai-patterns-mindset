# Chapter 5: Routing

Your customer service AI receives thousands of messages daily. Some are billing inquiries. Some are technical troubleshooting. Some are angry rants that need a human. Some are simple FAQs. If you throw every message at the same model with the same prompt, you'll overspend on trivial questions, underperform on complex ones, and miss the escalation signals on urgent ones.

Routing fixes this. You add a classification step at the front that examines each input and directs it to the right handler — the one with the right prompt, the right tools, the right model, or the right human. It's the receptionist pattern: a fast, cheap triage decision that ensures every request reaches the specialist best equipped to handle it.

## How It Works

The architecture is a classifier followed by branching paths:

```
                     ┌─→ [Handler A] → Response
                     │
Input → [Classifier] ├─→ [Handler B] → Response
                     │
                     ├─→ [Handler C] → Response
                     │
                     └─→ [Fallback]  → Response
```

The classifier examines the input and assigns it to a category. Each category maps to a specialized downstream handler. The handlers may differ in their system prompts, their available tools, their model choice, or even their processing pipeline (one category might trigger a prompt chain, another a single call).

This differs from prompt chaining in a fundamental way: **prompt chaining is sequential, routing is conditional.** With chaining, every input follows the same path. With routing, different inputs take different paths. The LLM's decision at the routing step determines which downstream logic executes.

There are two complementary routing strategies:

**Content-based routing** directs inputs based on *what they're about*. A legal assistant might route contract questions to a handler with access to the contract database, while routing regulatory questions to a handler loaded with compliance documents. The classifier looks at semantics.

**Model-based routing** directs inputs based on *how hard they are*. Simple factual questions go to a small, fast, cheap model. Complex reasoning tasks go to a large, slow, capable model. The classifier looks at complexity. This is primarily a cost optimization strategy — many production systems find that 60-80% of their queries can be handled by a model that costs 10-20x less than their most capable one.

## Implementation in Python

Let's build a customer service router. The classifier uses structured output to make a reliable routing decision:

```python
import json
from openai import OpenAI
from enum import Enum

client = OpenAI()


class Category(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    REFUND = "refund"
    GENERAL = "general"
    ESCALATE = "escalate"


def classify_request(message: str) -> Category:
    """Route step: classify the customer message."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Fast, cheap model for classification
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
        return Category.GENERAL  # Fallback for unexpected output
```

Notice the model choice: `gpt-4o-mini` for classification. This is deliberate. Classification is a straightforward task that doesn't need a frontier model. Using a smaller model here reduces cost and latency while maintaining accuracy. The expensive model should be reserved for the handlers that need it.

Now the specialized handlers:

```python
HANDLER_PROMPTS = {
    Category.BILLING: """You are a billing specialist. You have access to 
the customer's account details. Be precise about amounts and dates. 
If you need to make changes, confirm with the customer first.""",
    
    Category.TECHNICAL: """You are a technical support engineer. 
Walk through troubleshooting steps methodically. Ask clarifying 
questions about the customer's setup. Never guess at solutions — 
if you're unsure, escalate.""",
    
    Category.REFUND: """You are a customer retention specialist handling 
refund requests. Be empathetic. Follow the refund policy strictly: 
full refund within 30 days, prorated after. Always confirm the 
refund amount before processing.""",
    
    Category.GENERAL: """You are a helpful product specialist. Answer 
questions about features, pricing, and availability. Be friendly 
and informative.""",
}


def handle_request(message: str, category: Category) -> str:
    """Route to the appropriate handler based on category."""
    if category == Category.ESCALATE:
        return "[ESCALATED] This message has been flagged for human review."
    
    system_prompt = HANDLER_PROMPTS[category]
    
    response = client.chat.completions.create(
        model="gpt-4o",  # Capable model for the actual response
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content


def customer_service_router(message: str) -> dict:
    """Full routing pipeline."""
    category = classify_request(message)
    response = handle_request(message, category)
    
    return {
        "category": category.value,
        "response": response,
    }
```

The `ESCALATE` category doesn't use an LLM handler at all — it returns a fixed response and queues for human review. This is routing's hidden strength: one of the "handlers" can be a deterministic code path that doesn't involve an LLM. You can route to a database lookup, a static response, an API call, or a human queue.

## Structured Output for Reliable Routing

The weak link in any routing system is the classification step. If the classifier returns garbage, every downstream handler receives misrouted input. Structured output makes classification reliable.

OpenAI and Anthropic both support structured output schemas. Here's a more robust classifier using OpenAI's structured output:

```python
from pydantic import BaseModel, Field


class RoutingDecision(BaseModel):
    category: Category = Field(
        description="The category that best matches the customer message"
    )
    confidence: float = Field(
        ge=0, le=1,
        description="Confidence in the classification (0.0 to 1.0)"
    )
    reasoning: str = Field(
        description="Brief explanation of why this category was chosen"
    )


def classify_with_confidence(message: str) -> RoutingDecision:
    """Classify with structured output and confidence score."""
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Classify the customer message. Be precise.",
            },
            {"role": "user", "content": message},
        ],
        response_format=RoutingDecision,
        temperature=0,
    )
    return response.choices[0].message.parsed
```

The confidence score unlocks a second routing strategy: **confidence-based escalation**. If the classifier isn't sure, route to a fallback.

```python
def confident_router(message: str) -> dict:
    """Route with confidence threshold."""
    decision = classify_with_confidence(message)
    
    if decision.confidence < 0.7:
        # Low confidence: route to general handler or human
        return handle_request(message, Category.GENERAL)
    
    return handle_request(message, decision.category)
```

This is a practical application of Chapter 2's trust calibration principle. When the system's confidence is low, it reduces autonomy — defaulting to a generalist handler rather than risking a misrouted specialist response.

## Model Routing for Cost Optimization

Model routing is content-based routing's pragmatic sibling. Instead of routing by topic, you route by difficulty.

```python
class DifficultyLevel(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


MODEL_MAP = {
    DifficultyLevel.SIMPLE: "gpt-4o-mini",      # $0.15 / 1M tokens
    DifficultyLevel.MODERATE: "gpt-4o",           # $2.50 / 1M tokens
    DifficultyLevel.COMPLEX: "o1",                # $15.00 / 1M tokens
}


def assess_difficulty(query: str) -> DifficultyLevel:
    """Classify query difficulty to select the appropriate model."""
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
        return DifficultyLevel.MODERATE  # Default to middle tier


def model_routed_response(query: str) -> str:
    """Route to appropriate model based on query difficulty."""
    difficulty = assess_difficulty(query)
    model = MODEL_MAP[difficulty]
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": query}],
    )
    return response.choices[0].message.content
```

The economics are compelling. If 70% of queries are simple, model routing reduces average cost per query by 60-80% compared to sending everything to the most capable model. The classification step itself (using GPT-4o-mini) costs fractions of a cent per call — trivial compared to the savings on the response calls.

The risk is misclassification in the dangerous direction: routing a complex query to a simple model, producing a confidently wrong answer that the user trusts. The safe default is always the more capable model. When in doubt, route up.

## Case Study: Customer Service Triage

A mid-size SaaS company receives ~2,000 support messages daily. Before routing:

- All messages go to GPT-4o with a generic support prompt
- Average response quality: acceptable but inconsistent
- Monthly API cost: ~$4,200
- Escalation to humans: 25% (many unnecessary)

After implementing routing:

- **Classifier** (GPT-4o-mini): categorizes each message into billing, technical, refund, general, or escalate
- **Billing handler** (GPT-4o): has access to account data tools, uses a precise, policy-aware prompt
- **Technical handler** (GPT-4o): has access to docs and error lookup tools, follows a diagnostic flowchart
- **Refund handler** (GPT-4o-mini): follows a strict decision tree, mostly deterministic
- **General handler** (GPT-4o-mini): answers FAQs from a knowledge base
- **Escalate**: flags for human review with context summary

Results after routing:

- Monthly API cost: ~$1,800 (57% reduction)
- Resolution quality: improved across all categories (specialized handlers outperform generalists)
- Escalation to humans: 12% (more accurate — fewer false escalations, fewer missed urgent cases)
- Average latency: +200ms (classifier overhead), offset by faster simple-path handling

The counterintuitive finding: **spending more on some categories while spending less on others improved both cost and quality.** The billing handler got a better model and richer prompt than before. The general FAQ handler got a cheaper model and still performed better because its prompt was laser-focused.

## Framework Spotlight: LangGraph Conditional Edges

LangGraph represents routing as conditional edges in a graph:

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict


class ServiceState(TypedDict):
    message: str
    category: str
    response: str


def classify_node(state: ServiceState) -> ServiceState:
    category = classify_request(state["message"])
    return {"category": category.value}


def billing_node(state: ServiceState) -> ServiceState:
    response = handle_request(state["message"], Category.BILLING)
    return {"response": response}


def technical_node(state: ServiceState) -> ServiceState:
    response = handle_request(state["message"], Category.TECHNICAL)
    return {"response": response}


def route_by_category(state: ServiceState) -> str:
    """Conditional edge: return the node name to route to."""
    return state["category"]


# Build the graph
graph = StateGraph(ServiceState)

graph.add_node("classify", classify_node)
graph.add_node("billing", billing_node)
graph.add_node("technical", technical_node)
# ... add other handler nodes

graph.set_entry_point("classify")
graph.add_conditional_edges(
    "classify",
    route_by_category,
    {
        "billing": "billing",
        "technical": "technical",
        # ... other routes
    },
)
graph.add_edge("billing", END)
graph.add_edge("technical", END)

app = graph.compile()
```

The graph representation makes routing logic explicit and visual. LangGraph compiles the graph into a runnable that handles state management automatically. For simple routing (3-5 categories), this is more infrastructure than you need. For complex routing with nested sub-graphs — where the technical handler itself branches into sub-specialties — the declarative graph starts paying for itself.

## Token Cost Profile

> **Cost structure:** 1 classification call + 1 handler call. The classification step is cheap (~200–500 tokens); the handler call varies by route.
>
> **Typical range:** Classification adds ~$0.00003–$0.0001 per request (using `gpt-4o-mini`). Total cost depends on the handler model — a simple-route handler on `gpt-4o-mini` costs ~10–20× less than a complex-route handler on `o1`.
>
> **Cost multiplier vs. single call:** Often *negative* — routing *reduces* average cost by steering easy queries to cheaper models. A system routing 70% of queries to `gpt-4o-mini` and 30% to `gpt-4o` saves 60–80% compared to sending everything to `gpt-4o`.
>
> **Worked example:** Assume 10,000 queries/day averaging 1,000 input + 500 output tokens each. Sending all to `gpt-4o` ($2.50/$10.00 per 1M tokens): ~$37.50/day. With routing (70% to `gpt-4o-mini` at $0.15/$0.60 per 1M tokens, 30% to `gpt-4o`): 7,000 × $0.00045 + 3,000 × $3.75/1000 ≈ $3.15 + $11.25 = **$14.40/day** — a 62% reduction. The classification step itself adds ~$0.30/day. Over a month, that’s ~$700 saved.
>
> **Where cost grows:** Category explosion (more categories = more handler maintenance) and misclassification (wrong route may trigger retries or escalation, doubling cost for that query).

## Tradeoffs and Failure Modes

**Misclassification cascades.** A wrong classification sends the input to a handler that lacks the right context, tools, or prompt. The handler doesn't know it received a misrouted input — it does its best with what it has, which is often confidently wrong. Mitigation: add monitoring for category distribution shifts, sample misclassifications regularly, and test with adversarial inputs at category boundaries.

**Category explosion.** Starting with 5 categories is clean. Growing to 25 is messy. More categories means more handlers to maintain, more classification boundaries to get wrong, and more routing logic to debug. Keep categories coarse. Use sub-routing within handlers if you need finer granularity.

**Router latency.** Every request pays the classification tax, even the ones that would have been handled fine by a generalist. If classification adds 300ms to every request and only 30% of requests benefit from specialized handling, you're adding latency for the majority. Measure whether routing actually improves outcomes for your specific traffic.

**Edge cases that span categories.** "I was billed incorrectly, and when I tried to fix it in your app, I got an error." Is this billing or technical? The classifier has to pick one. Strategies: design categories with explicit overlap rules, allow multi-label classification and route to the handler that covers the most critical aspect, or use a "complex" catch-all for multi-category inputs.

### Observability Checklist

> **What to log:** Classification decision (category + confidence), selected handler, handler latency, handler output quality (if measurable), router model and version.
>
> **Key metrics:** Category distribution (track shifts over time), classification confidence histogram, per-category handler success rate, misclassification rate (sampled via human review), cost-per-query by route.
>
> **Alerts to set:** Category distribution drifting >10% from baseline (input shift), classification confidence dropping below threshold for >5% of requests, any handler error rate exceeding 3%.
>
> **Debugging tip:** Log the classification confidence alongside the decision. Low-confidence classifications are your highest misclassification risk — sample and review them regularly. Build a confusion matrix from human-labeled samples weekly.

## When NOT to Use Routing

- **Homogeneous inputs.** If all your inputs are the same type (e.g., all translation requests, all code reviews), there's nothing to route. A single well-crafted handler does the job.

- **Small-scale systems.** If you handle 50 queries a day, the cost savings from model routing are negligible, and the engineering overhead of maintaining specialized handlers isn't worth it.

- **When classification accuracy is poor.** If your classifier achieves less than 85% accuracy on your actual traffic, routing may do more harm than good. Misrouted requests get worse handling than a generalist would provide. Fix classification first.

- **When a single capable model handles everything well.** If GPT-4o with a good prompt already produces high-quality responses across all your input types, adding routing is optimization without a problem. Measure first, route second.

Routing is the pattern you reach for when you need different inputs to receive different treatment — different prompts, different tools, different models, different levels of human oversight. It's the gateway pattern: your system's front door. Get it right, and every downstream handler performs better. Get it wrong, and you've added complexity that actively degrades quality.

## Review Questions

**Knowledge & Design Questions:**

1. Explain the difference between content-based routing and model-based routing. For each approach, give a concrete example where it makes sense. Why is model-based routing primarily a cost optimization strategy? What are the risks of routing primarily for cost?

2. You design a router for a product support system. You've defined five categories: billing, technical, refund, general, escalate. Your testing shows the classifier makes the right decision 95% of the time. Design a fallback strategy for the 5% of mis-routed messages. What happens if a billing inquiry gets sent to the technical handler? How should the system recover?

3. The chapter emphasizes structured output (JSON schemas with strict parsing) for reliable routing. Why is structured output critical for routing specifically? What failures occur if the classifier generates unstructured text instead? How would you test this robustness?

4. Compare routing to prompt chaining: prompt chaining is sequential (same path for all inputs), routing is conditional (different paths based on classification). Design a system that uses both patterns — where would you route first, then chain? Where might chaining-then-routing make sense?

**Implementation Questions:**

5. Build a two-tier router: a cheap model (e.g., gpt-4o-mini) classifies the request, and based on the classification, either (A) responds directly if it's low-complexity, or (B) escalates to a more capable model (e.g., gpt-4o) for complex tasks. Write working Python code that implements this cost-optimization strategy. Include metrics tracking for classification accuracy and cost per request.

6. You have a routing system that sometimes mis-routes. Implement a feedback mechanism where users can report mis-routing, and use that data to improve the classifier over time. Write pseudocode or working Python that: (1) captures a mis-routing event, (2) stores it with the original input and correct category, (3) uses accumulated mis-routings to fine-tune or audit the classifier. What format would you use to store these examples?

## Sources

- Anthropic. "Building Effective Agents." *Anthropic Engineering Blog*, December 2024. https://www.anthropic.com/engineering/building-effective-agents. Accessed April 2025.
- Andrew Ng. "Agentic Design Patterns Part 1: Four AI Agent Strategies." *DeepLearning.AI*, March 2024. https://www.deeplearning.ai/the-batch/agentic-design-patterns-part-1-four-ai-agent-strategies/. Accessed April 2025.
- Harrison Chase. "What is an Agent?" *LangChain Blog*, June 2024. https://blog.langchain.dev/what-is-an-agent/. Accessed April 2025.
- LangGraph. "Conditional Edges Documentation." https://langchain-ai.github.io/langgraph/. Accessed April 2025.
