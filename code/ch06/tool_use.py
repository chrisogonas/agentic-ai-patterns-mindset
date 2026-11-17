"""Tool-use loop example with sample tools and a constrained file writer.

Setup from the repository root (PowerShell)::

    python -m pip install openai
    $env:OPENAI_API_KEY = "<your OpenAI API key>"
    python code/ch06/tool_use.py

The script runs ``agent_loop`` with a sample arithmetic question. To use the
loop from another script, run from ``code/ch06``::

    from tool_use import agent_loop

    print(agent_loop("What is 12 * 7 + 5?"))

The search and weather functions return illustrative placeholder results; they
do not call external services. Replace them with real providers before relying
on current data. ``write_file`` is not registered as an LLM tool in this sample:
call it directly with a path under ``ALLOWED_DIRECTORY``. It limits file size
and applies basic content filtering, but those checks are not a complete
security boundary. Tool calls use OpenAI and may incur charges.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from openai import OpenAI


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def search_api(query: str) -> str:
    """Return a placeholder result; replace this function with a search API.

    Args:
        query: Search terms supplied by the caller or model.

    Returns:
        An illustrative result string, not live search data.
    """
    return f"Search results for '{query}': [example result 1, example result 2]"


def get_weather(city: str) -> str:
    """Return a placeholder forecast; replace this with a weather provider.

    Args:
        city: City name to look up.

    Returns:
        An illustrative weather string, not live weather data.
    """
    return f"Weather in {city}: 72°F and sunny"


def calculate(expr: str) -> str:
    """Evaluate a simple arithmetic expression safely."""
    allowed = re.compile(r"^[0-9+\-*/().\s]+$")
    if not allowed.fullmatch(expr):
        return "Error: expression contains unsupported characters"
    try:
        result = eval(expr, {"__builtins__": {}}, {})
    except Exception as exc:  # pragma: no cover - simple safety guard
        return f"Error: could not evaluate expression: {exc}"
    return f"Result: {result}"


def execute_tool(name: str, arguments: dict[str, Any]) -> str:
    """Execute a tool call and return the result as a string."""
    if name == "search_web":
        return search_api(arguments["query"])
    if name == "get_weather":
        return get_weather(arguments["city"])
    if name == "calculate":
        return calculate(arguments["expression"])
    return f"Error: Unknown tool '{name}'"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for current information on a topic. Use when you need fresh facts or data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query. Be specific."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the weather for a city. Use when the user asks about current weather.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name."},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a simple arithmetic expression. Use for calculations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Arithmetic expression such as '2 + 3 * 4'."},
                },
                "required": ["expression"],
            },
        },
    },
]


def agent_loop(user_message: str, max_iterations: int = 6) -> str:
    """Call the model repeatedly, executing requested tools until it responds.

    Args:
        user_message: User request to answer.
        max_iterations: Maximum model turns before returning a limit message.

    Returns:
        The final assistant response or a message indicating the iteration
        limit was reached.
    """
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]

    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS,
        )

        message = response.choices[0].message
        messages.append(message)

        if not getattr(message, "tool_calls", None):
            return message.content or ""

        for tool_call in message.tool_calls:
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as exc:
                result = f"Error: invalid tool arguments: {exc}"
            else:
                result = execute_tool(tool_call.function.name, arguments)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                }
            )

    return "Agent reached maximum iterations without a final response."


ALLOWED_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), "sandbox"))
MAX_FILE_SIZE = 1024 * 1024


def write_file(filepath: str, content: str) -> str:
    """Write filtered content to a size-limited path under ``ALLOWED_DIRECTORY``.

    Args:
        filepath: Absolute path inside ``ALLOWED_DIRECTORY``. Relative paths
            are resolved from the current working directory.
        content: Text to write; content larger than ``MAX_FILE_SIZE`` or
            containing the sample blocked strings is rejected.

    Returns:
        A success message or an explanatory error string. This is a teaching
        example, not a complete security boundary.
    """
    abs_path = os.path.abspath(filepath)
    if not abs_path.startswith(ALLOWED_DIRECTORY):
        return f"Error: access denied. Files outside {ALLOWED_DIRECTORY} are not allowed."

    if len(content.encode("utf-8")) > MAX_FILE_SIZE:
        return f"Error: file exceeds maximum size of {MAX_FILE_SIZE} bytes."

    if "<script" in content.lower() or "drop table" in content.lower():
        return "Error: content contains disallowed material."

    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return f"Wrote {len(content.encode('utf-8'))} bytes to {abs_path}"


if __name__ == "__main__":
    example_prompt = "What is 12 * 7 + 5?"
    print(agent_loop(example_prompt))
