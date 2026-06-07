import json
import re
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


def parse_json_response(result: str):
    """Parse a model response as JSON, allowing for surrounding text."""
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        candidate = _extract_json_snippet(result)
        if candidate is None:
            raise ValueError(f"Unable to parse JSON response from LLM:\n{result}")
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            raise ValueError(f"Unable to parse JSON response from LLM after extracting JSON snippet:\n{candidate}")


def _extract_json_snippet(text: str) -> str | None:
    start_chars = "[{"
    open_pairs = {"[": "]", "{": "}"}

    for start_index, char in enumerate(text):
        if char not in start_chars:
            continue

        stack = [char]
        for current_index in range(start_index + 1, len(text)):
            current_char = text[current_index]
            if current_char in start_chars:
                stack.append(current_char)
            elif current_char in open_pairs.values():
                if not stack:
                    break
                opener = stack.pop()
                if open_pairs[opener] != current_char:
                    break
                if not stack:
                    return text[start_index:current_index + 1]

    return None


# This call_llm function is the building block. Every step in the chain calls it with a different prompt. Now the chain itself:

def extract_themes(document: str) -> list[str]:
    """Step 1: Extract key themes from the document."""
    prompt = f"""Read the following document and identify the 3-7 key themes.
        Return ONLY a JSON array of theme strings, no other text.

        Document:
        {document}"""
    
    result = call_llm(prompt)
    themes = parse_json_response(result)
    if not isinstance(themes, list) or len(themes) < 2 or not all(isinstance(theme, str) for theme in themes):
        raise ValueError(
            f"Invalid theme extraction response: expected a JSON list of 2+ strings, got {themes}"
        )
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
    analysis = parse_json_response(result)
    if not isinstance(analysis, dict):
        raise ValueError(
            f"Invalid theme analysis response: expected a JSON object, got {analysis}"
        )

    for theme in themes:
        if theme not in analysis:
            raise ValueError(
                f"Analysis response missing theme '{theme}': {analysis}"
            )
        theme_entry = analysis[theme]
        if not isinstance(theme_entry, dict) or "analysis" not in theme_entry or "quotes" not in theme_entry:
            raise ValueError(
                f"Invalid structure for theme '{theme}': {theme_entry}"
            )
        if not isinstance(theme_entry["quotes"], list) or len(theme_entry["quotes"]) < 2:
            raise ValueError(
                f"Theme '{theme}' must include at least two quotes: {theme_entry}"
            )

    return analysis


def generate_summary(analysis: dict) -> str:
    """Step 3: Produce an executive summary from the analysis."""
    prompt = f"""Based on the following thematic analysis, write a concise 
        executive summary (200-300 words). Lead with the most important finding. 
        Use clear, direct language suitable for a senior executive.

        Analysis:
        {json.dumps(analysis, indent=2)}"""
    
    return call_llm(prompt)


# Three functions, three LLM calls, each with a single clear job. Now we wire them together with gates:

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
    
