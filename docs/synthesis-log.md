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

## Strong Patterns Worth Reinforcing

*Track positive patterns demonstrating senior-engineer instincts. These are habits to keep.*

| Pattern | First seen | Notes |
|---|---|---|
| Self-directed consolidation | Q-Re-2 (Phase 0 re-drill) | When a concept came in below threshold, Bryan paused for a deliberate consolidation session before re-attempting — slowing down to actually understand rather than memorize. Drove a +2.0 score improvement (6.5 → 8.5) on the same question with a different scenario. This is a senior-engineer instinct. |
| Pattern transfer across scenarios | Q-Re-3 (Phase 0 re-drill) | Bidirectional defense-in-depth argument originally taught with STORAGE_ALLOWED_LOCATIONS + IAM transferred cleanly to gitignore + IAM. Same argument shape applied to different specifics. This signals the underlying mental model has internalized rather than been memorized. |
| Layer/scope discipline as meta-skill | Across all three Phase 0 re-drills | Q-Re-1 (system cast vs runtime cast), Q-Re-2 (six-layer config cascade), Q-Re-3 (bidirectional defense layers) — all three improvements came from the same meta-skill of separating layers/scopes/directions and naming each precisely. The original drill's recurring "vocabulary precision on layered systems" weakness had a single root cause that the re-drill systematically addressed. |

---

## Phase 0 — Hardest Questions

*Drill date: 2026-04-29 — Original average: 7.45/10. Re-drill in progress.*

### Original drill

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

### Re-drill

| Q# | Score | Why it was hard | Key takeaway |
|---|---|---|---|
| Q-Re-1 | 7.5/10 ✓ (was 5.5) | Required separating system cast (identities that built/exist in the system) from runtime cast (identities that authenticate during one specific execution); needed Socratic walk to surface | System cast vs runtime cast is the central distinction. At 3 AM when an automated script fires, no human is authenticating — only orchestration components, the script's outbound auth, and any cross-cloud assumed roles. |
| Q-Re-2 | 8.5/10 ✓ (was 6.5) | Required mapping the six-layer config cascade explicitly to fix the layer-confusion from the original | Configuration values cascade through layers (file → tool → process → consumer). Debugging means walking the chain backward. |
| Q-Re-3 | 8.0/10 ✓ (was 7.0) | Required articulating bidirectional defense — what each layer protects against AND what threat it doesn't cover | Bidirectional reasoning pattern transferred from STORAGE_ALLOWED_LOCATIONS+IAM to gitignore+IAM — the shape of the argument generalizes across layer pairs |

### Re-drill Verdict

**Average: 8.0/10 ✓** — meets threshold exactly. **Phase 0 cleared.**

Improvement across the three weakest topics: +6.0 points combined (5.5→7.5, 6.5→8.5, 7.0→8.0). Notably, all three improvements came from the *same underlying meta-skill*: separating layers/scopes/directions and naming each precisely. This is not coincidence — it's evidence the recurring weakness pattern from the original drill ("vocabulary precision on layered systems") has a single root cause that the re-drill systematically addressed.

### Self-reflection notes (to be filled in by Bryan)

*Pick the 2-3 questions that felt hardest in the moment and add a one-line note on what made them hard. This grows the personal pattern map over time.*

- Q__:
- Q__:
- Q__:

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
