# Chapter 3: How AI Reasoning Actually Works

Every engineer should understand their material. A structural engineer knows how steel behaves under load — its yield strength, its failure modes, the conditions that cause fatigue. A software engineer building agentic systems should know how LLMs actually reason — what they can do, what they can't, and where the failures are predictable.

This chapter draws on mechanistic interpretability research, philosophy of mind, and recent empirical results to give you a grounded, honest picture of the reasoning engine at the center of every agent you build.

## Moving the Goalposts

Every few years, we draw a line in the sand. "Machines can't play chess." Then Deep Blue crushed Kasparov. "Well, chess is just brute-force calculation — machines can't play Go." Then AlphaGo beat Lee Sedol. "Okay, but games are narrow. Machines can't *write*." And then GPT arrived, and people started reading AI-generated text without realizing it.

The pattern is called the AI Effect: every time a machine crosses a threshold we once called "intelligent," we redefine intelligence to exclude whatever the machine just did. The goalposts keep moving. Always backward. Always just out of reach.

This matters for agent engineering because the same instinct — "it's not *really* reasoning" — can lead you to either over-trust or under-trust your agent's capabilities. You need a clearer framework than vibes and metaphors.

## The Parrot Hypothesis and Its Limits

The skeptical position has a catchy name. Bender, Gebru, and colleagues called large language models "stochastic parrots" — systems that stitch together probable word sequences without understanding what any of it means (Bender et al., 2021). Under this view, when an LLM explains quantum mechanics, it's doing something closer to autocomplete on steroids. No comprehension. No meaning. Just statistics.

There's force in that critique. When you change the numbers in a math problem, some models fall apart. They memorized the pattern, not the principle. Studies have shown that model performance on standard benchmarks drops by 50% or more when question formats are altered — numbers changed, phrasing restructured (Sánchez Salido et al., 2026). That's not reasoning. That's a lookup table with good lighting.

But the metaphor has started to crack. Humans also learn language through statistical exposure. A child learns the word "dog" by encountering it in contexts involving dogs — a process that developmental psychologists describe in explicitly statistical terms (Saffran, Aslin, & Newport, 1996). If learning from statistical exposure precludes "true understanding," the exclusion applies uncomfortably to human cognition as well.

For the agent engineer, the practical takeaway is this: your agents are neither pure parrots nor pure reasoners. They are somewhere in between, and the position varies by task. Understanding *where* your specific use case falls on that spectrum is critical to designing appropriate trust levels, guardrails, and verification strategies.

## What's Happening Inside the Black Box

The debate between "sophisticated mimic" and "genuine reasoner" cannot be settled by examining outputs alone. Outputs can deceive. The field of mechanistic interpretability offers a way forward: rather than asking what models *say*, it asks what they *represent*.

### Internal World Models

In 2023, researchers at Harvard trained a small transformer model on nothing but Othello move sequences — raw text, no board images, no rules. Just strings like "C4, E3, F5" (Li et al., 2023). The model was never shown what an Othello board looks like.

When they probed the model's internals, they found something remarkable: it had constructed a complete, accurate representation of the 8×8 board. Not because anyone told it to. It deduced the geometry from patterns alone.

They went further. They surgically altered the model's internal state — flipped a single tile from Black to White inside the network — and the model's predictions changed to reflect the new, artificial board state. It predicted moves legal on the doctored board, not the real one.

That's not autocomplete. That's a system building a model of its world and reasoning from it. The finding was *causal*, not merely correlational — the model's predictions were *caused by* its internal representation, not just associated with it.

This result has been replicated across domains. Research on larger language models has found that abstract concepts — sentiment, truthfulness, geographical location, historical chronology — are encoded as linear directions in activation space (Li et al., 2024; Marks & Tegmark, 2023). When models are queried about cities, their internal activations reflect actual geographical distances, recreating spatial maps from text alone.

### Why This Matters for Agent Engineering

These findings change how you should think about your agents' capabilities:

1. **The model has a model.** When your agent reasons about a domain, it's not just doing string matching. It has internal representations that, at least partially, capture the structure of the domain. This is why well-prompted agents can generalize to novel situations within familiar domains.

2. **The model's model has limits.** The internal representations are learned from statistical regularities in text, not from direct interaction with the world. They capture what *has been written about* a domain, which is not the same as the domain itself. This is why your agent can reason about physics questions it's seen phrased in familiar ways but struggle with genuinely novel physical scenarios.

3. **You can probe the representations.** Techniques from mechanistic interpretability — linear probes, activation patching, causal intervention — can help you understand what your agent has actually learned about your domain, rather than what it appears to know from its outputs.

## From Memorization to Generalization: Grokking

If models can reason, how do they acquire the capability? The phenomenon of "grokking" offers a window into the transition from memorization to genuine generalization (Power et al., 2022).

In typical training, a model first memorizes its training data — training accuracy reaches 100% while test accuracy remains near zero. Grokking occurs when, long after memorization is complete, the model undergoes a sudden phase transition: test accuracy spikes from near-zero to near-perfect. The model has discovered a generalizable algorithm.

The most striking example involves modular arithmetic. When trained to compute (a + b) mod 97, models initially memorize the addition table. During the grokking phase, mechanistic analysis reveals that the model's internal weights reorganize to implement a discrete Fourier transform: mapping numbers onto a circle, performing rotation, and mapping back (Nanda et al., 2023). Nobody taught the model Fourier analysis. It appears to have learned an algorithm that resembles a discrete Fourier transform, likely because it represents a more compressible solution than brute memorization. (An important caveat: these grokking experiments use small, purpose-built transformer models on synthetic tasks. Whether identical representational reorganization occurs in production-scale LLMs trained on natural language remains an active area of research.)

A system that induces generalizable mathematical algorithms from training data is doing something qualitatively different from lookup. The underlying process — learning and applying abstract rules to novel instances — satisfies most functional definitions of reasoning, though researchers continue to debate how closely these learned algorithms mirror true mathematical understanding.

For agent engineers, grokking reveals something important about your agents' behavior: **the boundary between "memorized response" and "genuine reasoning" is not fixed.** It depends on the task, the model's training, and whether the model has undergone the kind of representational reorganization that grokking represents. You cannot assume either extreme for any given task. You must test.

## System 2: Deliberate Reasoning in Machines

Daniel Kahneman's distinction between System 1 (fast, intuitive) and System 2 (slow, deliberate) thinking has become a standard framework in cognitive science. Until recently, LLMs were purely System 1 — producing tokens in a single forward pass with no capacity for reflection, backtracking, or self-correction.

### Chain-of-Thought as Working Memory

Chain-of-thought prompting introduced a simple but transformative idea: ask the model to show its work (Wei et al., 2022). When models verbalize intermediate steps, they effectively use their own output as a working memory buffer, attending to prior reasoning when generating the next step. This produces dramatic performance gains on multi-step mathematical, logical, and planning tasks.

The functional parallel to human deliberation is hard to ignore. Decomposing a problem, holding intermediate results, and building toward a conclusion through sequential steps is precisely what we mean by deliberate reasoning.

This is directly relevant to agent design. Every agentic pattern that involves multi-step reasoning — planning (Chapter 8), reflection (Chapter 7), evaluator-optimizer loops (Chapter 13) — relies on the model's ability to engage in this kind of extended deliberation. When you design a reflection loop, you are giving the model multiple opportunities to engage System 2 reasoning.

### Inference-Time Compute: Thinking Harder

The paradigm shift from training-time scaling to inference-time scaling represents a breakthrough for agent capabilities. OpenAI's o1 model (2024) demonstrated that allocating more computation at inference time — letting the model think longer, explore multiple paths, backtrack from dead ends — yields qualitatively different performance.

On the AIME (American Invitational Mathematics Examination) benchmark, GPT-4o scores approximately 12%. The o1 model, using extended internal chains of thought, exceeds 83% — matching top-percentile human students (OpenAI, 2024).

This is not a marginal improvement. It is evidence that *deliberation itself* — not just training data — drives reasoning capability. The model is not recalling a memorized answer. It is exploring a solution space, evaluating candidates, and recovering from errors.

For agent engineers, inference-time compute has a direct implication: **the reasoning quality available to your agent is not a fixed constant.** By allocating more compute — using longer chains of thought, multiple attempts, or tree-search strategies — you can systematically improve your agent's reasoning on hard problems. This is the technical foundation of parallelization patterns (Chapter 9) and reflection patterns (Chapter 7).

### Neurosymbolic Integration

A parallel development combines neural networks with symbolic engines. DeepMind's AlphaGeometry exemplifies this: a neural model generates geometric constructions ("try adding a perpendicular line here"), and a symbolic prover rigorously validates the resulting theorem (Trinh et al., 2024). The neural system provides the creative leap; the symbolic system provides the logical guarantee.

This mirrors how human mathematicians actually work — intuition first, proof second. More importantly for agent design, it demonstrates the pattern of combining an LLM's generative flexibility with structured verification. Many of the patterns in this book — reflection with test execution (Chapter 7), tool use for validation (Chapter 6), evaluator-optimizer loops (Chapter 13) — implement the same principle: let the LLM generate, then verify with something more reliable.

## Intelligence vs. Consciousness: Why It Matters for Engineering

Here is where we must be precise about what our agents can and cannot do.

Anil Seth, Director of the Centre for Consciousness Science at the University of Sussex, published an essay in *Noema* that crystallizes a distinction routinely blurred in AI discourse. His core argument: intelligence and consciousness are different things (Seth, 2026).

"Intelligence is mainly about *doing*: solving a crossword puzzle, assembling some furniture, navigating a tricky family situation. ... Consciousness, in contrast to intelligence, is mostly about *being*."

AI systems can claim intelligence — they do things with increasing sophistication. Whether there is *anything it is like* to be an LLM is a separate question, and the evidence suggests not. There is no inner experience. No felt sense of solving a problem. When we say these models "hallucinate," we're projecting biological consciousness onto a statistical process. "Confabulate" would be more accurate — making things up without experiencing the making.

Why does this distinction matter for agent engineering? Three reasons:

**1. It explains confabulation.** Your agent doesn't "know" when it's making things up because there is no knower. The confident wrong answer and the confident right answer are produced by the same process. This is not a bug that will be fixed with better training. It's a structural feature of systems that generate text without experiential grounding. Your guardrail strategy (Chapter 14) must account for it.

**2. It bounds trust.** A conscious agent that understood the consequences of its actions would self-correct in ways that LLMs do not. An LLM that executes a destructive operation doesn't feel concern or hesitation. Your trust calibration (Chapter 2) must never assume that the agent "cares" about outcomes. You must build the caring into the architecture — through verification steps, human checkpoints, and explicit constraints.

**3. It reframes the design challenge.** You are not building a colleague who understands your intent. You are building a system that processes tokens in ways that frequently align with useful behavior. The alignment is real and valuable, but it is statistical, not semantic. Every pattern in this book is, at bottom, a technique for increasing the reliability of that statistical alignment.

## The Known Limits

Understanding your agent's limits is as important as understanding its capabilities. Three categories of limitation directly affect agent design:

### Abstraction and Out-of-Distribution Reasoning

François Chollet's Abstraction and Reasoning Corpus (ARC) was designed to test fluid intelligence through novel visual puzzles that cannot be solved by pattern-matching against training data (Chollet, 2019). Each task presents a few input-output examples illustrating an underlying rule, and the solver must infer and apply that rule to a new input. Humans solve most ARC tasks easily. Until recently, even the most capable LLMs performed poorly.

The landscape is shifting. OpenAI's o3 model (2024) achieved a significant improvement on ARC-AGI, reaching approximately 76% on the semi-private evaluation set — a dramatic jump from prior models that scored in the low single digits. However, this came at substantial computational cost (thousands of dollars per task at the high-compute setting), and performance on the held-out private test set remained lower. The result demonstrates that inference-time compute scaling can partially close the gap on abstract reasoning, but does not yet match the efficiency or generality of human cognition on these tasks.

The failure mode remains revealing: where humans struggle with perceptual complexity, models struggle with *rule induction itself*. The kind of reasoning LLMs excel at — interpolation within learned patterns — still differs from the extrapolative, out-of-distribution reasoning that characterizes flexible intelligence, though the boundary is narrowing with each generation of reasoning models.

**Engineering implication:** If your agent encounters problems that require reasoning beyond the distribution of its training data, it will likely fail. Design your agent's scope to stay within its zone of reliability, and build escalation paths for novel situations.

### Counterfactual Reasoning

When asked to reason about scenarios that contradict established facts — "If gravity were repulsive, what would happen to ocean tides?" — LLMs frequently default to descriptions consistent with reality rather than following the counterfactual premise to its logical consequences. They describe tides as they are, not as they would be under altered physics.

This brittleness reveals that what these systems have learned is less a flexible causal model of the world than a high-fidelity map of statistical regularities in how humans describe the world.

**Engineering implication:** Be cautious with agents that need to reason about hypotheticals, edge cases, or scenarios that deviate significantly from common patterns in training data. Use structured prompting and chain-of-thought to enforce counterfactual premises explicitly.

### Embodiment and Grounding

Purely text-trained models lack sensorimotor grounding. They have never touched an apple or heard a thunderstorm. Their understanding of the physical world comes from descriptions of it, not experience of it. Multimodal models partially address this, with probing studies showing progressive integration of visual and lexical representations (Yu & Lee, 2025). But the extent to which any current AI system is genuinely grounded in the world — rather than grounded in a statistical model of human descriptions of the world — remains an open question.

**Engineering implication:** Agents tasked with physical-world reasoning (robotics, spatial planning, material properties) operate at the edges of current capability. Supplement LLM reasoning with structured data, simulation tools, and domain-specific models.

## Practical Synthesis: What This Means for Your Agents

Here is the condensed picture, translated into engineering terms:

| What LLMs Do Well | What They Don't Do Well |
|---|---|
| Pattern recognition within training distribution | Novel reasoning outside training distribution |
| Multi-step reasoning with chain-of-thought | Consistent reliability across attempts |
| Tool selection and structured output | Knowing when they're wrong |
| Summarization, analysis, and synthesis | Counterfactual and hypothetical reasoning |
| Code generation for familiar patterns | Genuine abstraction and rule induction |
| Following complex instructions | Maintaining coherence over very long tasks |

The patterns in this book are, fundamentally, engineering strategies for amplifying the left column and mitigating the right column:

- **Reflection** (Chapter 7) gives the agent multiple passes to catch its own errors.
- **Tool use** (Chapter 6) grounds the agent's reasoning in external reality — databases, APIs, code execution.
- **Planning** (Chapter 8) structures the agent's reasoning into manageable steps.
- **Guardrails** (Chapter 14) catch the failures that the agent cannot catch itself.
- **Evaluation** (Chapter 15) measures whether the agent's reasoning is actually working.

Understanding the reasoning engine doesn't make you a philosopher. It makes you a better engineer. When you know *why* your agent produces confident wrong answers, you design verification differently. When you know *why* chain-of-thought works, you structure your prompts differently. When you know *where* the boundaries of reliable reasoning lie, you scope your agent's autonomy appropriately.

The goalposts have moved far enough. What matters now is building well.

---

## Sources

- Bender, E. M., Gebru, T., McMillan-Major, A., & Shmitchell, S. "On the Dangers of Stochastic Parrots: Can Language Models Be Too Big?" *FAccT '21*, March 2021. <https://dl.acm.org/doi/10.1145/3442188.3445922>

- Chollet, F. "On the Measure of Intelligence." *arXiv*, 2019. <https://arxiv.org/abs/1911.01547>

- Li, K., Hopkins, A. K., Bau, D., Viégas, F., Pfister, H., & Wattenberg, M. "Emergent World Representations: Exploring a Sequence Model Trained on a Synthetic Task." *ICLR 2023*. <https://arxiv.org/abs/2210.13382>

- Li, K., et al. "Language Models Linearly Represent Sentiment." *BlackBoxNLP, ACL Anthology*, 2024. <https://aclanthology.org/2024.blackboxnlp-1.5/>

- Marks, S., & Tegmark, M. "The Geometry of Truth: Emergent Linear Structure in Large Language Model Representations of True/False Datasets." *arXiv*, 2023. <https://arxiv.org/abs/2310.06824>

- Nanda, N., Chan, L., Lieberum, T., Smith, J., & Steinhardt, J. "Progress Measures for Grokking via Mechanistic Interpretability." *ICLR 2023*. <https://arxiv.org/abs/2301.05217>

- OpenAI. "Learning to Reason with LLMs." *OpenAI Blog*, September 2024. <https://openai.com/index/learning-to-reason-with-llms/>

- Power, A., Burda, Y., Edwards, H., Babuschkin, I., & Misra, V. "Grokking: Generalization Beyond Overfitting on Small Algorithmic Datasets." *ICLR 2022*. <https://arxiv.org/abs/2201.02177>

- Saffran, J. R., Aslin, R. N., & Newport, E. L. "Statistical Learning by 8-Month-Old Infants." *Science*, 274(5294), 1926–1928, 1996.

- Sánchez Salido, E., Gonzalo, J., & Marco, G. "On the Limits of LLM Reasoning." *IEEE Access*, 14, 9384–9393, 2026.

- Seth, A. "The Mythology of Conscious AI." *Noema Magazine*, January 14, 2026. <https://www.noemamag.com/the-mythology-of-conscious-ai/>

- Trinh, T. H., Wu, Y., Le, Q. V., He, H., & Luong, T. "Solving Olympiad Geometry without Human Demonstrations." *Nature*, 625, 476–482, 2024.

- Wei, J., Wang, X., Schuurmans, D., Bosma, M., et al. "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models." *NeurIPS 2022*. <https://arxiv.org/abs/2201.11903>

- Yu, Z., & Lee, Y. J. "How Multimodal LLMs Solve Image Tasks." *COLM 2025*. <https://arxiv.org/abs/2508.20279>
