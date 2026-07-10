# Kinochi — Project Requirements Document & Technical Documentation

**Version:** 1.0 (MVP)
**Document type:** PRD + Technical Architecture
**Audience:** Engineering team, Product, Design, QA

---

## 1. Project Overview

Kinochi is a movie discovery and delivery platform built around a simple, proven distribution loop for short-video-driven traffic: **discover on the web, watch via Telegram**.

The product is composed of three client applications sharing a single backend and a single database:

| Application | Purpose | Primary Users |
|---|---|---|
| Telegram Bot | Delivers movies, handles search, subscriptions, and user interaction | End users watching movies |
| Website (Next.js) | SEO-friendly movie catalog and discovery surface | End users arriving from social media |
| Admin Panel | Content and operations management | Internal team / moderators |

The website never streams video. It exists purely to inform, rank in search engines, and convert visitors into Telegram bot users via a single "Watch on Telegram" call to action. The bot is the only place where the actual movie file/content is delivered.

This document defines the MVP scope, architecture, and module breakdown needed for a development team to begin implementation immediately, while keeping the design extensible for future growth.

---

## 2. Vision

Kinochi aims to become the go-to lightweight movie discovery layer for social-media-driven audiences — capturing viewers scrolling TikTok, Reels, and Shorts, and converting that attention into an engaged Telegram community where movies are delivered instantly, without friction, ads, or streaming infrastructure overhead.

Long-term, Kinochi should become a content brand: a catalog trusted for accurate movie metadata, fast search, and reliable delivery, with the Telegram bot as the retention and monetization engine.

---

## 3. Goals

- Ship a functional MVP with the three applications integrated through one backend.
- Provide a fast, SEO-optimized movie catalog website that ranks organically and converts visitors into Telegram bot users.
- Deliver movies through Telegram reliably, with basic gating (mandatory channel subscription) to grow owned community channels.
- Give the internal team a simple admin panel to manage movies, categories, mandatory channels, and broadcasts without engineering involvement.
- Establish clean architectural boundaries so that v2 features (payments, recommendations, multi-language, mobile apps) can be added without rewriting the core system.

---

## 4. Non-Goals

To keep the MVP lean, the following are explicitly **out of scope for v1**:

- In-browser or in-app video streaming/playback.
- User accounts, login, or authentication on the website.
- Payment processing, subscriptions, or monetization features.
- Recommendation engine / personalization algorithms.
- Multi-language localization (v1 ships in a single language, extensible later).
- Native mobile apps.
- Comments, ratings, or reviews submitted by users.
- Advanced analytics/BI dashboards (only basic statistics in v1).
- Multi-admin role-based permission granularity (a single admin role is sufficient for v1).

---

## 5. User Journey

### 5.1 Primary discovery flow (Website)

1. User watches a short clip about a movie on TikTok / Reels / Shorts.
2. User clicks a link in bio or caption, landing on the Kinochi website (movie detail page or homepage).
3. User browses movie details: poster, description, ratings, cast, trailer.
4. User clicks **"Watch on Telegram."**
5. User is redirected to the Telegram bot with a deep link (e.g., `t.me/KinochiBot?start=movie_<code>`).

### 5.2 Telegram delivery flow (Bot)

1. Bot receives `/start` with an optional movie code payload.
2. If new user, bot registers the user (Telegram ID, username, language, join date).
3. Bot checks mandatory channel subscription; if not subscribed, prompts the user to join required channels before proceeding.
4. Once verified, bot sends the requested movie (if a code was passed) or shows the main menu (search by title, browse categories, search by code).
5. User can search again, browse categories, or check their profile at any time.

### 5.3 Admin flow

1. Admin logs into the Admin Panel.
2. Admin adds/edits movies, categories, and mandatory channels.
3. Admin creates and sends broadcasts to the bot's user base.
4. Admin reviews basic statistics (users, top movies, bot growth).

---

## 6. Functional Requirements

### 6.1 Telegram Bot

| Feature | Description |
|---|---|
| Start / onboarding | Handles `/start`, deep-link payloads, and first-time registration |
| User registration | Stores Telegram ID, username, first name, language, created_at |
| Mandatory subscription | Verifies membership in one or more required channels before granting access |
| Search by code | Users enter a short unique movie code to retrieve a specific movie instantly |
| Search by title | Free-text search against movie titles (and optionally original titles) |
| Categories | Browse movies by genre/category via inline menus |
| Send movie | Delivers the movie file (or file reference) plus caption/metadata to the user |
| Basic profile | Shows user's Telegram ID, join date, and basic usage stats (e.g., movies watched count) |
| Admin broadcast | Allows admins to push a message/media to all or segmented bot users |
| Basic statistics | Tracks total users, daily active users, most requested movies |

### 6.2 Website

| Feature | Description |
|---|---|
| Homepage | Featured/latest/popular movies, entry point for browsing |
| Movie search | Search by title with instant results, filterable by category |
| Movie details page | Full metadata display + "Watch on Telegram" CTA |
| SEO | Server-side rendering, meta tags, structured data (schema.org Movie), sitemap, clean URLs |
| No streaming | No video player, no file delivery on the website |
| No login | Fully public, anonymous browsing |

**Movie details page must display:**
Poster, Title, Original Title, Description, IMDb rating, TMDB rating (if available), Genres, Cast, Director, Release Year, Runtime, Trailer (embedded, e.g., YouTube), "Watch on Telegram" button.

### 6.3 Admin Panel

| Feature | Description |
|---|---|
| Dashboard | High-level overview: total movies, total users, recent activity |
| Movie CRUD | Create, read, update, delete movie entries including metadata and Telegram file reference |
| Category CRUD | Manage genre/category taxonomy |
| Mandatory channels management | Add/remove Telegram channels users must join |
| Broadcast management | Compose, schedule, and send broadcasts; view delivery status |
| Basic statistics | Charts/numbers for user growth, popular movies, bot engagement |
| Settings | Global configuration (e.g., bot messages, default mandatory channel list, maintenance mode) |

---

## 7. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Performance | Website pages should load (LCP) under 2.5s on 4G; API responses under 300ms for read endpoints under normal load |
| Scalability | Backend must scale horizontally (stateless API instances behind a load balancer) |
| Availability | Target 99.5% uptime for MVP; graceful degradation if Telegram API is temporarily unavailable |
| SEO | Server-side rendering for all public movie pages; valid structured data; sitemap.xml and robots.txt |
| Security | Admin panel behind authentication; rate limiting on public search endpoints; input validation everywhere |
| Maintainability | Clean Architecture layering; clear separation between domain logic, API layer, and infrastructure |
| Observability | Structured logging, basic error tracking, health-check endpoints |
| Data integrity | Alembic-managed migrations; referential integrity enforced at the database level |
| Portability | Fully containerized (Docker) for consistent local/staging/production environments |

---

## 8. System Architecture

### 8.1 High-level architecture

```
                         ┌─────────────────────┐
                         │   PostgreSQL (DB)    │
                         └──────────▲───────────┘
                                    │
                         ┌──────────┴───────────┐
                         │     Redis (cache,     │
                         │  rate-limit, sessions)│
                         └──────────▲───────────┘
                                    │
                    ┌───────────────┴────────────────┐
                    │      Backend API (FastAPI)      │
                    │  - Domain Layer                 │
                    │  - Application Layer (use cases)│
                    │  - Infrastructure Layer          │
                    └───────────────┬────────────────┘
                                    │  REST (internal)
        ┌───────────────┬──────────┴─────────┬───────────────┐
        │               │                    │               │
┌───────▼──────┐ ┌───────▼───────┐  ┌─────────▼────────┐      │
│ Telegram Bot  │ │  Website      │  │  Admin Panel     │      │
│ (aiogram 3.x) │ │  (Next.js)    │  │  (Next.js)       │      │
└───────────────┘ └───────────────┘  └───────────────────┘      │
        │                                                        │
        ▼                                                        ▼
  Telegram API                                          End users / Admins
```

**Key architectural principles:**

- **Single source of truth:** One PostgreSQL database, accessed only through the backend API — no client talks to the database directly.
- **Stateless API:** The FastAPI backend holds no session state in memory; all shared state lives in PostgreSQL or Redis, enabling horizontal scaling.
- **Clean Architecture layering:** Domain (entities, business rules) → Application (use cases/services) → Infrastructure (DB, Telegram, external APIs) → Presentation (REST controllers, bot handlers).
- **Bot as a client, not a monolith:** The Telegram bot is a thin presentation layer calling the same backend API as the website and admin panel — it does not contain business logic itself.
- **Redis for cross-cutting concerns:** Caching movie queries, rate-limiting search endpoints, and (optionally) tracking mandatory-subscription check results to reduce Telegram API calls.

### 8.2 Why this architecture fits an MVP

- Avoids duplicating business logic across bot/web/admin — all three consume the same API contract.
- Keeps the system simple: one database, one backend, three thin clients.
- Leaves room to later split the backend into services (e.g., a dedicated search service) without touching the clients, since they only depend on the API contract, not on internal implementation.

---

## 9. Folder Structure

### 9.1 Backend (`/backend`)

```
backend/
├── app/
│   ├── domain/                 # Entities, value objects, domain rules (no framework deps)
│   │   ├── movies/
│   │   ├── categories/
│   │   ├── users/
│   │   ├── channels/
│   │   └── broadcasts/
│   ├── application/            # Use cases / services, orchestration logic
│   │   ├── movies/
│   │   ├── categories/
│   │   ├── users/
│   │   ├── channels/
│   │   ├── broadcasts/
│   │   └── statistics/
│   ├── infrastructure/         # DB models, repositories, external integrations
│   │   ├── db/
│   │   │   ├── models/
│   │   │   ├── repositories/
│   │   │   └── session.py
│   │   ├── telegram/           # Wrapper around Telegram Bot API calls (send file, check membership)
│   │   ├── cache/              # Redis client wrappers
│   │   └── external/           # IMDb/TMDB metadata fetchers (optional, v1.1+)
│   ├── api/                    # FastAPI routers, request/response schemas
│   │   ├── v1/
│   │   │   ├── movies.py
│   │   │   ├── categories.py
│   │   │   ├── users.py
│   │   │   ├── channels.py
│   │   │   ├── broadcasts.py
│   │   │   ├── statistics.py
│   │   │   └── admin_auth.py
│   │   └── deps.py             # Shared dependencies (auth, pagination, db session)
│   ├── core/                   # Settings, config, security, logging
│   └── main.py                 # FastAPI app entrypoint
├── alembic/                     # Migrations
├── tests/
└── pyproject.toml / requirements.txt
```

### 9.2 Telegram Bot (`/bot`)

```
bot/
├── handlers/
│   ├── start.py
│   ├── search.py
│   ├── categories.py
│   ├── profile.py
│   └── admin_broadcast.py
├── middlewares/
│   ├── subscription_check.py
│   └── user_registration.py
├── services/                    # Thin API client calling the backend
│   └── api_client.py
├── keyboards/                    # Inline/reply keyboard builders
├── config.py
└── main.py
```

### 9.3 Website (`/web`)

```
web/
├── app/                          # Next.js App Router
│   ├── page.tsx                  # Homepage
│   ├── movies/
│   │   ├── page.tsx               # Search results
│   │   └── [slug]/page.tsx        # Movie details page
│   └── sitemap.ts / robots.ts
├── components/
├── lib/
│   └── api.ts                    # Backend API client
└── styles/
```

### 9.4 Admin Panel (`/admin`)

```
admin/
├── app/
│   ├── dashboard/
│   ├── movies/
│   ├── categories/
│   ├── channels/
│   ├── broadcasts/
│   ├── statistics/
│   └── settings/
├── components/
├── lib/
│   └── api.ts
└── styles/
```

---

## 10. Database Design (High Level)

The MVP requires the following core entities. No SQL or field-level schema is defined here — only conceptual structure and relationships.

| Entity | Purpose | Key Relationships |
|---|---|---|
| **Movie** | Core catalog item: title, original title, description, ratings, genres, cast, director, year, runtime, poster, trailer URL, unique code, Telegram file reference | Many-to-many with Category; referenced by Broadcast and Statistics |
| **Category** | Genre/category taxonomy | Many-to-many with Movie |
| **User** (Telegram user) | Bot user profile: Telegram ID, username, language, join date, activity flags | One-to-many with MovieRequestLog |
| **MandatoryChannel** | Telegram channels users must join before bot access | Referenced by subscription-check logic |
| **Broadcast** | Admin-created messages sent to users | One-to-many with BroadcastDeliveryLog (optional, for delivery tracking) |
| **MovieRequestLog** | Records each time a user requests/receives a movie (powers statistics) | Belongs to User and Movie |
| **AdminUser** | Admin panel accounts | Independent, used only for admin auth |

**Conceptual relationship diagram:**

```
Category ──(M:N)── Movie ──(1:N)── MovieRequestLog ──(N:1)── User
                                                              │
MandatoryChannel (independent, checked at runtime)           │
Broadcast ──(sent to)── User(s)                               │
AdminUser (manages Movie, Category, MandatoryChannel, Broadcast)
```

**Design notes:**

- The unique **movie code** is the field that connects the website's "Watch on Telegram" button to the bot's deep-link payload — this is the critical integration point between web and bot.
- Movie storage itself (the actual video file) lives on Telegram's infrastructure; the database only stores a **file_id/reference**, keeping the backend lightweight and avoiding media storage costs.
- All timestamps (created_at, updated_at) should be standard on every table for auditability and future analytics.

---

## 11. API Structure (High Level Only)

The backend exposes a single versioned REST API (`/api/v1/`) consumed by all three clients. No endpoint-level detail is specified here — only resource groupings and access boundaries.

| Resource Group | Consumed By | Access Level |
|---|---|---|
| `movies` | Website, Bot, Admin | Public read (website/bot); authenticated write (admin) |
| `categories` | Website, Bot, Admin | Public read; authenticated write |
| `users` | Bot, Admin | Internal (bot uses service credentials); admin read-only |
| `channels` (mandatory subscriptions) | Bot, Admin | Internal read (bot); authenticated write (admin) |
| `broadcasts` | Bot (delivery), Admin (management) | Authenticated write (admin); internal trigger (bot delivery worker) |
| `statistics` | Admin | Authenticated read only |
| `auth` | Admin | Public login endpoint; issues session/JWT for admin panel |

**Cross-cutting API principles:**

- All public-facing read endpoints (movies, categories) are cacheable via Redis to reduce database load from website traffic spikes.
- Bot-to-backend and admin-to-backend calls are authenticated differently: the bot uses a service-level API key/secret; the admin panel uses per-admin session/JWT authentication.
- Pagination, filtering, and search are standardized across all list endpoints (movies, categories, users) using shared query parameter conventions.
- The API is the **only** integration point — the bot and admin panel never query PostgreSQL or Redis directly.

---

## 12. Telegram Bot Modules

| Module | Responsibility |
|---|---|
| **Onboarding** | Handles `/start`, deep-link payload parsing, first-time user registration |
| **Subscription Gate** | Middleware that checks mandatory channel membership before allowing any other action |
| **Search (code)** | Accepts a movie code, fetches and delivers the matching movie |
| **Search (title)** | Free-text search against the movies API, returns a selectable list |
| **Categories** | Inline-keyboard-driven browsing by genre |
| **Movie Delivery** | Sends the movie file (via stored Telegram file_id) with caption/metadata; logs the delivery event |
| **Profile** | Displays user's basic info and usage stats |
| **Broadcast Receiver** | Listens for admin-triggered broadcast jobs and delivers messages/media to the user base (in batches, respecting Telegram rate limits) |
| **Statistics Reporting** | Sends usage events to the backend for aggregation (does not compute statistics itself) |

---

## 13. Website Modules

| Module | Responsibility |
|---|---|
| **Homepage** | Fetches and displays featured/latest/popular movies from the API |
| **Search & Browse** | Title search and category filtering, server-rendered for SEO |
| **Movie Details Page** | Renders full metadata, trailer embed, and "Watch on Telegram" CTA with the deep-link containing the movie code |
| **SEO Layer** | Metadata generation, structured data (schema.org `Movie`), sitemap generation, canonical URLs |
| **API Client** | Shared module for all server-side data fetching against the backend API |

---

## 14. Admin Panel Modules

| Module | Responsibility |
|---|---|
| **Auth** | Admin login/session management |
| **Dashboard** | Aggregated overview widgets (totals, recent activity) |
| **Movie Management** | Full CRUD UI for movies, including Telegram file_id input/validation |
| **Category Management** | CRUD UI for categories |
| **Mandatory Channels Management** | CRUD UI for required subscription channels |
| **Broadcast Management** | Compose/schedule/send broadcasts, view basic delivery status |
| **Statistics** | Visualizes user growth, top movies, engagement metrics |
| **Settings** | Global bot messages/config, feature toggles (e.g., maintenance mode) |

---

## 15. Security Considerations

- **Admin authentication:** Session-based or JWT authentication required for all admin panel and admin API routes; passwords hashed with a strong algorithm (e.g., bcrypt/argon2).
- **Bot-to-backend trust:** The bot authenticates to the backend using a dedicated service credential (not a per-user token), scoped to only the endpoints it needs.
- **Rate limiting:** Public search endpoints (website and bot search) are rate-limited via Redis to prevent scraping and abuse.
- **Input validation:** All API inputs validated via Pydantic schemas; no raw user input reaches the database layer unvalidated.
- **Telegram data handling:** Only the minimum necessary Telegram user data is stored (ID, username, language) — no sensitive personal data is collected.
- **Mandatory subscription integrity:** Subscription checks are performed server-side against the Telegram API at request time (with short-lived caching), not trusted from client-reported state.
- **Secrets management:** Bot tokens, DB credentials, and API keys stored via environment variables / secret manager, never committed to source control.
- **CORS:** Backend API restricts cross-origin access to the known website and admin panel domains.
- **Audit logging:** Admin actions (movie edits, broadcasts sent) are logged with admin ID and timestamp for accountability.

---

## 16. Scalability Plan

The MVP architecture is intentionally simple, but each layer has a clear scaling path:

| Layer | MVP Approach | Scaling Path |
|---|---|---|
| Backend API | Single FastAPI service, stateless | Run multiple instances behind a load balancer; scale horizontally |
| Database | Single PostgreSQL instance | Add read replicas for read-heavy website traffic; connection pooling (PgBouncer) |
| Caching | Redis for hot movie queries and rate limiting | Expand to cache search results, category listings, and session data as traffic grows |
| Telegram Bot | Single aiogram process (long polling or webhook) | Move to webhook mode behind a load balancer; shard broadcast delivery across workers/queues |
| Broadcasts | Synchronous or simple batch sending | Move to a queue-based worker (e.g., Celery/RQ + Redis) for large-scale, rate-limit-safe delivery |
| Website | Server-rendered Next.js, cacheable pages | CDN caching for static/ISR pages; edge caching for movie detail pages |
| Search | Simple SQL `LIKE`/trigram search on title | Migrate to a dedicated search engine (e.g., PostgreSQL full-text search → Meilisearch/Elasticsearch) as catalog grows |

**Guiding principle:** every scaling step above is additive — none require rewriting the domain/application layers, because they sit behind the Clean Architecture boundaries defined in Section 8.

---

## 17. Future Roadmap (Post-MVP)

- **v1.1:** Automated metadata enrichment (IMDb/TMDB API integration) instead of manual admin entry.
- **v1.2:** Advanced search (autocomplete, typo-tolerant search, filters by year/genre/rating).
- **v1.3:** Personalized recommendations ("Similar movies," "Because you watched...").
- **v1.4:** Multi-language support for both website and bot.
- **v1.5:** User accounts on the website (watchlists, favorites) — still no streaming, purely engagement features.
- **v1.6:** Monetization: premium Telegram channel tiers, ads on website, or sponsored placements.
- **v1.7:** Native mobile app wrapping the same backend API.
- **v1.8:** Analytics dashboard expansion (cohort analysis, retention curves, funnel tracking from social → website → bot).

---

## 18. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Telegram API rate limits during broadcasts | Delayed/failed message delivery to large user bases | Implement queue-based, rate-limit-aware broadcast delivery from day one |
| Copyright/content takedown requests | Legal exposure, bot/channel bans | Maintain clear content moderation policy and rapid takedown process in admin panel |
| Mandatory subscription abuse (users leaving channels after access) | Reduced channel growth value | Periodic re-verification; acceptable as an MVP trade-off, revisit in v1.x |
| SEO underperformance | Low organic traffic, over-reliance on social ads | Invest early in structured data, sitemaps, and performance (Core Web Vitals) |
| Single point of failure (one backend, one DB) | Downtime affects all three apps simultaneously | Health checks, automated backups, staged rollout, and monitoring/alerting from launch |
| Movie file_id invalidation (Telegram file references can expire in edge cases) | Broken delivery for older movies | Admin panel validation/re-upload workflow; periodic integrity checks |
| Manual metadata entry errors | Poor catalog quality, SEO harm | Admin panel form validation; future roadmap item to automate via TMDB/IMDb APIs |

---

## 19. Deployment Overview

```
                     ┌───────────────────────────┐
                     │        DNS / CDN           │
                     └──────────────┬─────────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
         ┌───────▼───────┐  ┌───────▼───────┐  ┌────────▼────────┐
         │  Website        │  │  Admin Panel  │  │  Reverse Proxy  │
         │  (Next.js,      │  │  (Next.js,    │  │  (Nginx/Traefik)│
         │  containerized) │  │  containerized│  │                 │
         └───────┬─────────┘  └───────┬────────┘  └────────┬────────┘
                 │                    │                     │
                 └────────────────────┴─────────────────────┘
                                      │
                          ┌───────────▼────────────┐
                          │   Backend API (FastAPI) │
                          │   (containerized,       │
                          │   multiple replicas)    │
                          └────────┬────────┬────────┘
                                   │        │
                       ┌───────────▼──┐  ┌───▼───────────┐
                       │ PostgreSQL    │  │ Redis          │
                       │ (managed DB)  │  │ (managed cache)│
                       └───────────────┘  └────────────────┘

                          ┌──────────────────────────┐
                          │  Telegram Bot (aiogram)   │
                          │  (containerized worker)   │
                          └──────────────┬────────────┘
                                         │
                                   Telegram API
```

**Deployment principles:**

- Each application (backend, bot, website, admin) is independently containerized (Docker) and independently deployable.
- Database migrations run via Alembic as a controlled deployment step, never automatically on app boot in production.
- Environment separation: local → staging → production, with isolated databases and Telegram bot tokens per environment.
- CI/CD pipeline runs tests, builds images, and deploys on merge to main branches (exact CI tooling to be decided by the team — e.g., GitHub Actions).
- Logging and monitoring (e.g., basic APM/error tracking) attached to the backend and bot from day one to catch issues before they affect users.

---

## 20. Development Phases

| Phase | Scope | Outcome |
|---|---|---|
| **Phase 0 — Foundations** | Repo setup, Docker Compose for local dev, PostgreSQL + Redis provisioning, base FastAPI app skeleton with Clean Architecture layers, Alembic setup | Running local environment, empty but structured backend |
| **Phase 1 — Core Domain** | Implement Movie, Category, User, MandatoryChannel domain + application + infrastructure layers; core API endpoints for movies/categories | Backend can store and serve movie/category data |
| **Phase 2 — Telegram Bot MVP** | Onboarding, registration, subscription gate, search by code/title, categories, movie delivery, profile | Bot can register users and deliver movies end-to-end |
| **Phase 3 — Website MVP** | Homepage, search, movie details page, SEO essentials (metadata, sitemap, structured data) | Public-facing catalog live, linking to the bot |
| **Phase 4 — Admin Panel MVP** | Auth, dashboard, movie/category/channel CRUD, broadcast composer, basic statistics, settings | Team can manage content and communicate with users without engineering support |
| **Phase 5 — Broadcast & Statistics Hardening** | Queue-based broadcast delivery, statistics aggregation jobs, rate-limit safety | Reliable, scalable messaging and reporting |
| **Phase 6 — QA, Security Review & Launch Prep** | End-to-end testing, security review (Section 15), performance testing, deployment pipeline finalization | Production-ready MVP |
| **Phase 7 — Launch & Monitoring** | Production deployment, monitoring/alerting active, initial social traffic onboarding | Kinochi live and measurable |

---

*End of document. This PRD defines the complete MVP scope and architecture for Kinochi. Implementation should proceed phase by phase as outlined in Section 20, with architectural boundaries from Section 8 strictly respected to preserve the system's extensibility for the roadmap in Section 17.*
