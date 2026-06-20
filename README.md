# QuizCat Terminal User Interface

QuizCat is a [Textual](https://textual.textualize.io/) terminal UI for timed,
CCAT-style multiple-choice practice tests. Pick an exam from the dashboard, work
through it against a 15-minute clock, and get scored on submission. It ships with
a 400-question bank (see below) and can also **generate fresh exams on demand**
using an agentic LLM harness.

## Running it

Dependencies are managed by [uv](https://docs.astral.sh/uv/) and the project
targets Python 3.14+.

```bash
uv sync
uv run python main.py          # run the TUI in your terminal
uv run python serve.py         # serve it in a browser at http://localhost:8000
```

The browser build (`serve.py`) uses
[`textual-serve`](https://github.com/Textualize/textual-serve) to stream the
real terminal app to a web page, which is how it's deployed. See
[`DEPLOY.md`](DEPLOY.md) for the Docker + render.com walkthrough.

## Test generation harness

The "generate test" feature is powered by an agentic harness
(`harness.py`, exposed to the UI through `services.py`). A worker LLM drafts one
question at a time while the harness governs the loop around it — validation,
revision, persistence, and observability — so generated questions are
answerable, correctly solved, properly categorized, and traceable from draft to
acceptance. `HARNESS.md` is the design spec; the implemented harness demonstrates
four hackathon components directly in-product:

* **Main loop** — `run_generation()` walks a fixed question-type distribution
  (`GenerationRequest`, default 6 few-shot examples per type, up to 3 attempts
  each), generating and validating one question per slot until the requested set
  is accepted.
* **Tool calling** — math-like question types route through a
  calculator-enabled generation **and** verification path
  (`ChatClient.complete_with_tools`). The worker must check every non-trivial
  arithmetic step with a pure, no-network `calculate` tool before committing to
  an answer; non-math types use the standard path. Every tool invocation is
  captured as a `ToolCallRecord`.
* **Guardrails & checkpoints** — `validate_draft()` rejects structurally
  malformed questions (missing fields, no correct choice, off-taxonomy), and a
  strict math **verifier** re-solves each math question and retries on
  failed/warning verdicts (`VerificationResult`) up to `max_attempts`.
* **Observability** — every attempt yields a `HarnessQuestionTrace` (raw output,
  tool calls, verifier verdict, guardrail errors, repair attempts) and each run
  yields a `HarnessRunSummary`; both are persisted so generated exams can be
  inspected after the fact.

Few-shot examples are drawn from the seed question bank, so generated questions
match the style and taxonomy of the real CCAT items without copying them.

### Model boundary

Only the `ChatClient` boundary touches the network — the calculator, parsing,
and guardrail logic are pure and unit-testable without an API key (the tests
inject a scripted client to drive the loop deterministically). The default
client (`create_chat_client()`) is OpenAI-backed via LangChain's `ChatOpenAI`,
and the worker is **swappable** behind the `ChatClient` protocol. Configure it
with environment variables:

* `OPENAI_API_KEY` — **required** to generate tests (locally via `.env`, or as a
  service env var in deployment). The bundled question bank works without it.
* `OPENAI_MODEL` — model id, default `gpt-4o-mini`.
* `OPENAI_TEMPERATURE` — sampling temperature, default `0.2`.

## CCAT Question Bank Dataset Context

This project includes a seed dataset named `ccat_full_question_bank_prompt_stimulus.csv`. It contains 400 CCAT-style practice questions extracted from 8 BoostPrep Course Statistics reports, with 50 questions per source exam.

Each row represents one question. The dataset is intended to seed the application database, not to be treated as final production content. Preserve the data carefully during imports and migrations.

### Core structure

Questions are split into two conceptual fields:

* `prompt`: Reusable instructional text that explains how the question should be answered. This is often shared by many questions of the same type.
* `stimulus`: The unique content for the specific question. This is what the user must reason about to produce an answer.

Examples:

* Sentence completion:

  * `prompt`: “Choose the word or words that, when inserted in the sentence to replace the blank or blanks, best fits the meaning of the sentence.”
  * `stimulus`: The actual sentence with missing word(s).
* Antonym questions:

  * `prompt`: The instruction text asking for the opposite meaning.
  * `stimulus`: The all-caps target word.
* Attention to detail:

  * `prompt`: The shared instruction asking the user to compare entries.
  * `stimulus`: The five string pairs that would populate the comparison table.
* Image-based questions:

  * `prompt`: The text instruction for the question.
  * `stimulus`: The image filename needed to recover/render the image later.

### Stimulus types

The `stimulus_type` column indicates how the stimulus should be rendered:

* `text`: Plain text stimulus.
* `text_table`: Structured text that should eventually be rendered as a table, especially attention-to-detail questions.
* `image`: The stimulus is an image filename. The actual image asset may need to be resolved separately.

### Taxonomy

Each question has a broad `category` and a more specific `question_type`.

Primary categories:

* `Verbal`
* `Math & Logic`
* `Spatial Reasoning`

Primary question types include:

* Sentence Completion
* Analogies
* Attention to Detail
* Antonyms
* Applied Quantitative Word Problems
* Percent, Ratio & Proportion
* Syllogisms / Formal Logic
* Basic Numeric Calculation & Comparison
* Tables & Graphs
* Letter-Group Series
* Number Series
* Arrangement Logic
* Visual Next-in-Series
* Odd One Out
* Matrix Completion

Small one-off variants were intentionally rolled up into broader question types. For example, different numeric sequence patterns are all classified as `Number Series`, and different analogy relation types are all classified as `Analogies`.

### Answer fields

The dataset includes multiple-choice answer fields, a correct choice label, correct choice text, and an explanation. Import logic should preserve both the label and text because answer choice ordering matters for quiz rendering.

### Implementation notes for agents

When writing importers, seed scripts, migrations, or validation logic:

* Treat each CSV row as one question record.
* Do not recombine `prompt` and `stimulus`; they are intentionally separate.
* Preserve image filenames exactly as written in `stimulus`.
* Do not discard image-based questions.
* Do not assume every question has the same number of answer choices.
* Preserve explanations as plain text.
* Use `category`, `question_type`, and `stimulus_type` as controlled values where practical.
* Retain information about which exam the questions originated from
* Add validation that every imported question has a prompt or stimulus, at least one answer choice, a correct answer, a category, and a question type.
* Be careful with commas, quotes, and newlines when parsing the CSV; use a real CSV parser instead of string splitting.
