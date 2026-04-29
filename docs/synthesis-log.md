# Data Engineering Synthesis — Practice Log

> **Purpose:** Personal log of hardest synthesis questions and recurring weak patterns. Different from the Gaps Log (which tracks weak *concepts*); this tracks weak *question types* and *thinking patterns*.
>
> **Maintained by Bryan.** Claude prompts updates after each phase synthesis drill grading.
>
> **Companion files:**
> - [`synthesis-questions.md`](./synthesis-questions.md) — drill questions
> - [`synthesis-answers.md`](./synthesis-answers.md) — model answers

---

## Recurring Weak Patterns

*Track patterns that appear across multiple questions or phases. Update as patterns emerge.*

| Pattern | First seen | Frequency | Notes |
|---|---|---|---|
| Vocabulary precision on layered systems (role vs principal, integration vs stage, image vs container) | Phase 0 Q1 | 4x in Phase 0 | Recurring — affects identity enumeration, IAM, Docker explanations |
| Answer completeness — addressing every part of multi-part questions | Phase 0 Q2 | 3x in Phase 0 | When question asks "X and Y," tendency to answer X thoroughly and Y briefly |
| Senior-depth language (naming AWS API actions, Snowflake primitives by exact term) | Phase 0 Q5 | 3x in Phase 0 | Knows the concepts; doesn't always reach for the precise term |
| *(more patterns added as they emerge)* | | | |

---

## Phase 0 — Hardest Questions

*Drill date: 2026-04-29 — Final average: 7.45/10 (below 8.0 threshold; re-drill required for Q2/Q4/Q6)*

| Q# | Score | Why it was hard | Key takeaway |
|---|---|---|---|
| Q1 | 7.5/10 | Vocab precision on STS credential names; subtle attribution (integration vs. stage) | Use exact API/object terminology; integration is the security primitive, stage references it |
| Q2 | 7.0/10 | Answered defense-in-depth in only one direction | Defense in depth requires articulating threats from BOTH sides |
| Q3 | 8.5/10 ✓ | Strong; minor SNAPSHOTS slip; missing lifecycle/retention angle | SNAPSHOTS = SCD2 history (production), not dev |
| Q4 | 6.5/10 | Conflated service-level bind mounts with top-level named volumes; didn't directly answer "what would break" | Two kinds of "volumes" in Compose serve different purposes; answer the question's specific prompt directly |
| Q5 | 7.5/10 | Skipped the same-region cost decision; got the production AUTO_SUSPEND trade-off backwards | Cost trade-offs flip at scale: dev wants fast suspend; prod wants smooth resume |
| Q6 | 5.5/10 | Named ~3 of 8 distinct identities; treated `Principal` as an identity | `Principal` is a JSON field naming an identity, not the identity itself |
| Q7 | 7.5/10 | Right tools (CloudTrail) but wrong root cause hypothesis | When failures cycle with calendar regularity, look for scheduled infrastructure |
| Q8 | 8.5/10 ✓ | Clean diagnosis | Could have named the 12-Factor App pattern explicitly |
| Q9 | 7.5/10 | Right category (session state) but only named one of four state values | Always check ALL four: ROLE, DATABASE, SCHEMA, WAREHOUSE |
| Q10 | 8.5/10 ✓ | Strong technical defenses; light on the "interview signal" angle | Part (b) of design-defense questions matters as much as part (a) |

### Self-reflection notes (to be filled in by Bryan)

*Pick the 2-3 questions that felt hardest in the moment and add a one-line note on what made them hard. This grows the personal pattern map over time.*

- Q1: Having the first question force me to bring everything together was daunting. 
- Q4: Determining how docker and postgres communicate felt daunting at first. For this I had to look up what a connection string is, and struggled a little with volumes, containers and images. Will brush up on this before tackling next time.
- Q6: Naming each identity is something I'm having a good amount of trouble with, will look more into this. 


---

## Phase 1 — Hardest Questions

*To be added at end of Phase 1.*

---

## Phase 2 — Hardest Questions

*To be added at end of Phase 2.*

---

## Phase 3 — Hardest Questions

*To be added at end of Phase 3.*

---

## Phase 4 — Hardest Questions

*To be added at end of Phase 4.*

---

## Phase 5 — Hardest Questions

*To be added at end of Phase 5.*

---

## Phase 6 — Hardest Questions

*To be added at end of Phase 6.*

---

## How to Use This Log

After each phase's synthesis drill grading:

1. **Pick the 2–3 hardest questions** (lowest scores or where you felt least confident).
2. **For each: a one-line "why it was hard"** — was the concept fuzzy? The vocabulary? The connection between two domains? The diagnostic process?
3. **Identify the takeaway** — the one thing you'd do differently next time.
4. **Update the "Recurring Weak Patterns" table** if you notice the same kind of mistake across multiple questions.

This log is also a **portfolio artifact**. An interviewer who sees `/docs/synthesis-log.md` in your repo recognizes the kind of self-directed, deliberate learning that senior teams want. Don't hide it.
