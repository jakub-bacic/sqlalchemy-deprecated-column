from __future__ import annotations

import sys
from dataclasses import dataclass


@dataclass
class _Configuration:
    alembic_mode: bool = False


config = _Configuration()


_INTERNAL_PREFIXES = (
    "sqlalchemy",
    "sqlalchemy_deprecated_column",
)


def _is_internal(module_name: str) -> bool:
    return any(
        module_name == prefix or module_name.startswith(prefix + ".")
        for prefix in _INTERNAL_PREFIXES
    )


def find_stack_level() -> int:
    frame = sys._getframe(1)  # type: ignore[attr-defined]
    level = 1

    while frame:
        module_name = frame.f_globals.get("__name__", "")

        if not _is_internal(module_name):
            return level

        frame = frame.f_back
        level += 1

    return level  # pragma: no cover


class ColumnDeprecatedError(Exception):
    pass


def configure(*, alembic_mode: bool = False) -> None:
    """Configure sqlalchemy-deprecated-column behavior.

    Call with ``alembic_mode=True`` at the top of ``alembic/env.py``, before
    any model imports, so that Alembic sees deprecated columns as real nullable
    columns and does not generate DROP COLUMN migrations.
    """
    config.alembic_mode = alembic_mode
