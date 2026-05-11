# Appendix B: Python Environment Setup

Everything you need to run the book's code examples.

## Prerequisites

- **Python 3.11 or later.** Download from [python.org](https://www.python.org/downloads/). Verify with `python --version`.
- **An OpenAI API key.** Sign up at [platform.openai.com](https://platform.openai.com/). The book's examples use the OpenAI SDK as the primary interface. Most examples cost less than $0.10 per run.
- **A text editor or IDE.** VS Code with the Python extension is recommended.

## Environment Setup

### Create a Virtual Environment

```bash
# Create the project directory
mkdir agentic-patterns
cd agentic-patterns

# Create and activate virtual environment
python -m venv .venv

# Activate (Linux / macOS)
source .venv/bin/activate

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Windows Command Prompt)
.venv\Scripts\activate.bat
```

### Install Dependencies

```bash
# Core dependencies (required for all chapters)
pip install openai pydantic httpx

# Chapter-specific dependencies
pip install chromadb          # Chapters 6, 10 — vector storage
pip install pytest            # Chapter 16 — testing examples

# Framework spotlight dependencies (optional)
pip install langchain langchain-openai langgraph   # Chapters 4, 5, 7, 8, 9, 10
pip install crewai                                  # Chapter 12
```

### requirements.txt

Save this as `requirements.txt` in your project root:

```
openai>=1.30.0
pydantic>=2.5.0
httpx>=0.27.0
chromadb>=0.5.0
pytest>=8.0.0
langchain>=0.2.0
langchain-openai>=0.1.0
langgraph>=0.1.0
crewai>=0.30.0
```

Install everything at once: `pip install -r requirements.txt`

## API Key Configuration

**Never hard-code API keys in your source files.** Use environment variables.

```bash
# Linux / macOS — add to ~/.bashrc or ~/.zshrc
export OPENAI_API_KEY="sk-..."

# Windows PowerShell — add to your profile or run per session
$env:OPENAI_API_KEY = "sk-..."
```

Verify the key works:

```python
from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Say hello."}],
    max_tokens=10,
)
print(response.choices[0].message.content)
```

If this prints a greeting, you're set.

## Project Structure

Organize the code examples by chapter:

```
agentic-patterns/
├── requirements.txt
├── utils/
│   ├── __init__.py
│   ├── llm.py            # Shared call_llm() helper
│   └── tracing.py        # Tracer class from Chapter 15
├── ch04_prompt_chaining/
│   └── chain.py
├── ch05_routing/
│   └── router.py
├── ch06_tool_use/
│   └── agent.py
├── ch07_reflection/
│   └── self_refine.py
├── ch08_planning/
│   └── react_agent.py
├── ch09_parallelization/
│   └── parallel.py
├── ch10_memory/
│   └── memory.py
├── ch11_orchestrator_workers/
│   └── orchestrator.py
├── ch12_multi_agent/
│   └── team.py
├── ch13_evaluator_optimizer/
│   └── eval_loop.py
├── ch14_guardrails/
│   └── guardrails.py
├── ch15_evaluation/
│   └── eval_suite.py
└── ch16_production/
    └── production.py
```

## The Shared LLM Helper

Many chapters use a `call_llm()` helper. Create `utils/llm.py`:

```python
from openai import OpenAI, AsyncOpenAI

client = OpenAI()
async_client = AsyncOpenAI()


def call_llm(
    prompt: str,
    system: str = "You are a helpful assistant.",
    model: str = "gpt-4o",
    temperature: float = 0.0,
    max_tokens: int = 2000,
) -> str:
    """Simple synchronous LLM call used throughout the book."""
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


async def call_llm_async(
    prompt: str,
    system: str = "You are a helpful assistant.",
    model: str = "gpt-4o",
    temperature: float = 0.0,
    max_tokens: int = 2000,
) -> str:
    """Async variant for Chapter 9 (Parallelization) and beyond."""
    
    response = await async_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content
```

## Model Availability

The book uses three OpenAI models:

| Model | Used For | Chapters |
|---|---|---|
| `gpt-4o` | Primary reasoning and generation | All |
| `gpt-4o-mini` | Classification, routing, guardrails | 5, 14, 16 |
| `o1` | Complex reasoning tasks | 8 |

If you're using a different provider (Anthropic, Google, local models), swap the model name and SDK calls. The patterns are provider-agnostic — only the API calls change.

## Troubleshooting

**"openai.AuthenticationError"** — Your API key is missing or invalid. Check `echo $OPENAI_API_KEY` (or `$env:OPENAI_API_KEY` on Windows).

**"openai.RateLimitError"** — You've hit the API rate limit. Wait a few seconds and retry. For new accounts, OpenAI applies lower limits that increase over time.

**"ModuleNotFoundError: No module named 'chromadb'"** — Install it: `pip install chromadb`. Only needed for chapters 6 and 10.

**Pydantic validation errors** — Make sure you have Pydantic v2 (`pip install pydantic>=2.5`). The book's structured output examples use v2 syntax.

**Slow responses** — `gpt-4o` calls take 2-10 seconds depending on prompt length. This is normal. `gpt-4o-mini` is 2-3x faster for tasks that don't need the full model.
