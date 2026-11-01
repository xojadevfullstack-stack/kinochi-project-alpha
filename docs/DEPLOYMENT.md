# Production Deployment Architecture & Recommendations

## 1. Executive Summary & Audit Context (Finding #12)
Currently, `run.py` launches both the FastAPI web server (`uvicorn`) and the Telegram Bot (`aiogram` long-polling) within the same Python process and single event loop inside a single container on Render.com.

While convenient for local development, running both workloads inside a single container in production introduces structural operational risks.

---

## 2. Risk Analysis of Single-Container Deployment

### 2.1. Shared Memory Boundary & OOM Kills
Render Starter/Standard instances operate with fixed memory allocations (typically 512MB to 2GB). In a coupled process:
- Telegram bot media handling, caching, or message fan-out can push memory beyond container limits.
- An Out-Of-Memory (OOM) kill by the Linux kernel terminates the entire container, taking down both the bot and the public web API simultaneously.

### 2.2. Event Loop Starvation & Blast Radius
FastAPI and Aiogram share the same asyncio event loop in `run.py`.
- Synchronous or CPU-intensive operations inside Telegram message handlers (e.g., parsing large payloads, heavy json serialization, or un-awaited blocking I/O) delay event loop ticks.
- This results in degraded response times, latency spikes, and timeouts for web portal users.

### 2.3. Horizontal Scaling Barrier (Telegram Long-Polling Conflict)
- Aiogram bot operates in **long-polling** mode (`getUpdates`).
- Telegram's Bot API prohibits multiple concurrent polling connections with the same bot token. If more than one instance attempts long-polling, Telegram returns `409 Conflict: terminated by other getUpdates request`.
- Consequently, the web application **cannot be horizontally scaled** to 2 or more replicas on Render without instantly breaking the bot.

---

## 3. Recommended Decoupled Architecture

To achieve production reliability, zero-downtime rolling deploys, and independent scalability, the ecosystem should be split into **two distinct Render services**:

```
                           ┌──────────────────────────┐
                           │      Render Router       │
                           └─────────────┬────────────┘
                                         │ HTTPS
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Service 1: Web API (Render Web Service)                                         │
│ • Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2         │
│ • Health Check: /health (Probes DB SELECT 1 + Redis)                            │
│ • Scaling: Horizontally scalable (1 .. N replicas)                              │
│ • Environment: Web API + In-Memory Fallback / Redis Caching                     │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│ Service 2: Telegram Bot (Render Background Worker)                              │
│ • Command: python -m bot.main                                                   │
│ • Mode: Long-polling (Exactly 1 replica)                                        │
│ • Scaling: Single worker process with auto-restart supervision                  │
│ • Communication: Interacts with Service 1 via authenticated REST API            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1. Service 1: Web API (Render Web Service)
- **Service Type:** Web Service
- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
- **Health Check Path:** `/health`
- **Pre-deploy Command:** `alembic upgrade head`
- **Advantages:** Independent horizontal scaling, isolated web traffic, zero interference from bot crashes.

### 3.2. Service 2: Bot Client (Render Background Worker)
- **Service Type:** Background Worker
- **Root Directory:** `.`
- **Build Command:** `pip install -r bot/requirements.txt`
- **Start Command:** `python -m bot.main`
- **Replicas:** Fixed at 1 instance (avoiding `409 Conflict`).
- **Advantages:** If the bot restarts or encounters Telegram network disconnects, the public web portal and API remain 100% available.

---

## 4. Alternative: Webhook Mode for High Scale
If bot traffic increases significantly:
1. Transition the bot from long-polling to **Telegram Webhooks**.
2. Mount the webhook handler directly into FastAPI (e.g. `/api/v1/telegram/webhook`).
3. Set `X-Telegram-Bot-Api-Secret-Token` for secure request validation.
4. This eliminates background worker polling and allows both web traffic and bot updates to scale horizontally together behind the load balancer.

---

## 5. Deployment Verification Checklist
1. `alembic heads`: Verify exactly 1 linear head before every deploy.
2. Pre-deploy Alembic execution: Ensure `alembic upgrade head` succeeds before starting the new web binary.
3. Health check readiness: `/health` confirms DB connectivity with `SELECT 1` (timeout 2s) and reports Redis + Bot status.
