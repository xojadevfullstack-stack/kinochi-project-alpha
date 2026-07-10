"""
Application Layer — use cases, service orchestration, DTOs.

This layer sits between Domain and Infrastructure in Clean Architecture.
It depends on the Domain layer (entities, repository interfaces) but
NEVER on Infrastructure (no SQLAlchemy, no HTTP clients, no Redis here).
Dependencies are injected at runtime.

Sub-packages (populated in Phase 1+):
  - movies/       MovieService — CRUD orchestration, search
  - categories/   CategoryService
  - users/        UserService — registration, profile
  - channels/     ChannelService — mandatory subscription management
  - broadcasts/   BroadcastService — compose, schedule, deliver
  - statistics/   StatisticsService — aggregation queries
"""
