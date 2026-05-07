from __future__ import annotations

import sys
import warnings
from dataclasses import dataclass
from typing import Any

from sqlalchemy import null
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column


@dataclass
class _Configuration:
    alembic_mode: bool = False


_config = _Configuration()


_INTERNAL_PREFIXES = (
    "sqlalchemy",
    "sqlalchemy_deprecated_column",
)


def _is_internal(module_name: str) -> bool:
    return any(
        module_name == prefix or module_name.startswith(prefix + ".")
        for prefix in _INTERNAL_PREFIXES
    )


def _find_stack_level() -> int:
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


class _DeprecatedColumn:
    def __init__(self, *_args: Any, raise_on_access: bool = False, **_kwargs: Any) -> None:
        self._raise_on_access = raise_on_access

    def __set_name__(self, owner: type, name: str) -> None:
        raise_on_access = self._raise_on_access

        def _emit(msg: str) -> None:
            if raise_on_access:
                raise ColumnDeprecatedError(msg)
            warnings.warn(msg, DeprecationWarning, stacklevel=_find_stack_level())

        @hybrid_property
        def prop(instance: Any) -> None:
            _emit(f"accessing deprecated field {type(instance).__name__}.{name}")
            return None

        @prop.inplace.setter
        def _(instance: Any, value: Any) -> None:
            _emit(f"writing to deprecated field {type(instance).__name__}.{name}")

        @prop.inplace.expression
        @classmethod
        def _(cls: type) -> Any:
            _emit(f"referencing deprecated class field {cls.__name__}.{name}")
            return null()

        setattr(owner, name, prop)


def configure(*, alembic_mode: bool = False) -> None:
    """Configure sqlalchemy-deprecated-column behaviour.

    Call with ``alembic_mode=True`` at the top of ``alembic/env.py``, before
    any model imports, so that Alembic sees deprecated columns as real nullable
    columns and does not generate DROP COLUMN migrations.
    """
    _config.alembic_mode = alembic_mode


def deprecated_column(*args: Any, raise_on_access: bool = False, **kwargs: Any) -> Any:
    """Drop-in replacement for mapped_column() that marks the column as deprecated.

    In normal mode the column is excluded from the ORM mapper entirely:
    it will not appear in SELECT, INSERT, UPDATE, or RETURNING statements.
    Instance reads return None and emit a DeprecationWarning; writes emit a
    warning and are silently discarded.

    Pass ``raise_on_access=True`` to raise ``ColumnDeprecatedError`` on any
    access instead of emitting a warning.

    In Alembic mode (after ``configure(alembic_mode=True)``) the call is
    forwarded to ``mapped_column(*args, nullable=True, **kwargs)`` so that
    Alembic sees the column as a regular nullable column and generates correct
    migrations.

    Usage::

        class User(Base):
            __tablename__ = "users"
            id: Mapped[int] = mapped_column(primary_key=True)
            old_email: Mapped[str] = deprecated_column(String(200))
            removed_field: Mapped[str] = deprecated_column(String(200), raise_on_access=True)
    """
    if _config.alembic_mode:
        kwargs["nullable"] = True
        return mapped_column(*args, **kwargs)
    return _DeprecatedColumn(*args, raise_on_access=raise_on_access, **kwargs)
