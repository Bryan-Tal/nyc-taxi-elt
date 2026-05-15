# Data Engineering Synthesis — Practice Log

> **Purpose:** Personal log of hardest questions and recurring weak patterns. Different from the Gaps Log (which tracks weak *concepts*); this tracks weak *question types* and *thinking patterns*.
>
> **Sources tracked (dual-stream as of 2026-05-07):** Patterns surface from both **synthesis drills** (end-of-phase) AND **random interview questions** (dice-triggered, recorded in `interview-questions.md` / `interview-answers.md`). One log, two sources — patterns that recur across both streams are the strongest signal.
>
> **Maintained by Bryan.** Claude prompts updates after each phase synthesis drill grading and after sub-8.0 random questions complete consolidation.
>
> **Standards (raised 2026-05-07):** Drill advancement requires **≥8.5 average AND zero individual questions <8.0**. Random interview questions held to the same individual threshold (≥8.0). Any sub-8.0 question triggers a consolidation session before re-testing, with continuation until ≥95% confidence in topical fluency. The "I don't know" protocol applies during consolidation: hint-driven guidance with a 3-strike rule before full disclosure + deeper consolidation. Senior-DE / intern framing means depth and substantive defense of every claim are mandatory, not optional.
>
> **Companion files:**
> - [`synthesis-questions.md`](./synthesis-questions.md) — synthesis drill questions
> - [`synthesis-answers.md`](./synthesis-answers.md) — synthesis model answers
> - [`interview-questions.md`](./interview-questions.md) — random interview question record
> - [`interview-answers.md`](./interview-answers.md) — random interview model answers

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
| **Self-correction discipline under pushback** | Phase 1 Q-Re-3 consolidation (Layer 2 Q2.1 NULL-vs-legacy correction; Layer 3 column-choice pivot) | When pushed back on a factual error or flawed framing, response was to re-read the data and reason forward from corrected facts — not dig in or guess. This is the senior-engineer habit that compounds. The pattern showed twice in one consolidation session. |
| **Framework transfer without doc consultation** | Phase 1 Q-Re-3 (8.0, +2.0 from original Q6) | Schema vs Semantics Stability framework applied automatically to a fresh domain (8-year e-commerce) without consulting mental-models.md. Diagnostic ritual (structural pass + semantic pass) reached for reflexively. The framework is now internalized rather than recall-on-demand. |
| **Mini-consolidation as recovery pattern** | Phase 1 Q-Re-1 (7.5 first attempt → 8.0 re-attempt) | When the first re-drill attempt landed just short of threshold (7.5), instead of accepting the lower score or jumping immediately to a fresh question, paused for a 10-minute mini-consolidation focused on the specific gap (fingerprint sharpness). Re-attempt with sharper tools cleared 8.0. This is a meta-skill: surgical correction on a named gap beats global re-attack. Mirrors the Phase 0 Q-Re-2 self-directed consolidation pattern at a smaller scale within a single round. |

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

**Average: 8.0/10 ✓** — met original 8.0 threshold (cleared at the time).

> **Note (2026-05-07):** The drill threshold was subsequently raised to 8.5+ average AND zero individual questions <8.0. Under the new standard, the Phase 0 re-drill (Q-Re-1 = 7.5) would not have cleared without further consolidation. The pillars promoted to ★ during Phase 0 (Git workflows, Medallion architecture, Snowflake RBAC, IAM principles, Docker, Docker Compose) remain accurate as theory-learned ★ items because the underlying concepts were demonstrated. The senior-DE / intern framing established 2026-05-07 means future drills will not advance under similar circumstances; consolidation continues until ≥95% confidence is reached.

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
| Q-Re-1 (was Q9: 5.5) | 8.0/10 ✓ (+2.5) | Required building "Investigation as Decision Tree" framework from scratch (no existing mental model entry). First re-attempt landed at 7.5 due to vague fingerprints; recovered via mid-round mini-consolidation on fingerprint-sharpness specifically. Re-attempt scored 8.0 with sharper signatures. | Largest improvement of any Phase 1 re-drill (+2.5). New mental model "Investigation as Decision Tree" added to mental-models.md §12 with 6-category checklist + distinguishing-query pattern. Mini-consolidation as a recovery pattern proves: surgical precision-building beats global re-attack when a re-drill falls just short. |
| Q-Re-2 (was Q10: 5.5) | (pending) | (pending) | (pending) |
| Q-Re-3 (was Q6: 6.0) | 8.0/10 ✓ (+2.0) | Required reaching for the structured drift taxonomy reflexively rather than improvising from "first thing that came to mind". One terminology slip (soft-state vs NULL-population) and missed the acquisition-context hint. | The structural pass + semantic pass discipline transferred without consulting the doc — that's the consolidation working. Categories of drift internalized; precision between similar categories (soft-state vs NULL-population) is the next refinement. |

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

## Phase 1 Wave 2 — Deferred Consolidation Tracker

*Added 2026-05-08. **Phase-1-only exception** to the strict elevated standard. Phase 2 onward enforces strict (every sub-8.0 → consolidation + re-drill before phase advances; no deferrals).*

The Phase 1 drill produced more sub-8.0 questions than the original re-drill plan covered. Rather than block forward momentum with 6+ consecutive consolidation rounds (cognitive load risk; some items naturally re-test through Phase 2/3 implementation), these items are deferred to Wave 2 with explicit trigger conditions. **All Wave 2 items must close before Phase 2 advances to Phase 3.**

| Item | Score | Concept gap | Treatment | Trigger condition |
|---|---|---|---|---|
| Q1 (Grain) | 7.0 | Grain-statement precision (single noun phrase, not domain description) | Light consolidation (~1 round) | Phase 2 grain decisions or Phase 3 fact-table design |
| Q4 (Role-playing SQL) | 7.0 | SQL execution mechanics (alias-as-column, surrogate-vs-natural join, interval arithmetic, group-by-attribute) | Implementation-based re-test | Phase 3 dbt model writing — real role-playing dimension queries |
| Q5 (Star vs Snowflake) | 7.5 | Depth-per-part on the historical context and cost-benefit math | Light consolidation (~1 round) | Phase 2 STAGING design discussions |
| Q7 (Type drift) | 7.5 | Concrete failure mode for Option 3 (over-engineering with opportunity cost) | Implementation-based re-test | Phase 2 STAGING dbt models — TRY_CAST patterns |
| Q8 (Surrogate key failure) | 6.5 | Distinct correctness vs performance failures (one mechanism, two failure types) | Targeted consolidation (~1 round) | Phase 3 SCD2 implementation |
| RQ-002 (Snowflake perf tuning) | 6.0 | Three areas: is_current trap mechanics, range-filter SQL precision, Snowflake performance fundamentals | Full teaching session + re-drill | Phase 3 query optimization OR quarterly rerun |

**Rules for Wave 2:**
- Each item gets full consolidation when its trigger fires — not light treatment
- Re-drill must score ≥8.0 individually to close
- If a trigger doesn't fire by end of Phase 2 work, the item gets explicit consolidation before Phase 3 advances
- Items closed in Wave 2 update this table with score and date

**Why Phase 1 gets this exception:** the standard was elevated mid-drill. Applying it retroactively to all sub-8.0 questions would mean 6+ consecutive consolidation rounds on Phase 1 material before Phase 2 starts. Cognitive-load risk degrades consolidation quality. Some items (Q4, Q7) re-test naturally through Phase 2/3 implementation more rigorously than isolated drill questions could. Severity-weighted approach (Wave 1 = ≤6.0; Wave 2 = 6.5-7.5) honors the standard's spirit — every gap gets addressed, but each gets the treatment that matches its severity.

**Phase 2 onward:** strict standard. No Wave 2.

---

## Random Interview Questions — Sub-8.0 Tracker

*Persistent record of random interview questions (from `interview-answers.md`) that scored below the individual 8.0 threshold and require consolidation before re-drill. Updated as questions are graded and as consolidation status changes.*

| ID | Topic | Score | Consolidation status | Re-drill target |
|---|---|---|---|---|
| RQ-002 | SCD2 + is_current trap; SQL rewrite; Snowflake perf tuning | 6.0/10 | 🚧 OPEN — 3 sub-areas need teaching: (1) is_current trap mechanics, (2) range-filter SQL precision, (3) Snowflake performance tuning fundamentals | End of Phase 2 OR quarterly rerun, whichever first |
| *(more entries added as random questions surface gaps)* | | | | |

**Above-threshold random questions** (≥8.0, no consolidation needed) are not listed here — they're recorded in `interview-answers.md` only.

---

## How to Use This Log

After each phase's synthesis drill grading:

1. **Pick the 2–3 hardest questions** (lowest scores or where you felt least confident).
2. **For each: a one-line "why it was hard"** — was the concept fuzzy? The vocabulary? The connection between two domains? The diagnostic process?
3. **Identify the takeaway** — the one thing you'd do differently next time.
4. **Update the "Recurring Weak Patterns" table** if you notice the same kind of mistake across multiple questions.

This log is also a **portfolio artifact**. An interviewer who sees `/docs/synthesis-log.md` in your repo recognizes the kind of self-directed, deliberate learning that senior teams want. Don't hide it.
