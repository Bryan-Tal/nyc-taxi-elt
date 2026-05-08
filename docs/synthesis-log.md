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
| Answer completeness — addressing every part of multi-part questions | Phase 0 Q2 | 3x in Phase 0; **improved** in Phase 1 (every Q1-Q10 answer covered all parts) | When question asks "X and Y," tendency to answer X thoroughly and Y briefly |
| Senior-depth language (naming AWS API actions, Snowflake primitives by exact term) | Phase 0 Q5 | 3x in Phase 0 | Knows the concepts; doesn't always reach for the precise term |
| **Enumeration depth on multi-part questions** | Phase 1 Q5, Q8, Q9, Q10 | 4x in Phase 1 | When question asks for N items (e.g., "at least three causes"), answer often gives 1-2 with full reasoning instead of N each. Different from answer-completeness — that's about covering sub-parts; this is about the count *within* a sub-part. Diagnostic: "How many distinct things does this question ask me to enumerate? Have I named that many?" |
| **Reading proposals/scenarios carefully before defending** | Phase 1 Q4 SQL, Q10 challenges 2 & 3 | 3x in Phase 1 | When defending against a proposal, answer addresses a *related but different* question. Diagnostic: "Re-state the proposal in your own words before defending." |
| **Open-book consultation under drill conditions** | Phase 1 Q6 | 1x in Phase 1 | When question explicitly hints at a mental model by name, doesn't reach for the doc. Open-book leverage is unused. Diagnostic: "Did the question name a model/framework? Consult that section before answering." |
| *(more patterns added as they emerge)* | | | |

## Strong Patterns Worth Reinforcing

*Track positive patterns demonstrating senior-engineer instincts. These are habits to keep.*

| Pattern | First seen | Notes |
|---|---|---|
| Self-directed consolidation | Q-Re-2 (Phase 0 re-drill) | When a concept came in below threshold, Bryan paused for a deliberate consolidation session before re-attempting — slowing down to actually understand rather than memorize. Drove a +2.0 score improvement (6.5 → 8.5) on the same question with a different scenario. This is a senior-engineer instinct. |
| Pattern transfer across scenarios | Q-Re-3 (Phase 0 re-drill) | Bidirectional defense-in-depth argument originally taught with STORAGE_ALLOWED_LOCATIONS + IAM transferred cleanly to gitignore + IAM. Same argument shape applied to different specifics. This signals the underlying mental model has internalized rather than been memorized. |
| Layer/scope discipline as meta-skill | Across all three Phase 0 re-drills | Q-Re-1 (system cast vs runtime cast), Q-Re-2 (six-layer config cascade), Q-Re-3 (bidirectional defense layers) — all three improvements came from the same meta-skill of separating layers/scopes/directions and naming each precisely. The original drill's recurring "vocabulary precision on layered systems" weakness had a single root cause that the re-drill systematically addressed. |
| **Answer-completeness improvement** | Phase 1 (vs Phase 0) | Phase 0's recurring pattern was "skip a sub-part entirely." Phase 1 every question (Q1-Q10) addressed every sub-part in some form — measurable improvement in coverage discipline. The next layer (enumeration depth within sub-parts) is the new growth area. |
| **Honest "I'm not sure"** | Phase 1 banked SQL Q (part c) | When asked about Snowflake performance tuning levers, said "I'm not sure" instead of guessing. This is the right call — preserves trust in scoring and surfaces a real study target (warehouse query optimization) rather than papering over the gap with confident-wrong reasoning. |
| **Strong concept fluency on dimensional modeling** | Phase 1 Q2 (8.0), Q3 (8.5), banked SCD2 Q (8.0) | Core dimensional modeling concepts (Richness Test, SCD types, surrogate-key implications) are solid and articulated crisply. The drill's lower scores cluster around *applying* these concepts in multi-part / depth-required formats, not in *understanding* them. |

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

*Drill date: 2026-05-07 — Original average: 6.85/10. Re-drill in progress (Q9, Q10, Q6 targeted).*

### Original drill

| Q# | Score | Why it was hard | Key takeaway |
|---|---|---|---|
| Q1 | 7.0/10 | Grain stated descriptively rather than as a precise noun phrase | Grain statements are single-noun precise: "one row per X" |
| Q2 | 8.0/10 ✓ | Two minor under-classifications (coupon_code, order_status borderline) | Apply richness test, not just cardinality. Use shortcut: "would an analyst JOIN for richer text?" |
| Q3 | 8.5/10 ✓ | Compressed reasoning; could connect SCD choice to schema implication | Type 2 → surrogate keys required. Type 1 → no validity windows. Type 0 → no change-tracking. |
| Q4 | 7.0/10 | SQL has 4 specific bugs (alias-as-column, natural-key join, interval arithmetic, group-by-table) | Concept solid, execution buggy. Phase 3 dbt work is the proving ground. |
| Q5 | 7.5/10 | All four parts addressed but each at one level of depth | Depth-per-part: each sub-part deserves mechanism + consequence |
| Q6 | 6.0/10 | Mental model wasn't fully reached for; "(c) categories" answered with examples | Open-book leverage: when question explicitly hints at a mental model, consult the doc |
| Q7 | 7.5/10 | Rejection of Option 3 too compressed; missed naming concrete failure mode | Defend rejected options with concrete failure modes, not verdicts |
| Q8 | 6.5/10 | Conflated correctness and performance into one failure | Multi-part questions need multi-part answers structurally |
| Q9 | 5.5/10 | One hypothesis fixated on instead of three; queries didn't distinguish hypotheses | Investigation plan = decision tree where each query rules in/out specific causes |
| Q10 | 5.5/10 | Misread Challenges 2 and 3; only addressed (a) sub-part, not (b); only 3 of 6 items | Read proposal carefully; count what question asks for; address each enumeration |

### Re-drill

| Q# | Score | Why it was hard | Key takeaway |
|---|---|---|---|
| Q-Re-1 (was Q9: 5.5) | (pending) | (pending) | (pending) |
| Q-Re-2 (was Q10: 5.5) | (pending) | (pending) | (pending) |
| Q-Re-3 (was Q6: 6.0) | (pending) | (pending) | (pending) |

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
