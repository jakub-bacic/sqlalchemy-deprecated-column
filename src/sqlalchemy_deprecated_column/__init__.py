"""Safely remove SQLAlchemy ORM columns through a gradual deprecation process."""

from .deprecated_column import configure, deprecated_column

__all__ = ["configure", "deprecated_column"]
