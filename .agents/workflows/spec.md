# Spec Workflow & Deep Evaluation Framework

## 1. Workflow Steps
1. Interview the user with clarifying questions to elicit complete requirements.
2. Filter the proposed feature or change through the **8-Axis Deep Evaluation Matrix** below.
3. Define the exact goal, acceptance criteria, out-of-scope items, and technical risks.
4. Formulate test criteria and identify failure modes before writing implementation details.
5. Draft the specification document and save it to `docs/specs/<name>.md`.
6. Present the specification to the user and halt execution until explicit approval is granted.

## 2. 8-Axis Deep Evaluation Matrix
Before drafting any specification or touching code, evaluate across all 8 dimensions:

1. **Problem & Value:** What is this? Why is it needed? What user pain point does it solve? What is lost if omitted?
2. **Target Persona & UX:** Who uses it (mobile, low-bandwidth, Telegram user)? Is it intuitive or confusing? Any friction?
3. **Infrastructure & Cost (0$ Budget):** Impact on serverless quotas (Vercel, Render), Neon DB connections, Telegram API rate limits?
4. **Performance & Resources:** Impact on page speed (LCP, TTFB), DB load (avoid N+1 queries), caching needs?
5. **Edge Cases & Failure Modes:** Offline state, empty DB, Telegram 429 flood wait / 403 forbidden, invalid input?
6. **Alternatives & Benchmarking:** How do competitors (Kinochilar, Netflix, Allplay) solve it? Is there a simpler, zero-code, or leaner alternative?
7. **Reality Check (Code vs Blueprint):** What currently exists in code? (Mock, hardcoded text, broken API, or dummy button?)
8. **Verdict:** Full implementation, lean simplification, or removal (YAGNI)?

## 3. 6 Elite Engineering & Architectural Paradigms
When designing architecture, APIs, or user journeys, verify against these 6 principles:

1. **Antifragility:** Failures must trigger automated self-healing, recovery queues, or fallback discovery—never unhandled crashes or dead ends.
2. **Pre-Mortem & Chaos Verification:** Model catastrophic failure scenarios (rate limits, network partitions, zero balance/quota, DB pool exhaustion) before committing to an architecture.
3. **Circuit Breakers & Bulkheads:** Isolate external dependencies (scrapers, external CDNs, third-party APIs) so that a failure in one subsystem never degrades the core web or bot experience.
4. **Idempotency & Zero-State Safety:** Ensure duplicate user actions, network retries, and rapid clicks produce identical, safe, and deduplicated side-effects.
5. **Working Backwards (PR/FAQ):** Write user-facing value and clarify brutal user questions before writing code or designing mock UI elements.
6. **Observability & Telemetry:** Build mechanisms to capture real-time behavior (search misses, quality selections, error rates) rather than flying blind.
