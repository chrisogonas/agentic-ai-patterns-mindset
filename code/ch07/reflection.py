"""Reflection patterns: generate, critique, and improve LLM output.

Setup (PowerShell, from the repository root)::

    python -m pip install openai
    $env:OPENAI_API_KEY = "<your OpenAI API key>"
    python code/ch07/reflection.py

Running this file makes OpenAI API calls and may incur charges. The example at
the bottom runs one self-refinement iteration. To use another pattern, import
its function in your own Python script, for example::

    # Run from the code/ch07 directory.
    from reflection import self_refine_with_rollback

    answer = self_refine_with_rollback(
        "Explain input validation in APIs.",
        max_iterations=2,
        score_fn=lambda text: len(text.split()),
    )
    print(answer)

Other entry points include ``self_refine``, ``reflexion_loop``,
``code_with_critic``, and ``two_agent_reflection``. The LangGraph example is
optional; install ``langgraph`` before calling
``build_langgraph_reflection_agent``. ``evaluate_with_tests`` requires pytest
and runs code with the current user's permissions; it is process isolation, not
a security sandbox. Use trusted code or provide an external sandbox instead.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from typing import Any, TypedDict

from openai import OpenAI


client = OpenAI()
PASS_PATTERN = re.compile(r"^\s*PASS\s*[.!]?\s*$", re.IGNORECASE)


def call_llm(
    prompt: str,
    system: str = "",
    model: str = "gpt-4o",
    temperature: float = 0.7,
) -> str:
    """Send one chat completion request and return the generated text.

    Args:
        prompt: User-task text to send to the model.
        system: Optional system instruction.
        model: OpenAI model identifier.
        temperature: Sampling temperature accepted by the selected model.

    Returns:
        The assistant's text, or an empty string when the response has no text.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def _passed(critique: str) -> bool:
    """Only treat a concise, standalone PASS as a successful evaluation."""
    return bool(PASS_PATTERN.fullmatch(critique))


def self_refine(task: str, max_iterations: int = 3) -> str:
    """Generate, critique, and revise a draft until it passes or runs out of iterations.

    Args:
        task: The output to create or improve.
        max_iterations: Maximum critique-and-revision rounds; zero returns the
            initial draft without critique.

    Returns:
        The latest draft, including the initial draft if no revision was run.
    """
    draft = call_llm(task)

    for _ in range(max(0, max_iterations)):
        critique = call_llm(
            "Review this output and identify specific, actionable weaknesses. "
            "Point to exact phrases, missing elements, or logical gaps. "
            "If the output is good enough, respond with exactly 'PASS'.\n\n"
            f"TASK: {task}\n\nOUTPUT:\n{draft}"
        )
        if _passed(critique):
            break

        draft = call_llm(
            "Revise this output to address the following critique. "
            "Make specific improvements rather than merely rephrasing.\n\n"
            f"ORIGINAL TASK: {task}\n\nCURRENT DRAFT:\n{draft}\n\n"
            f"CRITIQUE:\n{critique}\n\nREVISED OUTPUT:"
        )

    return draft


def self_refine_with_rollback(
    task: str,
    max_iterations: int = 3,
    score_fn: Callable[[str], float] | None = None,
) -> str:
    """Refine a draft while preserving the highest-scoring version seen.

    Args:
        task: The output to create or improve.
        max_iterations: Maximum critique-and-revision rounds.
        score_fn: Optional function that assigns a numeric quality score to a
            draft. When omitted, the latest revision is returned.

    Returns:
        The highest-scoring draft when ``score_fn`` is supplied; otherwise, the
        latest draft.
    """
    draft = call_llm(task)
    best_draft = draft
    best_score = score_fn(draft) if score_fn else 0.0

    for _ in range(max(0, max_iterations)):
        critique = call_llm(
            "Review this output and identify specific, actionable weaknesses. "
            "If it is good enough, respond with exactly 'PASS'.\n\n"
            f"TASK: {task}\n\nOUTPUT:\n{draft}"
        )
        if _passed(critique):
            break

        draft = call_llm(
            "Revise this output to address the following critique.\n\n"
            f"ORIGINAL TASK: {task}\n\nCURRENT DRAFT:\n{draft}\n\n"
            f"CRITIQUE:\n{critique}\n\nREVISED OUTPUT:"
        )

        if score_fn is None:
            best_draft = draft
        else:
            score = score_fn(draft)
            if score > best_score:
                best_draft = draft
                best_score = score

    return best_draft


def reflexion_loop(task: str, max_attempts: int = 3) -> str:
    """Carry concise lessons from failed attempts into subsequent attempts.

    Args:
        task: The output to create or solve.
        max_attempts: Maximum generate-and-evaluate attempts.

    Returns:
        The first passing output, or the last attempt if none passes.
    """
    reflections: list[str] = []
    output = ""

    for attempt in range(max(0, max_attempts)):
        reflection_context = ""
        if reflections:
            reflection_context = (
                "LESSONS FROM PREVIOUS ATTEMPTS:\n"
                + "\n".join(f"- {reflection}" for reflection in reflections)
                + "\n\nApply these lessons and avoid repeating the mistakes.\n\n"
            )

        output = call_llm(
            f"{reflection_context}TASK: {task}\n\n"
            f"Attempt {attempt + 1} of {max_attempts}."
        )
        evaluation = call_llm(
            "Evaluate this output rigorously. Identify errors, omissions, or "
            "weaknesses. If it is correct and complete, respond with exactly 'PASS'.\n\n"
            f"TASK: {task}\n\nOUTPUT:\n{output}"
        )
        if _passed(evaluation):
            return output

        reflection = call_llm(
            "Based on this failed attempt, write one concise lesson about what "
            "went wrong and what to do differently next time.\n\n"
            f"TASK: {task}\n\nOUTPUT:\n{output}\n\nEVALUATION:\n{evaluation}"
        )
        reflections.append(reflection)

    return output


def evaluate_with_tests(code: str, tests: str, timeout: int = 30) -> dict[str, Any]:
    """Run code against pytest tests in a temporary directory.

    Args:
        code: Python source to write as ``solution.py``.
        tests: Pytest test source appended to ``test_solution.py``.
        timeout: Maximum test-process duration in seconds.

    Returns:
        A dictionary with ``passed`` (bool) and ``output`` (pytest output or
        timeout message).

    This is process isolation only, not a security sandbox. Use only with trusted
    code or replace this runner with an externally sandboxed execution service.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        code_path = os.path.join(tmpdir, "solution.py")
        test_path = os.path.join(tmpdir, "test_solution.py")

        with open(code_path, "w", encoding="utf-8") as handle:
            handle.write(code)
        with open(test_path, "w", encoding="utf-8") as handle:
            handle.write(f"from solution import *\n{tests}")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or "") + (exc.stderr or "")
            return {"passed": False, "output": f"Test run timed out after {timeout}s.\n{output}"}

        return {
            "passed": result.returncode == 0,
            "output": result.stdout + result.stderr,
        }


def code_with_critic(task: str, tests: str, max_iterations: int = 3) -> str:
    """Generate code and revise it using concrete pytest feedback.

    Args:
        task: Requirements for the code to generate.
        tests: Pytest source used to evaluate the generated code.
        max_iterations: Maximum test-and-revision rounds.

    Returns:
        The generated or latest revised source. Test execution is not a
        security sandbox; see ``evaluate_with_tests`` before using this helper.
    """
    code = call_llm(
        "Write Python code to solve this task. Return only the code, without "
        f"explanations.\n\n{task}"
    )

    for _ in range(max(0, max_iterations)):
        result = evaluate_with_tests(code, tests)
        if result["passed"]:
            return code

        code = call_llm(
            "This code failed tests. Fix it based on the test output. Return only "
            "the corrected code.\n\n"
            f"TASK: {task}\n\nCURRENT CODE:\n```python\n{code}\n```\n\n"
            f"TEST RESULTS:\n{result['output']}"
        )

    return code


def two_agent_reflection(
    task: str,
    max_iterations: int = 3,
    generator_model: str = "gpt-4o",
    critic_model: str = "gpt-4o",
) -> str:
    """Use separate generator and critic prompts for iterative refinement.

    Args:
        task: The output to create or improve.
        max_iterations: Maximum critique-and-revision rounds.
        generator_model: Model used to draft and revise.
        critic_model: Model used to review the draft.

    Returns:
        The latest draft after passing review or reaching the iteration limit.
    """
    generator_system = (
        "You are an expert writer. Produce high-quality work. When revising, "
        "carefully address every point in the critique."
    )
    critic_system = (
        "You are a demanding editor. Find specific, concrete weaknesses. "
        "Do not praise; identify problems. If there are no significant issues, "
        "respond with exactly 'PASS'."
    )

    draft = call_llm(task, system=generator_system, model=generator_model)
    for _ in range(max(0, max_iterations)):
        response = client.chat.completions.create(
            model=critic_model,
            messages=[
                {"role": "system", "content": critic_system},
                {"role": "user", "content": f"TASK: {task}\n\nOUTPUT:\n{draft}"},
            ],
        )
        critique = response.choices[0].message.content or ""
        if _passed(critique):
            break

        draft = call_llm(
            "Revise your output based on this editorial feedback. Produce an "
            "improved version.\n\n"
            f"CRITIQUE:\n{critique}\n\nORIGINAL TASK: {task}\n\n"
            f"YOUR CURRENT DRAFT:\n{draft}",
            system=generator_system,
            model=generator_model,
        )

    return draft


class ReflectionState(TypedDict):
    task: str
    draft: str
    critique: str
    iteration: int
    max_iterations: int


def build_langgraph_reflection_agent() -> Any:
    """Build the optional LangGraph version of the reflection loop.

    Returns:
        A compiled LangGraph that accepts a ``ReflectionState`` dictionary.
        Invoke it with ``task``, empty ``draft`` and ``critique``, ``iteration``
        set to 0, and a positive ``max_iterations`` value.

    Raises:
        ImportError: If the optional ``langgraph`` package is not installed.
    """
    from langgraph.graph import END, StateGraph

    def generate(state: ReflectionState) -> dict[str, Any]:
        if state.get("critique"):
            draft = call_llm(
                "Revise based on this critique:\n"
                f"{state['critique']}\n\nCurrent draft:\n{state['draft']}"
            )
        else:
            draft = call_llm(state["task"])
        return {"draft": draft, "iteration": state.get("iteration", 0) + 1}

    def evaluate(state: ReflectionState) -> dict[str, str]:
        critique = call_llm(
            "Find specific weaknesses in this output. If it is good enough, "
            "respond with exactly 'PASS'.\n\n"
            f"Task: {state['task']}\nOutput: {state['draft']}"
        )
        return {"critique": critique}

    def should_continue(state: ReflectionState) -> str:
        if state["iteration"] >= state["max_iterations"]:
            return "end"
        if _passed(state.get("critique", "")):
            return "end"
        return "revise"

    graph = StateGraph(ReflectionState)
    graph.add_node("generate", generate)
    graph.add_node("evaluate", evaluate)
    graph.set_entry_point("generate")
    graph.add_edge("generate", "evaluate")
    graph.add_conditional_edges(
        "evaluate",
        should_continue,
        {"revise": "generate", "end": END},
    )
    return graph.compile()


if __name__ == "__main__":
    task = "Write a concise explanation of why input validation matters in APIs."
    print(self_refine(task, max_iterations=1))
