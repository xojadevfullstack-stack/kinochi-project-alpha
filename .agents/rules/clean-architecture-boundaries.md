# Clean Architecture Boundaries — Always-On Rule

## Purpose
Enforce the layering rules defined in PRD §8.1 across the entire Kinochi
backend codebase.

## Dependency Direction (inward only)

```
Presentation (api/, bot handlers)
      │  depends on ↓
Application (use cases / services)
      │  depends on ↓
   Domain (entities, value objects, repository interfaces)
```

Infrastructure (db/, telegram/, cache/, external/) implements domain
interfaces but is **injected at runtime** — domain and application code
never import from infrastructure.

## Rules

1. **Domain Layer** (`app/domain/`)
   - ZERO framework imports (no FastAPI, SQLAlchemy, Redis, Pydantic, etc.).
   - Contains only: entities, value objects, domain exceptions, repository
     interface definitions (abstract base classes / Protocols).
   - May import from Python stdlib and from other domain sub-packages.

2. **Application Layer** (`app/application/`)
   - Depends on Domain (imports entities, repository interfaces).
   - NEVER imports from Infrastructure or API directly.
   - Receives infrastructure implementations via dependency injection.
   - Contains: use-case services, DTOs (Data Transfer Objects), application
     exceptions.

3. **Infrastructure Layer** (`app/infrastructure/`)
   - Implements repository interfaces from Domain using concrete tech
     (SQLAlchemy, Redis, httpx, etc.).
   - May import from Domain (to implement interfaces).
   - NEVER imported by Domain or Application at module level.

4. **API / Presentation Layer** (`app/api/`)
   - Depends on Application (calls services).
   - Wires together Infrastructure → Application via FastAPI dependency
     injection (`Depends()`).
   - Contains: routers, request/response Pydantic schemas, dependency
     providers.

5. **Core** (`app/core/`)
   - Cross-cutting: config, settings, logging, security utilities.
   - May be imported by any layer.
   - Never imports from domain, application, infrastructure, or api.

## What to watch for
- A domain entity importing `sqlalchemy` → ❌ violation.
- An application service importing a concrete repository class → ❌ violation;
  it should depend on the abstract interface.
- An API router containing business logic instead of delegating to a service
  → ❌ violation.
