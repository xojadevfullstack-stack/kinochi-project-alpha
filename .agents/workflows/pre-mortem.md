# Pre-Mortem & Chaos Engineering Workflow

## Purpose
Anticipate and eliminate catastrophic system failures before deploying features or modifying architecture. Assume the system has already suffered a total outage and determine why.

## Execution Steps
1. **Define the Future Disaster:** Assume 6 months have passed and the feature or system has completely collapsed (e.g. database locked up, Telegram bot banned, Vercel budget drained, users rage-quitting).
2. **Brainstorm Catastrophic Vectors:**
   - **External APIs:** What if Telegram returns 429 Flood Wait, 403 Forbidden, or undergoes a 2-hour downtime?
   - **Infrastructure Quotas:** What if Neon DB exhausts connection pools, or Vercel hits serverless execution limits?
   - **Concurrency & Races:** What happens if 500 users click the same movie code simultaneously?
   - **Data Corruption:** What if partial records are written when an external scraper fails mid-run?
3. **Design Defensive Countermeasures:**
   - Add Circuit Breakers for all third-party network calls.
   - Enforce Idempotency on database mutations and bot button dispatches.
   - Implement Graceful Degradation (fallback cached content instead of raw 500 errors).
4. **Document in Spec:** Record all identified vectors and mitigation logic in Section 5 of `docs/specs/<name>.md`.
