# `/docs/` — Documentation & Learning Artifacts

This folder contains project documentation, design artifacts, and structured learning materials. Each file serves a distinct purpose; together they form a self-contained learning + portfolio system.

---

## File Index

### Project Design

| File | Purpose | When to consult |
|---|---|---|
| [`design-doc.md`](design-doc.md) | Why the schema looks this way — modeling decisions, trade-offs, decision log | Reviewing why we chose star vs snowflake, why each dimension has its SCD type, what we considered and rejected |
| [`data-dictionary.md`](data-dictionary.md) | Per-table column reference (fct_trips + 5 dimensions) | Querying the warehouse, looking up column types/meanings, checking known values |

### Roadmap & Progress

| File | Purpose | When to consult |
|---|---|---|
| [`roadmap.md`](roadmap.md) | 10-pillar DE skill roadmap with checkbox state (☐/◐/☑/★) and Gaps Log | Tracking interview-readiness; identifying what to study next |

### Learning System (Per-Phase Drills)

| File | Purpose | When to consult |
|---|---|---|
| [`synthesis-questions.md`](synthesis-questions.md) | Interview-style synthesis drills, one set per phase | Preparing for interviews; running end-of-phase drills |
| [`synthesis-answers.md`](synthesis-answers.md) | Verbatim answers + grading + model answers + key lessons | Reviewing past performance; comparing your answer to a 9/10 model |
| [`synthesis-log.md`](synthesis-log.md) | Recurring weak patterns and strong patterns identified across drills | Identifying *meta-skills* needing attention; reinforcing positive habits |

### Reference Materials

| File | Purpose | When to consult |
|---|---|---|
| [`mental-models.md`](mental-models.md) | Reusable thinking tools (e.g., Configuration Cascade, Grain First, Defense in Depth) | Stuck on a problem; want to apply a known reasoning pattern |
| [`tooling-reference.md`](tooling-reference.md) | Terminal commands, SQL idioms, DuckDB↔Pandas mappings, dual-platform notes (🍎/🐧) | Looking up a command; switching between Pandas and SQL idioms |
| [`de_flashcards.csv`](de_flashcards.csv) | Spaced-repetition deck (Anki-importable) | Daily review; vocabulary reinforcement |

---

## How These Files Fit Together

Three layers of artifact serve three different needs:

**1. Vocabulary** — `de_flashcards.csv`. Atomic terms and short definitions. Use for spaced-repetition recall of facts.

**2. Patterns** — `mental-models.md`, `tooling-reference.md`. Reusable structures for thinking and doing. Use when you need a template you've seen before.

**3. Application** — `design-doc.md`, `data-dictionary.md`, `synthesis-*.md`, `roadmap.md`. The actual project work plus reflective study log. Use to demonstrate or audit your understanding.

The vocabulary feeds the patterns; the patterns scaffold the application; the application surfaces what's missing in the vocabulary. The flow is bidirectional and self-reinforcing.

---

## Conventions

- **Per-phase synthesis drills** — every phase ends with ~10 questions covering its key concepts. Score ≥8.0/10 average to advance.
- **Re-drill protocol** — phases below 8.0 trigger fresh-scenario re-drills targeting weakest questions.
- **Quarterly rerun** — every ~6 weeks, re-ask 1-2 prior questions to test retention, especially Gaps Log items.
- **Verbatim answer preservation** — `synthesis-answers.md` always preserves Bryan's actual answers without summarization, so future re-reads compare exact phrasing to the model answer.
- **Roadmap promotion rule** — items only promote to ☑ or ★ when every distinct concept in the item's name has been explicitly taught. For "X vs Y" items, both X and Y must be covered.

---

## How to Add a New File

When the project grows, new artifacts may be needed (e.g., a Phase 6 lessons-learned doc). Convention:

1. Create the file in `/docs/`
2. Add an entry to this README's File Index with purpose and when-to-consult
3. Cross-reference from any other artifact that benefits (e.g., link from root README)
4. Commit with a `docs:` prefix per Conventional Commits style

---

## Phase 1 Closeout Snapshot (current state)

Phase 0 and Phase 1 are complete. The artifacts most representative of current progress:

- **Architecture & decisions:** [`design-doc.md`](design-doc.md) (~280 lines)
- **Schema reference:** [`data-dictionary.md`](data-dictionary.md) (~280 lines)
- **Skill progress:** [`roadmap.md`](roadmap.md) — 6 ★ interview-ready, 6 ☑ theory learned
- **Drill performance:** Phase 0 re-drill avg 8.0/10 (cleared); Phase 1 drill pending after schema evolution investigation
- **Learning artifacts:** 10 mental models, ~58 flashcards, comprehensive tooling reference

Phase 2 (ingestion) is the next active workstream.
