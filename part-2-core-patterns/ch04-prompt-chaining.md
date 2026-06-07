# Chapter 4: Prompt Chaining

You need an LLM to analyze a legal contract. It should identify the parties involved, extract key obligations, flag risky clauses, and produce a summary memo suitable for a non-lawyer. You could stuff all of that into a single mega-prompt — and watch the model drop obligations, misclassify risks, and produce a muddled summary. Or you could decompose the work.

Prompt chaining is the simplest agentic pattern, and for many real-world tasks, it is all you need. You break a complex task into a sequence of focused LLM calls, where each call does one thing well and passes its output to the next. Between calls, you insert programmatic gates — validation checks, transformations, filters — that catch errors before they propagate.

If Chapter 2's mindset principle was "start simple, add complexity only when it helps," prompt chaining is what *starting simple* looks like in practice.

## How It Works

The architecture is a pipeline:

```
Input → [Step 1] → Gate → [Step 2] → Gate → [Step 3] → Output
              ↓              ↓              ↓
          Validation     Transform      Validation
```

Each step is a single LLM call with a tightly scoped prompt. Each gate is ordinary code — an `if` statement, a schema validator, a word count check. The LLM handles the cognitive work. Your code handles the plumbing.

This division matters. One of the recurring lessons from production agentic systems is that **the more you can push into deterministic code, the more reliable your system becomes.** An LLM should not be counting words. It should not be validating JSON. It should not be deciding whether step 2 received valid input from step 1. Those are jobs for code.

Three properties make prompt chaining effective:

1. **Focused scope.** Each prompt asks the model to do one cognitive operation. "Extract the parties from this contract" is a clearer task than "analyze this entire contract and produce a memo." Narrower scope means higher accuracy.

2. **Verifiable intermediates.** Because you have programmatic access to each step's output, you can check it. Does the extracted party list contain at least two entries? Is each entry a properly formatted entity name? You can catch failures immediately rather than discovering them in the final output.

3. **Transparent debugging.** When something goes wrong, you know *which step* failed. You see its exact input and output. Compare this to debugging a single monolithic prompt where you have no visibility into the model's internal reasoning process.

## Implementation in Python

Let's build a concrete prompt chain. We'll create a content analysis pipeline that takes a raw document, extracts key themes, generates a structured analysis, and produces an executive summary.

```python
import json
from openai import OpenAI

client = OpenAI()

def call_llm(prompt: str, system: str = "") -> str:
    """Single LLM call with a focused prompt."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.3,
    )
    return response.choices[0].message.content
```

This `call_llm` function is the building block. Every step in the chain calls it with a different prompt. Now the chain itself:

```python
def extract_themes(document: str) -> list[str]:
    """Step 1: Extract key themes from the document."""
    prompt = f"""Read the following document and identify the 3-7 key themes.
Return ONLY a JSON array of theme strings, no other text.

Document:
{document}"""
    
    result = call_llm(prompt)
    themes = json.loads(result)
    return themes


def analyze_themes(document: str, themes: list[str]) -> dict:
    """Step 2: Analyze each theme with supporting evidence."""
    prompt = f"""For each theme listed below, provide:
- A one-paragraph analysis
- Two direct quotes from the document that support it

Themes: {json.dumps(themes)}

Document:
{document}

Return your analysis as a JSON object where each key is a theme 
and the value is an object with "analysis" and "quotes" fields."""
    
    result = call_llm(prompt)
    analysis = json.loads(result)
    return analysis


def generate_summary(analysis: dict) -> str:
    """Step 3: Produce an executive summary from the analysis."""
    prompt = f"""Based on the following thematic analysis, write a concise 
executive summary (200-300 words). Lead with the most important finding. 
Use clear, direct language suitable for a senior executive.

Analysis:
{json.dumps(analysis, indent=2)}"""
    
    return call_llm(prompt)
```

Three functions, three LLM calls, each with a single clear job. Now we wire them together with gates:

```python
def content_analysis_chain(document: str) -> dict:
    """Full prompt chain with validation gates."""
    
    # Step 1: Extract themes
    themes = extract_themes(document)
    
    # Gate 1: Validate theme extraction
    if not isinstance(themes, list) or len(themes) < 2:
        raise ValueError(
            f"Theme extraction failed: expected 2+ themes, got {themes}"
        )
    
    # Step 2: Analyze themes
    analysis = analyze_themes(document, themes)
    
    # Gate 2: Validate analysis completeness
    missing = [t for t in themes if t not in analysis]
    if missing:
        raise ValueError(
            f"Analysis incomplete: missing themes {missing}"
        )
    
    # Step 3: Generate summary
    summary = generate_summary(analysis)
    
    # Gate 3: Validate summary length
    word_count = len(summary.split())
    if word_count < 100:
        raise ValueError(
            f"Summary too short: {word_count} words (minimum 100)"
        )
    
    return {
        "themes": themes,
        "analysis": analysis,
        "summary": summary,
    }
```

The gates are simple — type checks, length checks, completeness checks. Nothing sophisticated. But they catch real failures. Without Gate 1, a malformed theme extraction silently produces a garbage analysis. Without Gate 2, a partially completed analysis feeds an incomplete summary. The gates turn silent failures into explicit errors you can diagnose and fix.

## Designing Effective Gates

Gates are the engineering value-add that separates prompt chaining from naively pasting outputs together. There are three types:

**Validation gates** check that a step's output meets structural or quality requirements. Does the JSON parse? Does the list have the right number of items? Does the text exceed a minimum length? These are cheap — pure code, no LLM call needed.

```python
def validate_json_output(text: str, required_keys: list[str]) -> dict:
    """Validation gate: parse JSON and check required fields."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Step output is not valid JSON: {e}")
    
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    
    return data
```

**Transformation gates** reshape one step's output into the format the next step needs. Maybe step 1 produces a full JSON object, but step 2 only needs the values from one field. Maybe you need to truncate long intermediate results to fit within context limits. These are also pure code.

```python
def truncate_to_context(text: str, max_tokens: int = 3000) -> str:
    """Transformation gate: truncate intermediate output to fit."""
    words = text.split()
    # Rough estimate: 1 token ≈ 0.75 words
    max_words = int(max_tokens * 0.75)
    if len(words) > max_words:
        return " ".join(words[:max_words]) + "\n\n[Truncated for context]"
    return text
```

**LLM-as-judge gates** use a separate LLM call to evaluate whether the previous step's output is good enough to proceed. This is more expensive — it adds an extra LLM call — but necessary when quality checks are too nuanced for code alone.

```python
def quality_gate(step_output: str, criteria: str) -> bool:
    """LLM-as-judge gate: evaluate output quality."""
    prompt = f"""Evaluate the following output against this criterion:
Criterion: {criteria}

Output to evaluate:
{step_output}

Does the output meet the criterion? Respond with exactly 
"PASS" or "FAIL" followed by a one-sentence explanation."""
    
    judgment = call_llm(prompt, system="You are a strict quality evaluator.")
    return judgment.strip().startswith("PASS")
```

Use LLM-as-judge gates sparingly. They double the cost of a step. But for high-stakes chains — medical document analysis, legal review, financial reporting — the cost is justified.

## Handling Failures

What happens when a gate rejects a step's output? You have three options:

**Retry.** Run the same step again, possibly with a modified prompt. LLM outputs are non-deterministic, so a second attempt may succeed where the first failed. Set a maximum retry count to avoid infinite loops.

```python
def step_with_retry(step_fn, *args, max_retries: int = 2):
    """Retry a chain step on failure."""
    for attempt in range(max_retries + 1):
        try:
            result = step_fn(*args)
            return result
        except (ValueError, json.JSONDecodeError) as e:
            if attempt == max_retries:
                raise
            print(f"Step failed (attempt {attempt + 1}): {e}. Retrying...")
```

> [!TIP]
> **Production consideration: exponential backoff.** The retry above fires immediately, which is fine for parsing errors. For API errors (rate limits, timeouts), add exponential backoff with jitter to avoid thundering herds:
>
> ```python
> import time, random
>
> def step_with_backoff(step_fn, *args, max_retries: int = 3):
>     for attempt in range(max_retries + 1):
>         try:
>             return step_fn(*args)
>         except Exception as e:
>             if attempt == max_retries:
>                 raise
>             delay = (2 ** attempt) + random.uniform(0, 1)
>             print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
>             time.sleep(delay)
> ```
>
> For most production chains, the `tenacity` library provides configurable retry policies with less boilerplate.

**Fallback.** Switch to a simpler approach. If structured JSON extraction fails, fall back to free-text extraction with a regex. If theme analysis fails, skip it and generate the summary directly from the document. Graceful degradation beats hard failure.

**Abort with context.** Stop the chain and return what you have so far, along with a clear description of where and why it failed. This is often the right choice for user-facing systems — show partial results and explain the gap rather than returning nothing.

## Case Study: Content Generation Pipeline

Let's apply prompt chaining to a realistic content generation task. A marketing team needs to produce blog posts from product briefs. The chain:

1. **Outline Generation.** Given a product brief and target audience, generate a structured blog post outline with 5-8 sections.
2. **Section Drafting.** For each section in the outline, draft 150-250 words. Each drafting call receives the outline for context and produces one section.
3. **Consistency Review.** Pass the complete assembled draft to an LLM for consistency checking: tone alignment, jargon usage, factual coherence.
4. **Final Edit.** Apply the consistency review's feedback to produce the final draft.

```python
def blog_generation_chain(brief: str, audience: str) -> str:
    """Generate a blog post from a product brief."""
    
    # Step 1: Generate outline
    outline_prompt = f"""Create a blog post outline for the following product brief.
Target audience: {audience}
Include 5-8 sections, each with a title and 1-sentence description.
Return as JSON: [{{"title": "...", "description": "..."}}]

Brief: {brief}"""
    
    outline_raw = call_llm(outline_prompt)
    outline = json.loads(outline_raw)
    
    # Gate: must have 5-8 sections
    assert 5 <= len(outline) <= 8, f"Outline has {len(outline)} sections"
    
    # Step 2: Draft each section (sequential, each sees the full outline)
    sections = []
    for section in outline:
        section_prompt = f"""Write 150-250 words for this blog section.
        
Section title: {section['title']}
Section purpose: {section['description']}
Target audience: {audience}
Full outline for context: {json.dumps(outline)}

Write ONLY this section. Use a conversational, authoritative tone."""
        
        draft = call_llm(section_prompt)
        
        # Gate: word count check
        wc = len(draft.split())
        if wc < 80:  # Allow some flexibility below 150
            draft = call_llm(section_prompt)  # Simple retry
        
        sections.append(f"## {section['title']}\n\n{draft}")
    
    full_draft = "\n\n".join(sections)
    
    # Step 3: Consistency review
    review_prompt = f"""Review this blog post draft for:
1. Tone consistency across sections
2. Redundant points between sections
3. Jargon that the target audience ({audience}) wouldn't understand
4. Missing transitions between sections

Provide specific, actionable feedback as a numbered list.

Draft:
{full_draft}"""
    
    feedback = call_llm(review_prompt)
    
    # Step 4: Apply feedback
    edit_prompt = f"""Revise this blog post based on the editorial feedback below.
Make targeted changes — don't rewrite sections that don't need it.

Feedback:
{feedback}

Current draft:
{full_draft}"""
    
    final = call_llm(edit_prompt)
    return final
```

Notice the design decisions. Step 2 loops — each section gets its own LLM call. This is deliberate. If the model drafted all sections in one call, you'd lose granular control and validation. By separating them, you can check word counts per section and retry individual sections without re-generating the entire draft.

Step 3 is a read-only step. It produces feedback but doesn't modify the draft. Step 4 applies the feedback. This separation prevents a common failure mode: asking the model to simultaneously critique and rewrite, which often results in it either over-editing (rewriting everything) or under-editing (rubber-stamping its own work).

**Results:** The marketing team measured the chained pipeline against single-prompt generation across 50 blog posts. The chain produced posts scoring 8.2/10 on editorial review versus 6.1/10 for the single-pass version — a 34% quality improvement. Average chain execution: 10 LLM calls (1 outline + 6 sections + 1 review + 1 edit + ~1 retry), ~$0.08 per post, 15-20 seconds. The team's editors estimated 45 minutes of editing per single-pass draft versus 15 minutes per chained draft.

## Framework Spotlight: LangChain LCEL

LangChain's Expression Language (LCEL) provides a declarative syntax for building prompt chains. The same content analysis pipeline looks like this:

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

# Define each step as a chain
extract_themes_chain = (
    ChatPromptTemplate.from_template(
        "Read this document and identify 3-7 key themes. "
        "Return ONLY a JSON array of theme strings.\n\n{document}"
    )
    | llm
    | JsonOutputParser()
)

# Invoke
themes = extract_themes_chain.invoke({"document": some_document})
```

LCEL chains compose with the `|` (pipe) operator, which is syntactically clean. The framework handles output parsing, retries, and streaming. For simple chains, this is convenient.

But there's a tension. Anthropic's recommendation — and the position this book takes — is to **understand the underlying code before reaching for an abstraction.** If your chain has three sequential steps with validation gates, plain Python is more debuggable and more transparent than a framework pipeline. If your chain has twenty steps with complex routing and error handling, the framework's built-in features start earning their weight.

The honest answer: for prompt chaining specifically, the framework adds less value than for more complex patterns. The pattern is inherently simple. The Python implementation is clear. You're not fighting concurrency, state management, or dynamic routing. Save the framework firepower for patterns that need it.

## Token Cost Profile

> **Cost structure:** N sequential LLM calls (one per step), each processing its own input plus the prior step's output.
>
> **Typical range:** A 3-step chain processing a 1,000-word input generates roughly 8,000–15,000 total tokens (input + output across all steps). Each additional step adds ~2,000–5,000 tokens depending on output length and how much prior context is forwarded.
>
> **Cost multiplier vs. single call:** 2–5× (linear in the number of steps).
>
> **Where cost grows:** Deep chains with full context forwarding — if every step sees all prior outputs, later steps consume disproportionately more input tokens. Summarizing intermediate results (lossy) or passing only structured outputs (selective) controls this.
>
> **Cost-saving tip:** Use a cheaper model (e.g., `gpt-4o-mini`) for validation gates. A gate call that checks structure or length is simple classification — it doesn't need a frontier model.

## Tradeoffs and Failure Modes

**Latency scales linearly.** A chain of N steps makes N sequential LLM calls. A 4-step chain with 2-second calls takes 8 seconds minimum. For user-facing applications, this is significant. Mitigations: parallelize independent steps (Chapter 9), use faster models for simple steps, stream intermediate results to keep users informed.

**Error propagation is the primary risk.** If step 1 produces a subtly wrong output — themes that are too vague, an analysis that misses key points — every downstream step inherits the error. Gates help, but they can only catch structural (not semantic) failures. The deeper a chain runs, the more you need quality validation at each stage.

**Over-decomposition wastes resources.** Breaking a task into 10 steps when 3 would suffice adds cost, latency, and complexity without improving quality. Each step boundary is a point where context can be lost — the LLM in step 5 doesn't see the raw input from step 1 unless you explicitly pass it. Too many steps means too many opportunities for context to degrade.

**Context windows have limits.** Each step only sees what you pass it. If step 4 needs information from step 1, you need to either pass the raw output forward (consuming tokens) or summarize it (risking information loss). Managing this context budget is a real engineering problem in deep chains.

A useful heuristic from Anthropic: **each step in the chain should represent a genuine cognitive boundary** — a point where a human would naturally "hand off" to the next phase of work. If you can't explain why two operations are in separate steps, merge them.

### Observability Checklist

> **What to log:** Input/output of every step, step latency, gate pass/fail decisions, token counts per step, total chain latency.
>
> **Key metrics:** Step success rate (per step), gate rejection rate, end-to-end latency (P50/P95), token spend per chain run, error propagation rate (how often a step produces output that causes downstream failure).
>
> **Alerts to set:** Chain latency exceeding SLA, any step failing >5% of the time, gate rejection rate spiking (input distribution shift), total token spend per chain rising unexpectedly.
>
> **Debugging tip:** Log step boundaries with unique trace IDs. When the final output is wrong, you need to identify *which step* introduced the error. Without per-step logging, you're debugging a black box.

## When NOT to Use Prompt Chaining

Prompt chaining is the wrong pattern when:

- **A single LLM call suffices.** Classification, simple Q&A, translation, summarization of short texts — these don't benefit from decomposition. Adding steps adds latency and cost for no quality gain.

- **Steps are deeply interdependent.** If step 3 needs to modify the output of step 1 based on what step 2 found, you don't have a clean pipeline — you have a loop. Use reflection (Chapter 7) or planning (Chapter 8) instead.

- **The task requires dynamic decision-making.** If the number or type of steps depends on intermediate results — sometimes you need 3 steps, sometimes 7 — you need routing (Chapter 5) or an orchestrator (Chapter 11), not a fixed-sequence chain.

- **Latency is critical.** Real-time applications where every millisecond counts can't afford sequential multi-step processing. Consider parallelization (Chapter 9) or reducing to fewer steps.

Prompt chaining is a workhorse pattern. It handles a surprising range of tasks with minimal architectural complexity. When your task has clear sequential phases — extract, transform, validate, generate — reach for this pattern first. Only when it proves insufficient should you consider the more complex patterns in the chapters ahead.

## Review Questions

**Knowledge & Design Questions:**

1. You are given two tasks to automate: (A) "Analyze a legal contract, extract parties, flag risks, and produce a summary," and (B) "Translate a single sentence into five languages." For each, decide whether prompt chaining is the right choice. Explain your reasoning by referring to the three properties that make prompt chaining effective (focused scope, verifiable intermediates, transparent debugging). What pattern would you use instead for the task where chaining is wrong?

2. In a prompt chain for document analysis, you extract entities in step 1 and classify them in step 2. Step 2's output is a JSON object with an entity list. Design three gates that should run between step 1 and step 2. For each gate, explain what it validates and how it would fail gracefully (i.e., what happens if the gate rejects the output).

3. Your prompt chain for customer support triage (route → classify severity → draft response) suddenly starts producing wrong classifications at step 2. Walk through the debugging process: what would you log at each step to isolate the root cause? How would this process be different if you had used a single monolithic prompt instead?

4. Compare the costs and latency tradeoffs between: (A) a single detailed prompt that handles extract+classify+summarize, and (B) a three-step chain with the same final quality. When would you choose each? At what point (e.g., 10,000 daily requests) would the cost difference matter?

**Implementation Questions:**

5. Extend the contract analysis code from this chapter to handle failure recovery: if step 2 (obligation extraction) returns an empty list, add a gate that automatically retries with a refined prompt rather than failing. Write the gate code and explain how it prevents cascading failures downstream.

6. Design and implement a new prompt chain that takes a research topic, (step 1) generates 3 candidate thesis statements, (step 2) evaluates each for clarity and novelty, and (step 3) produces a final ranked list with confidence scores. Write working Python code using the patterns from this chapter. Include at least two meaningful gates between steps and demonstrate what happens when a gate rejects invalid output.

## Sources
- Andrew Ng. "Agentic Design Patterns Part 1." *DeepLearning.AI*, March 2024. <https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/>. Accessed April 2025.
- Harrison Chase. "What is an Agent?" *LangChain Blog*, June 2024. <https://blog.langchain.dev/what-is-an-agent/>. Accessed April 2025.
- LangChain. "LangChain Expression Language (LCEL) Documentation." <https://python.langchain.com/docs/concepts/lcel/>. Accessed April 2025.
