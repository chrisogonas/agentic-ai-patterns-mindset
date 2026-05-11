# Chapter 2: The Agentic Engineering Mindset

Building agentic systems requires a different way of thinking about software. Traditional engineering assumes deterministic execution: given the same input, the system produces the same output, following the same path. Agentic engineering abandons this assumption. You are designing systems that make decisions, adapt to unexpected situations, and occasionally do things you didn't predict.

This shift doesn't require a new programming language or a new technology stack. It requires a new mental model. This chapter covers the six principles that define it.

## Delegation, Not Automation

The first mindset shift is the hardest: stop thinking about automating tasks and start thinking about *delegating* them.

Automation means specifying every step. You write the function, define the branches, handle the edge cases. The computer executes your instructions. You are the decision-maker. The computer is the executor.

Delegation means specifying the *goal* and letting the system determine the steps. You describe what you want, provide the tools and constraints, and let the agent figure out how to get there. The agent is the decision-maker. You are the architect of the environment in which it decides.

This is the same shift that happens when an engineer becomes a manager. As an individual contributor, you write the code. As a manager, you define objectives, provide resources, set boundaries, and trust your team to execute. Some managers struggle with this transition because they can't let go of control. The same happens with engineers building agents.

The practical consequences are significant:

**You debug differently.** With traditional code, you step through execution and find the line that went wrong. With agents, you examine the *decision that went wrong* — the reasoning trace, the tool selection, the misinterpretation of a result. Your debugging tools must show you what the agent thought, not just what it did.

**You test differently.** Unit tests verify specific outputs for specific inputs. Agent tests verify *behavior patterns*: Does the agent use appropriate tools? Does it recover from errors? Does it know when to stop? Does it escalate when uncertain? You test judgment, not just correctness.

**You specify differently.** Instead of writing detailed procedural instructions, you write clear intent descriptions, well-designed tool interfaces, and explicit constraints. The quality of your agent depends on the quality of these specifications far more than on the orchestration logic.

Andrew Ng draws an analogy to hiring: "When you hire a new team member, you don't script every minute of their day. You describe their role, give them tools and access, set expectations, and let them work." Agentic engineering is the same. The agent is your new hire. Your job is to set it up for success, not to micromanage its execution.

## Trust Calibration

The second principle follows directly from the first: you must calibrate how much autonomy to give the system.

Trust calibration is not a binary choice between "fully autonomous" and "fully supervised." It's a spectrum, and the right setting depends on three factors:

**Stakes.** An agent that drafts marketing copy can operate with high autonomy — the worst case is a mediocre paragraph that a human can fix. An agent that executes financial transactions should operate under tight constraints with mandatory human approval for anything above a threshold.

**Reliability.** How consistently does the agent make good decisions for this type of task? If your testing shows 95% accuracy on a particular workflow, that means 1 in 20 runs will go wrong. Is that acceptable? The answer depends on the cost of errors.

**Reversibility.** Can you undo what the agent does? An agent that writes files can be corrected. An agent that sends emails to customers cannot unsend them. Design for reversibility wherever possible, and require human approval wherever it isn't possible.

The practical framework for trust calibration looks like this:

| Trust Level | Description | Example |
|---|---|---|
| **Full supervision** | Agent proposes actions; human approves each one | Financial transactions, legal documents |
| **Guided autonomy** | Agent acts freely within defined boundaries; flags exceptions | Customer service within policy, code changes within a sandbox |
| **High autonomy** | Agent operates independently; human reviews outputs periodically | Report generation, data analysis, research synthesis |
| **Full autonomy** | Agent operates and resolves issues without human intervention | Internal monitoring, routine data processing |

Most production agents today operate at *guided autonomy* — the sweet spot where the agent is useful enough to save significant time while constrained enough to prevent significant damage. As reliability improves and trust is earned (through metrics, not intuition), you expand the boundaries.

The key insight: **trust is earned through measurable performance, not through architectural complexity.** A simple agent that you can verify is more trustworthy than a sophisticated one you can't.

## The Agent-Computer Interface (ACI)

When you build a web application, you invest heavily in the user interface — the Human-Computer Interface (HCI). You study how users interact with forms, buttons, and navigation. You refine layouts, error messages, and affordances. You know that a confusing interface leads to user errors, regardless of how correct the backend is.

Agents interact with tools, and the interface they use deserves the same care. Anthropic calls this the Agent-Computer Interface (ACI), and their recommendation is direct: *invest as much effort in designing your ACI as you would in designing a human-facing UX.*

What does excellent ACI design look like?

**Clear tool names and descriptions.** The LLM selects tools based on their names and descriptions. Vague or ambiguous descriptions lead to wrong tool selections — the agentic equivalent of a user clicking the wrong button because the label was confusing. Instead of `process_data`, use `transform_csv_to_json_with_column_filtering`.

**Explicit parameter schemas.** Every parameter should have a type, a description, and examples where helpful. Enum types are preferable to free-text parameters — they constrain the agent's choices to valid options. Think of this as the equivalent of a dropdown menu vs. a free-text field.

**Minimized required input.** Don't require the agent to provide information it doesn't have or can't reliably generate. If a function can determine a sensible default, use it. Reduce the number of decisions the agent needs to make per tool call.

**Helpful error messages.** When a tool call fails, the error message should tell the agent what went wrong and how to fix it. "File not found" is useless. "File 'report.csv' not found in /data/. Available files: sales.csv, users.csv, orders.csv" lets the agent recover autonomously.

**Poka-yoke design.** The Japanese manufacturing term for "mistake-proofing." Anthropic's SWE-bench coding agent provides a concrete example: they changed their file editing tool to use *absolute paths* instead of relative paths, eliminating an entire category of errors where the agent referenced the wrong file. The lesson: if you can change the tool to make a class of mistakes impossible, do it rather than prompting the agent to be careful.

ACI design is not a one-time activity. It's iterative. Log your agent's tool usage in production, analyze failures, and refine the interface. Most performance improvements come from making tools easier for the agent to use correctly, not from making the agent smarter.

## Start Simple, Add Complexity Only When It Helps

Anthropic's most emphatic recommendation across their work with production teams: **resist the urge to build complex agentic systems when simpler solutions work.**

This principle sounds obvious. In practice, it's routinely violated. Engineers discover agents and want to build a four-layer multi-agent orchestration system when a well-crafted prompt would do the job. The result is a system that's harder to debug, more expensive to run, and no more effective.

The hierarchy of complexity:

1. **Single LLM call with a well-designed prompt.** Try this first. Always. You will be surprised how often this is sufficient.
2. **Prompt chain.** Break the task into sequential steps. Add validation between steps. Still no agent — just a workflow.
3. **Router + specialized prompts.** Classify the input and route to different prompts or models. Still deterministic.
4. **LLM with tools.** Give the model the ability to take actions. Now you have a minimal agent.
5. **Agent with reflection loops.** The agent can critique and improve its own output.
6. **Multi-agent system.** Multiple agents with different specializations collaborate.

Each level adds latency, cost, and debugging complexity. Only move up when you can demonstrate — with measurements, not intuition — that the higher level improves outcomes enough to justify the cost.

The teams Anthropic found most successful "weren't building complex frameworks or specialized libraries. Instead, they were building with simple, composable patterns." The word *composable* is key. Build small, focused components that you can combine when needed, rather than monolithic architectures that try to do everything.

A concrete test: before adding a new layer of complexity, ask yourself two questions:

1. "Can I solve this with a better prompt?" (Usually yes.)
2. "What specific failure mode does this complexity address?" (If you can't name one, you don't need it.)

## Design for Observability from Day One

With deterministic code, you can reason about behavior from the source. Read the function, follow the logic, predict the output. With agents, you can't. The LLM is a black box that makes different decisions in different contexts. You *must* be able to see inside.

Observability in agentic systems means capturing three things:

**The reasoning trace.** What did the agent "think" at each step? What was in its context window? What options did it consider? If the agent made a bad decision, you need to see the decision process, not just the outcome.

**The action log.** What tools were called, with what parameters, and what results were returned? This is the equivalent of a traditional application log, but richer because each action was a *decision* made by the agent.

**The cost and performance metrics.** How many tokens were consumed? How many LLM calls were made? How long did each step take? Agents can be surprisingly expensive, and without metrics, you won't know until the bill arrives.

The practical approach:

- **Log everything from the start.** It's much harder to add instrumentation retroactively to an agentic system than to a traditional application. The data you need for debugging is the same data you need for evaluation. Capture it upfront.
- **Use structured logging.** Each agent step should emit a structured event with a trace ID, step number, action type, input, output, model used, tokens consumed, and wall-clock time.
- **Build a trace viewer early.** You will spend significant time reading agent traces — it's the primary debugging activity. A good trace viewer pays for itself within the first week.
- **Set cost budgets.** Implement hard limits on tokens per task, iterations per task, and total cost per session. Agents without cost bounds in development will develop execution patterns that are unsustainable in production.

Chapter 15 covers evaluation and observability tooling in detail. The point here is not how to implement it, but when: *from the very beginning.*

## Graceful Failure as a Feature

Traditional software fails abruptly. An uncaught exception, a crash, a 500 error. The system either works or it doesn't.

Agents fail differently. They rarely crash — the LLM always produces *something*. Instead, they fail subtly: they use the wrong tool, produce plausible-sounding but incorrect output, get stuck in loops, or quietly ignore part of the task. These failures are harder to detect and harder to diagnose than a clean crash.

Designing for graceful failure means anticipating these modes and building in responses:

**Tool failures.** An external API returns an error. A file doesn't exist. A database query times out. Your agent should detect the failure, understand it, and attempt recovery — try an alternative tool, adjust parameters, or work around the issue. This was the behavior Andrew Ng observed when his research agent hit a rate-limited API and pivoted to an alternative search tool.

**Reasoning failures.** The agent's plan doesn't work. A subtask produces unexpected results. The problem turns out to be different from what the agent anticipated. The agent should be able to *replan* — step back, reassess, and try a different approach rather than stubbornly continuing a failing strategy.

**Scope failures.** The task is too hard, too ambiguous, or outside the agent's capabilities. The agent should recognize this and escalate to a human rather than producing low-confidence output. *Knowing when to stop* is one of the hardest things to teach an agent and one of the most important.

**Loop detection.** Agents can get stuck repeating the same action, expecting different results. Implement maximum iteration limits, but also detection logic: if the agent calls the same tool with the same parameters twice in a row, that's a signal to change strategy.

The key design principle: **an agent should fail like a responsible employee.** When something goes wrong, it should report the problem clearly, explain what it tried, hand off what it has so far, and flag what remains unresolved. The worst outcome is an agent that silently produces bad output and presents it with confidence.

This is why observability and failure design are closely linked. You can't design for failure if you can't see what's happening. And you can't build trust (the second principle) without evidence of how the system behaves when things go wrong.

---

## Principles in Practice

These six principles are not independent. They reinforce each other:

- You *delegate* a task, which means you must *calibrate trust* for how the agent will handle it.
- You calibrate trust by measuring performance, which requires *observability*.
- You build good tools (*ACI design*) because clarity reduces errors and builds trust.
- You *start simple* because simpler systems are easier to observe and easier to trust.
- You design for *graceful failure* because trusted systems must fail transparently.

The mental model is this: you are building a working relationship with a capable but imperfect collaborator. Like any working relationship, it improves with clear communication (ACI), appropriate scope (simplicity), visibility into process (observability), proportional autonomy (trust calibration), and honest acknowledgment of limits (graceful failure).

The rest of this book is patterns and implementation. But patterns without the right mindset are just code. The mindset without patterns is just philosophy. You need both.

---

## Sources

- Anthropic. "Building Effective Agents." *Anthropic Engineering*, December 2024. <https://www.anthropic.com/engineering/building-effective-agents>. Accessed April 2026.

- Ng, A. "Agentic Design Patterns Part 1: Four AI agent strategies that improve GPT-4 and GPT-3.5 performance." *The Batch, DeepLearning.AI*, March 2024. <https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/>. Accessed April 2026.

- Ng, A. "Agentic Design Patterns Part 4: Planning." *The Batch, DeepLearning.AI*, April 2024. <https://www.deeplearning.ai/the-batch/agentic-design-patterns-part-4-planning/>. Accessed April 2026.
