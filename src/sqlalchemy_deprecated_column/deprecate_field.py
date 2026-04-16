from __future__ import annotations

import inspect
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


def _find_stack_level() -> int:
    """Return stacklevel for warnings.warn pointing at the first caller outside SQLAlchemy.

    Walks up the call stack from the warnings.warn call site, skipping all
    SQLAlchemy frames, so the warning always points at user code regardless of
    how many internal SQLAlchemy frames (e.g. __init__) sit in between.
    """
    frame = inspect.currentframe()
    if frame is not None:
        frame = frame.f_back  # skip this helper, land at the warnings.warn call site
    level = 1
    while frame is not None:
        frame = frame.f_back
        level += 1
        if frame is None:
            break
        if not frame.f_globals.get("__name__", "").startswith("sqlalchemy"):
            return level
    return level


def configure(alembic_mode: bool = False) -> None:
    """Configure sqlalchemy-deprecate-fields behaviour.

    Call with ``alembic_mode=True`` at the top of ``alembic/env.py``, before
    any model imports, so that Alembic sees deprecated columns as real nullable
    columns and does not generate DROP COLUMN migrations.
    """
    _config.alembic_mode = alembic_mode


class _DeprecatedColumn:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        pass

    def __set_name__(self, owner: type, name: str) -> None:
        @hybrid_property
        def prop(instance: Any) -> None:
            warnings.warn(
                f"accessing deprecated field {type(instance).__name__}.{name}",
                DeprecationWarning,
                stacklevel=_find_stack_level(),
            )
            return None

        @prop.inplace.setter
        def _(instance: Any, value: Any) -> None:
            warnings.warn(
                f"writing to deprecated field {type(instance).__name__}.{name}",
                DeprecationWarning,
                stacklevel=_find_stack_level(),
            )

        @prop.inplace.expression
        @classmethod
        def _(cls: type) -> Any:
            warnings.warn(
                f"referencing deprecated class field {cls.__name__}.{name}",
                DeprecationWarning,
                stacklevel=_find_stack_level(),
            )
            return null()

        setattr(owner, name, prop)


def deprecated_column(*args: Any, **kwargs: Any) -> Any:
    """Drop-in replacement for mapped_column() that marks the column as deprecated.

    In normal mode the column is excluded from the ORM mapper entirely:
    it will not appear in SELECT, INSERT, UPDATE, or RETURNING statements.
    Instance reads return None and emit a DeprecationWarning; writes emit a
    warning and are silently discarded.

    In Alembic mode (after ``configure(alembic_mode=True)``) the call is
    forwarded to ``mapped_column(*args, nullable=True, **kwargs)`` so that
    Alembic sees the column as a regular nullable column and generates correct
    migrations.

    Usage::

        class User(Base):
            __tablename__ = "users"
            id: Mapped[int] = mapped_column(primary_key=True)
            old_email: Mapped[str] = deprecated_column(String(200))
    """
    if _config.alembic_mode:
        kwargs["nullable"] = True
        return mapped_column(*args, **kwargs)
    return _DeprecatedColumn(*args, **kwargs)
