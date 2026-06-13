# CCAT Question Generator Harness

## Purpose

This harness governs a CCAT-style question generation agent. The worker agent generates one practice question at a time, including answer choices, the correct answer, and an explanation. The harness controls the loop around the agent: tool access, validation, revision, persistence, guardrails, and observability.

The goal is to produce questions that are answerable, correctly solved, properly categorized, and traceable from draft to final acceptance.

## Main Loop

The harness runs until the requested number of accepted questions has been generated.

For each question, the harness:

1. Selects a target category, subcategory, and difficulty.
2. Sends a generation request to the worker agent.
3. Receives a candidate question.
4. Runs guardrails and checkpoints.
5. Returns structured feedback if the candidate fails.
6. Allows the worker to revise or regenerate.
7. Saves each candidate, revision, checkpoint result, and accepted question.

The worker generates questions. The harness decides whether they are acceptable.

## Tools and Material Handling

The harness provides approved tools and manages all inputs and outputs.

Inputs may include question count, CCAT taxonomy, example questions, category distribution, difficulty targets, and previously accepted questions.

Available tools may include:

* arithmetic calculator
* deterministic math checker
* table or graph generator
* JSON schema validator
* duplicate / similarity checker

Tool calls are routed through the harness so inputs, outputs, and effects are observable.

## Guardrails and Checkpoints

Guardrails are declared rules that every accepted question must satisfy:

* The question is answerable from the provided information.
* Exactly one answer choice is correct.
* The explanation supports the correct answer.
* Math matches deterministic tool output.
* The question fits the requested category and subcategory.
* The question does not copy or closely paraphrase seed examples.
* The question is formatted as a valid structured record.
* The content is appropriate for a general CCAT-style study tool.

Core checkpoints:

| Checkpoint    | Pass Criteria                            | Failure Behavior          |
| ------------- | ---------------------------------------- | ------------------------- |
| Schema        | Required fields are present and valid    | Revise or regenerate      |
| Answerability | Question has enough information to solve | Revise prompt or stimulus |
| Single Answer | Exactly one choice is correct            | Revise choices or wording |
| Explanation   | Reasoning supports the answer            | Revise explanation        |
| Math          | Calculations match tool output           | Correct or regenerate     |
| Similarity    | Not too close to existing examples       | Reject and regenerate     |
| Category      | Matches requested taxonomy               | Revise or relabel         |

Checkpoint feedback is returned to the worker in structured form so the next attempt addresses the specific failure.

## Observability and Alarms

The harness records every candidate, revision, checkpoint result, guardrail failure, tool call, accepted question, and rejection reason.

It also tracks operational metrics such as latency, token usage, estimated cost, revision count, acceptance rate, failure rate by checkpoint, and tool usage frequency.

Alarms are structured events with a type, severity, context, and recommended action. Example alarm types include:

* `MAX_REVISIONS_EXCEEDED`
* `LOW_ACCEPTANCE_RATE`
* `COST_THRESHOLD_APPROACHING`
* `TOOL_OUTPUT_CONFLICT`
* `DUPLICATE_QUESTION_RISK`
* `HUMAN_REVIEW_REQUIRED`

## Swappable Worker Interface

The harness treats the worker agent as replaceable. Any worker only needs to support:

```ts
generateQuestion(input: GenerationRequest): CandidateQuestion
reviseQuestion(candidate: CandidateQuestion, feedback: CheckpointFeedback[]): CandidateQuestion
```

This keeps the agent focused on generation while the harness governs constraints, validation, iteration, and visibility.
