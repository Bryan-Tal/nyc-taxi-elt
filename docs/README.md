# Documentation Index

This folder contains structured documentation, learning artifacts, and study notes for the `nyc-taxi-elt` project. Most files are continuously updated as the project progresses.

---

## Roadmap & Status

### [`roadmap.md`](roadmap.md)
The 10-pillar data engineering roadmap with granular checkbox progress. Pillars cover Programming, SQL/Databases, Data Modeling, Warehousing Platforms, Pipelines/Orchestration, Streaming, Cloud, Infrastructure/DevOps, Data Quality, and Systems Design.

**Use when:** you want to see what's been learned so far, what's in progress, and what's coming next.

---

## Synthesis Drill System

End-of-phase interview-style drills that test cross-component understanding before advancing. Three files work together:

### [`synthesis-questions.md`](synthesis-questions.md)
Drill questions per phase, with hints and resources. **No answers** — used for self-testing without spoilers.

**Use when:** preparing for a phase synthesis drill, or self-quizzing on prior phases for spaced retrieval.

### [`synthesis-answers.md`](synthesis-answers.md)
For completed questions only: original answer, grading breakdown, model 9/10 reference answer, and key lessons.

**Use when:** reviewing graded drills or referring back to model answers for future interview prep.

### [`synthesis-log.md`](synthesis-log.md)
Personal log of hardest questions and recurring weak patterns. Tracks question *types* that repeatedly cause trouble, distinct from concept-level gaps.

**Use when:** noticing the same kind of mistake across multiple drills — the log reveals patterns over time.

---

## Reference Material

### [`terminal-cheatsheet.md`](terminal-cheatsheet.md)
Useful terminal commands organized by tool: shell/PATH, Git, Docker, AWS CLI, Homebrew, Python, file system, networking. Each command has a comment and a "when to use" note. Destructive commands flagged with ⚠️.

**Use when:** you remember "I did this once but can't remember the exact command."

### [`de_flashcards.csv`](de_flashcards.csv) and [`de_flashcards_review.md`](de_flashcards_review.md)
50+ flashcards covering the technical vocabulary encountered across the project. CSV is Anki-importable; Markdown version is human-readable, organized by pillar, with a self-test drill at the bottom.

**Use when:** doing daily 5–10 minute spaced-repetition review.

---

## How These Files Relate

```
                     roadmap.md
                          │
             ┌────────────┴────────────┐
             │                         │
   synthesis-questions.md       de_flashcards.csv
             │                         │
             ▼                         │
     (you attempt drill)               │
             │                         │
             ▼                         │
   synthesis-answers.md ◀──── feed ────┘
             │                vocabulary
             ▼
   synthesis-log.md
   (personal patterns)


   terminal-cheatsheet.md  ── used continuously across all phases
```

**Workflow during a phase:**
1. New concepts encountered → flashcards added to deck
2. New commands encountered → cheatsheet updated
3. End of phase → synthesis drill questions generated
4. Bryan attempts drill → answers + grading recorded
5. Hardest questions noted in synthesis-log
6. Next phase begins

---

## Maintenance

- **Continuously updated:** flashcards, terminal cheatsheet (as new commands appear)
- **Updated end of each phase:** roadmap, synthesis-questions, synthesis-answers, synthesis-log
- **Created once, refined over time:** this README, project root README

If you fork this repo and want to adapt the system to your own learning, the workflow rules are documented in the conversation history with Claude. The artifacts themselves are sufficient to start using.
