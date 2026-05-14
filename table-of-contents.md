# Agentic Engineering Patterns and Mindset

## Table of Contents

---

### Preface

---

## Part I: Foundations

**Chapter 1 — What Is an Agent? (And What Isn't)**

- The Agentic Spectrum
- Workflows vs. Agents: The Anthropic Distinction
- The Augmented LLM: The Fundamental Building Block
- The Agent Loop
- When to Use Agents (and When Not To)
- A Brief History of Agents
- Framework Landscape
- What's Ahead
- Review Questions
- Sources

**Chapter 2 — The Agentic Engineering Mindset**

- Delegation, Not Automation
- Trust Calibration
- The Agent-Computer Interface (ACI)
- Start Simple, Add Complexity Only When It Helps
- Design for Observability from Day One
- Graceful Failure as a Feature
- Principles in Practice
- Review Questions
- Sources

**Chapter 3 — How AI Reasoning Actually Works**

- Moving the Goalposts
- The Parrot Hypothesis and Its Limits
- What's Happening Inside the Black Box
- From Memorization to Generalization: Grokking
- System 2: Deliberate Reasoning in Machines
- Intelligence vs. Consciousness: Why It Matters for Engineering
- The Known Limits
- Practical Synthesis: What This Means for Your Agents
- Review Questions
- Sources

---

## Part II: Core Patterns

**Chapter 4 — Prompt Chaining**

- How It Works
- Implementation in Python
- Designing Effective Gates
- Handling Failures
- Case Study: Content Generation Pipeline
- Framework Spotlight: LangChain LCEL
- Tradeoffs and Failure Modes
- When NOT to Use Prompt Chaining
- Review Questions
- Sources

**Chapter 5 — Routing**

- How It Works
- Implementation in Python
- Structured Output for Reliable Routing
- Model Routing for Cost Optimization
- Case Study: Customer Service Triage
- Framework Spotlight: LangGraph Conditional Edges
- Tradeoffs and Failure Modes
- When NOT to Use Routing
- Review Questions
- Sources

**Chapter 6 — Tool Use and the Agent-Computer Interface**

- The Tool-Use Loop
- Implementation in Python
- The Agent-Computer Interface
- Tool Selection at Scale
- Case Study: Research Agent
- Security Considerations
- Tradeoffs and Failure Modes
- When NOT to Use Tool Use
- Review Questions
- Sources

**Chapter 7 — Reflection and Self-Critique**

- How It Works
- The Self-Refine Pattern
- The Reflexion Pattern
- Tool-Interactive Critiquing (CRITIC)
- Two-Agent Reflection
- Case Study: Code Generation with Test Feedback
- Framework Spotlight: LangGraph Cycles
- Tradeoffs and Failure Modes
- When NOT to Use
- Review Questions
- Sources

**Chapter 8 — Planning and Reasoning**

- Chain-of-Thought as Foundation
- The ReAct Pattern
- Task Decomposition
- Dynamic Replanning
- Tree-of-Thought
- Case Study: Research and Analysis Agent
- Framework Spotlight: LangChain ReAct Agent
- Tradeoffs and Failure Modes
- When NOT to Use
- Review Questions
- Sources

**Chapter 9 — Parallelization**

- Sectioning: Independent Subtasks in Parallel
- Voting: Multiple Perspectives on the Same Task
- Map-Reduce
- Case Study: Parallel Evaluation Pipeline
- Framework Spotlight: LangGraph Fan-Out/Fan-In
- Tradeoffs and Failure Modes
- When NOT to Use
- Review Questions
- Sources

**Chapter 10 — Memory and State**

- Memory Taxonomy
- Short-Term Memory: Context Management
- Long-Term Memory: Persistent Knowledge
- RAG as a Memory Pattern
- Case Study: Customer Support Agent
- Framework Spotlight: LangGraph Checkpointing and Mem0
- Tradeoffs and Failure Modes
- When NOT to Use
- Review Questions
- Sources

---

## Part III: Compositional Patterns

**Chapter 11 — Orchestrator-Workers**

- How It Works
- Orchestrator Design
- Worker Specialization
- The Orchestration Loop
- Replanning: When Workers Fail
- Case Study: Multi-File Feature Implementation
- Framework Spotlight: OpenAI Agents SDK
- Tradeoffs and Failure Modes
- When NOT to Use
- Review Questions
- Sources

**Chapter 12 — Multi-Agent Collaboration**

- Communication Patterns
- Role-Based Decomposition
- Shared State vs. Message Passing
- The Discussion Pattern
- Case Study: Collaborative Code Review
- Framework Spotlight: CrewAI and OpenAI Agents SDK
- Tradeoffs and Failure Modes
- When NOT to Use
- Review Questions
- Sources

**Chapter 13 — Evaluator-Optimizer**

- How It Works
- Evaluation Design
- The Refinement Loop
- LLM Evaluation vs. Programmatic Evaluation
- Combining with Other Patterns
- Case Study: Marketing Copy Generator
- Framework Spotlight: DSPy
- Tradeoffs and Failure Modes
- When NOT to Use
- Review Questions
- Sources

---

## Part IV: Production

**Chapter 14 — Guardrails, Safety, and Human-in-the-Loop**

- Input Guardrails
- Output Guardrails
- The Parallel Guardrails Pattern
- Human-in-the-Loop
- Sandboxed Execution
- Audit Logging
- Case Study: Financial Operations Agent
- Minimum Viable Guardrails
- Review Questions
- Sources

**Chapter 15 — Evaluation and Observability**

- Why Agent Eval Is Different
- Evaluation Strategies
- Building Eval Datasets
- Tracing and Observability
- Production Monitoring
- Framework Spotlight: OpenTelemetry and LangSmith
- Tradeoffs and Failure Modes
- When NOT to Over-Invest
- Review Questions
- Sources

**Chapter 16 — From Prototype to Production**

- The Simplicity Principle, Revisited
- Cost Management
- Error Handling and Recovery
- Latency Optimization
- Testing for Production
- Deployment Strategies
- Case Study: Customer Support Agent — Notebook to Production
- Review Questions
- Sources

---

## Appendices

**Appendix A — Pattern Quick Reference**

- Pattern Summary Table
- Decision Flowchart
- Implementation Checklists
- Pattern Combinations
- Anti-Patterns

**Appendix B — Python Environment Setup**

- Prerequisites
- Environment Setup
- API Key Configuration
- Project Structure
- The Shared LLM Helper
- Model Availability
- Troubleshooting

**Appendix C — Further Reading and Resources**

- Foundational Papers
- Industry References
- Frameworks and Tools
- Recommended Books
- Online Courses
