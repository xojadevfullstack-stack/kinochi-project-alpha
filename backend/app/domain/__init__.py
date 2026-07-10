"""
Domain Layer — pure business entities, value objects, and domain rules.

This is the innermost layer of Clean Architecture.  Code here has
ZERO framework dependencies (no FastAPI, no SQLAlchemy, no Redis).
Each sub-package corresponds to a bounded context / aggregate root.

Sub-packages (populated in Phase 1):
  - movies/       Movie entity, value objects (MovieCode, Rating)
  - categories/   Category entity
  - users/        User entity (Telegram user)
  - channels/     MandatoryChannel entity
  - broadcasts/   Broadcast entity
"""
