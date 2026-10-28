# Observability & Telemetry Workflow

## Purpose
Ensure complete operational visibility into system behavior. Eliminate "blind flying" by enforcing structured logging, error tracking, and actionable user metrics.

## Execution Steps
1. **No Swallowed Exceptions:**
   - Every `except Exception:` block must log the traceback with contextual metadata (`user_id`, `movie_code`, `request_id`).
   - Never use bare `pass` or silent `return None` in error handlers.
2. **Structured Logging:**
   - Use structured logs with severity levels (`INFO`, `WARNING`, `ERROR`).
   - Log critical state transitions: search queries, video deliveries, cache misses, and webhook retries.
3. **User Behavior Telemetry:**
   - Track zero-result searches ("Movie not found") to identify high-demand missing content.
   - Monitor quality preference distribution (`480p` vs `720p` vs `1080p`) to optimize bot payload sizes.
4. **Health & Circuit Status Endpoints:**
   - Expose `/api/v1/health` verifying DB connectivity, Redis availability, and bot webhook status.
   - Log circuit breaker trip and reset events immediately with `CRITICAL` or `WARNING` alerts.
