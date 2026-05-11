# Appendix A: Pattern Quick Reference

A condensed reference for all patterns covered in the book. Tear this out (or bookmark it) for quick lookup during development.

## Pattern Summary Table

| Pattern | Chapter | When to Use | Key Tradeoff |
|---|---|---|---|
| **Prompt Chaining** | 4 | Multi-step tasks with clear sequential stages | Latency (N sequential calls) |
| **Routing** | 5 | Diverse inputs needing specialized handlers | Misclassification risk |
| **Tool Use** | 6 | Tasks requiring external data or actions | Security + cost per tool call |
| **Reflection** | 7 | Output quality improves with self-critique | Cost multiplication per iteration |
| **Planning (ReAct)** | 8 | Complex goals requiring decomposition | Plan quality limits everything |
| **Parallelization** | 9 | Independent subtasks or consensus needed | Cost multiplication × parallelism |
| **Memory** | 10 | Multi-turn or cross-session knowledge needed | Context pollution + staleness |
| **Orchestrator-Workers** | 11 | Dynamic task decomposition required | Orchestrator is single point of failure |
| **Multi-Agent** | 12 | Tasks benefiting from role-based expertise | Communication overhead + cost |
| **Evaluator-Optimizer** | 13 | Iterative refinement with clear criteria | Evaluation quality is the ceiling |

## Decision Flowchart

Use this to choose the right pattern for your task:

```
START: Can a single LLM call solve this?
  ├─ YES → Use a single call. Done.
  └─ NO → Are the steps known in advance?
       ├─ YES → Are they independent?
       │    ├─ YES → Parallelization (Ch 9)
       │    └─ NO → Prompt Chaining (Ch 4)
       └─ NO → Does the task need external data or actions?
            ├─ YES → Tool Use (Ch 6)
            │    └─ Are there many tools to choose from?
            │         ├─ YES → Routing (Ch 5) + Tool Use (Ch 6)
            │         └─ NO → Tool Use (Ch 6) alone
            └─ NO → Does the task need dynamic decomposition?
                 ├─ YES → Do subtasks need different expertise?
                 │    ├─ YES → Is the task structure known upfront?
                 │    │    ├─ YES → Multi-Agent (Ch 12)
                 │    │    └─ NO → Orchestrator-Workers (Ch 11)
                 │    └─ NO → Planning/ReAct (Ch 8)
                 └─ NO → Does output quality improve with iteration?
                      ├─ YES → Do you have clear evaluation criteria?
                      │    ├─ YES → Evaluator-Optimizer (Ch 13)
                      │    └─ NO → Reflection (Ch 7)
                      └─ NO → Does the task need conversation history?
                           ├─ YES → Memory (Ch 10)
                           └─ NO → Re-examine. A single call
                                   might work after all.
```

## Implementation Checklists

### Prompt Chaining (Chapter 4)
- [ ] Define each stage's input/output contract
- [ ] Add validation gates between stages
- [ ] Decide: fail-fast or skip on stage failure?
- [ ] Set max_tokens per stage to control cost
- [ ] Log intermediate outputs for debugging

### Routing (Chapter 5)
- [ ] Define categories with clear boundaries
- [ ] Use structured output for classification
- [ ] Add a fallback/catch-all category
- [ ] Test with ambiguous inputs near category boundaries
- [ ] Monitor misclassification rates in production

### Tool Use (Chapter 6)
- [ ] Write clear tool descriptions (name, purpose, parameters)
- [ ] Implement error handling in every tool
- [ ] Set a maximum iteration count for the agent loop
- [ ] Sandbox any code execution tools
- [ ] Log all tool calls for audit

### Reflection (Chapter 7)
- [ ] Define what "good enough" means (stopping criteria)
- [ ] Set a maximum iteration count (3-5 typical)
- [ ] Detect stagnation (no improvement between iterations)
- [ ] Use a different model or prompt for the critic vs. generator
- [ ] Track quality scores across iterations

### Planning / ReAct (Chapter 8)
- [ ] Define available actions clearly
- [ ] Set maximum steps to prevent infinite loops
- [ ] Implement replanning on failure
- [ ] Validate action parameters before execution
- [ ] Log the full trajectory for debugging

### Parallelization (Chapter 9)
- [ ] Verify subtasks are truly independent
- [ ] Choose aggregation strategy (majority vote, merge, select best)
- [ ] Handle partial failures (some branches succeed, others fail)
- [ ] Set per-branch timeouts
- [ ] Monitor total token usage (scales with parallelism)

### Memory (Chapter 10)
- [ ] Choose memory type (sliding window, summary, vector store, key-value)
- [ ] Set context budget for memory retrieval
- [ ] Implement memory cleanup / expiration
- [ ] Test behavior when memory is empty vs. full
- [ ] Handle stale or contradictory memories

### Orchestrator-Workers (Chapter 11)
- [ ] Design the plan schema (Pydantic model)
- [ ] Define worker specializations and their system prompts
- [ ] Implement dependency resolution between subtasks
- [ ] Add replanning on worker failure
- [ ] Set overall task timeout and token budget

### Multi-Agent (Chapter 12)
- [ ] Define roles with clear, non-overlapping responsibilities
- [ ] Choose communication pattern (sequential, debate, hierarchical)
- [ ] Set maximum conversation rounds
- [ ] Monitor for echo chambers and role confusion
- [ ] Test with fewer agents first (2 before 5)

### Evaluator-Optimizer (Chapter 13)
- [ ] Design evaluation rubric with specific, measurable criteria
- [ ] Set score threshold for "good enough"
- [ ] Detect oscillation (score bouncing between iterations)
- [ ] Consider hybrid evaluation (LLM + programmatic checks)
- [ ] Budget for 2-4x cost of single generation

## Pattern Combinations

Common combinations that work well together:

| Combination | Use Case |
|---|---|
| Routing → Prompt Chaining | Classify input, then run specialized pipeline |
| Tool Use + Reflection | Execute tools, then verify results |
| Planning + Tool Use | Decompose goal, execute steps with tools |
| Parallelization + Evaluator-Optimizer | Generate N candidates, evaluate and select best |
| Orchestrator-Workers + Memory | Complex workflow with persistent state |
| Routing + Guardrails (Ch 14) | Classify, filter unsafe, route to handler |

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Agent for everything | Simple tasks get slow and expensive | Start with single LLM call |
| Infinite loops | No stopping criteria | Always set max iterations |
| God orchestrator | One agent does everything | Decompose into specialized roles |
| Blind trust | No output validation | Add guardrails (Ch 14) |
| Kitchen-sink memory | Store everything forever | Curate and expire memories |
| Premature multi-agent | 3+ agents when 1 would suffice | Benchmark simpler approaches first |
