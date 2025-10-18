"""Domain entities package.

Contains rich domain entities (aggregate roots) that encapsulate
business logic and emit domain events.
"""

from app.domain.entities.user import User

__all__ = ["User"]
