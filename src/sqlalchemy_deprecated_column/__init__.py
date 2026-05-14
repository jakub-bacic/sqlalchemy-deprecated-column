"""Safely remove SQLAlchemy columns through a gradual deprecation process."""

from ._core import DeprecatedColumn
from ._orm import deprecated_column
from ._shared import ColumnDeprecatedError, configure

__all__ = [
    "ColumnDeprecatedError",
    "DeprecatedColumn",
    "configure",
    "deprecated_column",
]
