# Chapter 1: What Is an Agent? (And What Isn't)

Every few months, a new AI demo captures the internet's attention. An LLM writes working code. A chatbot handles customer complaints without a script. A research assistant reads fifty papers and produces a synthesis no human had time to write. Each time, the same word surfaces: *agent*.

But the word is doing too much work. A chatbot that follows a fixed script is called an agent. A system that dynamically plans, selects tools, and recovers from failures is also called an agent. The salesperson pitching you an API wrapper calls it an "autonomous agent." The researcher publishing in NeurIPS uses the same term for something fundamentally different.

This chapter draws the boundaries. Before you can engineer agentic systems, you need to know what the term means — and, just as importantly, what it doesn't.

## The Agentic Spectrum

The most useful way to think about agents isn't as a binary — agent or not agent — but as a spectrum of autonomy. Harrison Chase of LangChain expressed this well: rather than arguing over which systems qualify as "true agents," we should acknowledge that systems can be *more or less agentic*.

Consider four levels:

**Level 1: Direct Prompting.** You send a message to an LLM, it returns a response. No tools, no loops, no decisions. This is a chat interface. It is not agentic in any meaningful sense, but it's how most people still interact with language models.

**Level 2: Router.** The LLM classifies an input and directs it to one of several predefined paths. A customer service system that distinguishes between billing questions, technical issues, and refund requests — then routes each to a specialized handler — operates at this level. The LLM makes a single decision, but the downstream workflow is fixed.

**Level 3: State Machine.** The system uses an LLM at multiple decision points, with branching logic and the ability to loop. It can decide whether to continue or stop. A coding assistant that generates code, runs tests, examines failures, and iterates until the tests pass operates here. The LLM controls flow at multiple junctures, but within a designed structure.

**Level 4: Autonomous Agent.** The system dynamically plans its approach, selects from available tools, executes multi-step strategies, learns from intermediate results, and determines when the task is complete. It operates in a loop driven by environmental feedback rather than a predetermined path. A research agent that formulates search queries, reads results, identifies gaps, reformulates, and synthesizes — deciding each step based on what it finds — operates at this level.

Most production systems today live at Levels 2 and 3. Level 4 is where the field is headed, and where most of this book's patterns apply. But the key insight is evolutionary, not revolutionary: you build toward autonomy incrementally, and you should understand every level beneath the one you're targeting.

## Workflows vs. Agents: The Anthropic Distinction

Anthropic, working with dozens of teams building LLM applications across industries, arrived at a useful architectural distinction:

**Workflows** are systems where LLMs and tools are orchestrated through predefined code paths. The developer designs the sequence. The LLM contributes intelligence at specific steps, but the overall flow is deterministic and known in advance.

**Agents** are systems where LLMs dynamically direct their own processes and tool usage, maintaining control over how they accomplish tasks. The developer designs the environment — the tools, the constraints, the stopping conditions — but the agent decides what to do and in what order.

This is not a value judgment. Workflows are not inferior to agents. They are predictable, debuggable, and cheaper to run. For many problems, a well-designed workflow outperforms an agent. The consistent finding from Anthropic's work with production teams is that "the most successful implementations weren't using complex frameworks or specialized libraries. Instead, they were building with simple, composable patterns."

The decision between workflow and agent reduces to a practical question: *Can you predict the steps needed to solve this problem in advance?* If yes, build a workflow. If the steps depend on intermediate results in ways you cannot anticipate, build an agent.

## The Augmented LLM: The Fundamental Building Block

Whether you're building a workflow or an agent, the foundational unit is the same: an LLM enhanced with three capabilities.

**Retrieval.** The model can access external information — documents, databases, APIs, search engines — to ground its responses in current, domain-specific knowledge. Without retrieval, the model is limited to what it learned during training.

**Tools.** The model can take actions in the world — execute code, send emails, query databases, call APIs, manipulate files. Tools transform the LLM from a text generator into an actor. Tool use is arguably the single most important capability that separates an agent from a chatbot.

**Memory.** The model can maintain state across interactions — remembering what happened earlier in a conversation, what a user prefers, what strategies worked on previous tasks. Without memory, every interaction starts from zero.

```
                    ┌─────────────┐
                    │  Retrieval  │
                    └──────┬──────┘
                           │
┌──────────┐        ┌──────▼──────┐        ┌──────────┐
│  Memory  ├────────►     LLM     ◄────────┤  Tools   │
└──────────┘        └─────────────┘        └──────────┘
```

This augmented LLM is the atom from which all agentic systems are composed. Every pattern in this book — from prompt chaining to multi-agent orchestration — is a different way of arranging and connecting these atoms.

The practical implication: before building complex agent architectures, invest in making each augmentation excellent. A well-designed tool interface matters more than a clever orchestration strategy. A reliable retrieval pipeline matters more than a sophisticated planning loop. Anthropic's SWE-bench coding agent spent more engineering time optimizing tool definitions than overall prompts — and that investment paid off directly in performance.

## The Agent Loop

At its simplest, an agent is an LLM running in a loop. The loop follows a consistent pattern:

1. **Observe.** The agent receives input — a user request, a tool result, an error message, a piece of retrieved context.
2. **Think.** The LLM processes the observation and decides what to do next. This may involve planning, reasoning about the current state, or simply selecting the next action.
3. **Act.** The agent executes an action — calling a tool, generating output, requesting more information.
4. **Evaluate.** The result of the action becomes a new observation, and the loop continues.

```
    ┌──────────┐
    │ Observe  │◄──────────────────────┐
    └────┬─────┘                       │
         │                             │
    ┌────▼─────┐                       │
    │  Think   │                  ┌────┴─────┐
    └────┬─────┘                  │ Evaluate │
         │                        └────▲─────┘
    ┌────▼─────┐                       │
    │   Act    ├───────────────────────┘
    └──────────┘
```

The loop terminates when the agent determines the task is complete, when it encounters a stopping condition set by the developer (maximum iterations, time limit, cost budget), or when it decides to escalate to a human.

This looks simple because it is. The complexity lives not in the loop structure but in what happens at each step: how the agent decides what to do (planning patterns, Chapter 8), which tools it calls and how (tool use patterns, Chapter 6), how it evaluates whether it's making progress (reflection patterns, Chapter 7), and how errors are handled (Chapter 16).

Andrew Ng describes an "AI Agentic moment" — the first time you see an agent do something you didn't expect. During a live demo of a research agent, his web search API returned a rate-limiting error. The agent, rather than failing, pivoted to a Wikipedia search tool he'd forgotten he'd given it, and completed the task. The loop is simple. What emerges from it is not.

## When to Use Agents (and When Not To)

This might be the most important section in the chapter. The instinct, when you discover agent architectures, is to apply them everywhere. Resist it.

Anthropic's core recommendation: **find the simplest solution possible, and only increase complexity when needed.** Agentic systems trade latency and cost for better task performance. That tradeoff is worth it sometimes. Not always.

### Use an agent when

- **The task requires dynamic decision-making.** If the steps depend on intermediate results — if you can't write a flowchart in advance — an agent adds value.
- **The task benefits from iteration.** If output quality improves with self-critique and revision, agentic patterns like reflection and evaluator-optimizer loops are worth the cost.
- **The environment is unpredictable.** If tools may fail, data may be missing, or the problem space is poorly defined, an agent's ability to adapt and recover justifies its overhead.
- **The task is complex enough to decompose.** Multi-step problems with distinct subtasks (research, analysis, writing, verification) are natural fits for agent architectures.

### Don't use an agent when

- **A single LLM call with good prompting solves the problem.** Most text generation, classification, summarization, and extraction tasks don't need agents. Start here.
- **A deterministic workflow suffices.** If you can draw the flowchart, build the flowchart. It will be faster, cheaper, and more reliable.
- **Cost and latency matter more than quality.** Agents make many LLM calls. Each call costs tokens and time. For high-throughput, low-latency applications, agents are usually the wrong pattern.
- **You can't tolerate unpredictable behavior.** Agents, by definition, make decisions you haven't hardcoded. If you need strict determinism, you need a workflow, not an agent.

The decision framework is straightforward: **start with the simplest approach that works. Add agentic complexity only when you can demonstrate that it improves outcomes.** Measure, don't assume.

## A Brief History of Agents

The idea of software agents long predates LLMs. The term was used in the 1990s for autonomous programs that could act on behalf of users — booking flights, filtering emails, monitoring stock prices. Those early agents used rule-based logic and simple planning algorithms.

The modern era of AI agents begins with three developments:

**Chain-of-thought prompting (2022).** Wei et al. showed that asking a model to "think step by step" dramatically improved performance on reasoning tasks. This was the first crack in the single-pass paradigm — the recognition that giving a model room to reason, rather than demanding an immediate answer, changes the quality of output fundamentally.

**Tool use and function calling (2023).** OpenAI's function calling API and similar capabilities from other providers gave LLMs the ability to generate structured calls to external tools. This transformed models from text generators into actors that could affect the world — search the web, execute code, query databases.

**Inference-time compute (2024).** OpenAI's o1 model demonstrated that allocating more computation at inference time — letting the model think longer, explore multiple paths, backtrack from dead ends — yields qualitatively different performance. On the AIME mathematics benchmark, o1 scored 83% compared to GPT-4o's 12%. This was not a marginal improvement. It was evidence that deliberation — not just training data — could drive reasoning.

These three capabilities — reasoning, tool use, and deliberation — are the technical foundation on which all modern agent patterns rest. The patterns in this book are ways of combining them.

## Framework Landscape

Building agents from scratch is entirely feasible — and this book will show you how to do it in plain Python before introducing any framework. But frameworks exist, and understanding the landscape helps you make informed choices.

**LangChain / LangGraph.** The most widely adopted ecosystem for building LLM applications. LangChain provides abstractions for chains, tools, and retrieval. LangGraph adds a graph-based orchestration layer for building stateful, multi-step agent workflows with cycles and branching.

**AutoGen (Microsoft).** A framework oriented around multi-agent conversation. Agents are defined as conversable entities that can exchange messages, use tools, and coordinate to solve problems. Particularly strong for scenarios involving multiple specialized agents.

**CrewAI.** Focused on multi-agent collaboration with role-based task assignment. Agents are defined with specific roles, goals, and backstories. Good for workflows that naturally decompose into specialized roles.

**Semantic Kernel (Microsoft).** An SDK for integrating LLMs into applications, with a focus on enterprise patterns. Supports planners, plugins (tools), and memory across multiple LLM providers.

**Claude Agent SDK (Anthropic).** A lightweight SDK for building agents using Claude models, with native support for tool use, guardrails, and the Model Context Protocol (MCP).

**Strands Agents SDK (AWS).** A recent entry focused on building production agents with AWS service integration.

Anthropic advises starting with direct LLM API calls — many patterns can be implemented in a few lines of code — and only adopting a framework when the complexity justifies it. The critical guideline: **if you use a framework, understand the underlying code.** Incorrect assumptions about what's happening under the hood are the most common source of bugs in agentic systems.

This book follows that philosophy. Every pattern is first explained and implemented from first principles, then shown in a framework context. You'll understand what the framework is doing for you before you start relying on it.

### A Note on Code Examples

The code throughout this book uses **OpenAI's Python SDK** (`openai`) for consistency and readability. This is a pragmatic choice, not an endorsement — the patterns themselves are provider-agnostic. Every pattern in this book works with Anthropic's Claude, Google's Gemini, Mistral, open-weight models via Ollama or vLLM, or any provider that supports chat completions and tool calling. Where a pattern depends on a provider-specific feature (such as OpenAI's structured output mode), the text notes this and describes portable alternatives. When adapting examples to another provider, the core architecture remains identical — only the client initialization and model name change.

## What's Ahead

The rest of this book is organized into three movements.

**Part I (this section)** establishes foundations. Chapter 2 covers the mindset shift required to think in terms of delegation and trust calibration. Chapter 3 examines how AI reasoning actually works — drawing on mechanistic interpretability, grokking, and the intelligence-consciousness distinction — because understanding your material makes you a better engineer.

**Part II** is the core pattern catalog. Chapters 4 through 10 cover the essential building blocks: prompt chaining, routing, tool use, reflection, planning, parallelization, and memory. Each pattern is presented with its intent, architecture, Python implementation, framework spotlight, tradeoffs, and real-world examples.

**Part III** covers compositional patterns: orchestrator-workers, multi-agent collaboration, and evaluator-optimizer loops — architectures that combine the core patterns into larger systems.

**Part IV** addresses production concerns: guardrails and safety, evaluation and observability, and the journey from prototype to production.

By the end, you'll have both a catalog of proven patterns and the judgment to know which ones to reach for — and which ones to leave on the shelf.

---

## Review Questions

1. Using the Agentic Spectrum framework, classify each of these systems and justify your answer: (A) A chatbot that selects from three predefined customer service templates based on the input, (B) An email client that learns user preferences and auto-files certain types of messages without user interaction, (C) A code completion tool that suggests the next line as you type. Where on the spectrum would each need to be to be called an "agent"?

2. The chapter contrasts "workflows" (predefined code paths) with "agents" (dynamic decision-making). You are tasked with building a system to process customer refund requests. The system must check eligibility, verify payment records, and either approve or reject. Does this problem call for a workflow or an agent? Defend your choice by explaining what information is and isn't predictable at design time.

3. The Augmented LLM consists of three capabilities: retrieval, tools, and memory. For each capability, describe a concrete failure mode that could occur if the capability is missing or broken. Then explain why each failure mode is specifically a problem for agents (rather than simple chatbots).

4. The chapter presents a history of the AI Effect — how capabilities once considered "intelligent" become dismissed as "mere statistics" once machines achieve them. Why does this matter for agentic engineering? How should this historical pattern influence your trust calibration when deploying an agent?

5. Describe the relationship between the Agent Loop and a traditional programming loop (like a `while` statement). What is conceptually similar? What is fundamentally different? Why does the agent loop require different testing and observability strategies?

---

## Sources

- Anthropic. "Building Effective Agents." *Anthropic Engineering*, December 2024. <https://www.anthropic.com/engineering/building-effective-agents>. Accessed April 2026.

- Chase, H. "What is an Agent?" *LangChain Blog*, June 2024. <https://blog.langchain.com/what-is-an-agent/>. Accessed April 2026.

- Ng, A. "Agentic Design Patterns Part 1: Four AI agent strategies that improve GPT-4 and GPT-3.5 performance." *The Batch, DeepLearning.AI*, March 2024. <https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/>. Accessed April 2026.

- Ng, A. "Agentic Design Patterns Part 4: Planning." *The Batch, DeepLearning.AI*, April 2024. <https://www.deeplearning.ai/the-batch/agentic-design-patterns-part-4-planning/>. Accessed April 2026.

- OpenAI. "Learning to Reason with LLMs." *OpenAI Blog*, September 2024. <https://openai.com/index/learning-to-reason-with-llms/>. Accessed April 2026.

- Wei, J., Wang, X., Schuurmans, D., Bosma, M., et al. "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models." *NeurIPS 2022*. <https://arxiv.org/abs/2201.11903>

- Wu, Q., Bansal, G., Zhang, J., et al. "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation." *arXiv:2308.08155*, 2023.
