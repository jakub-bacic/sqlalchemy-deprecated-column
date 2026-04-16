from __future__ import annotations

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
                stacklevel=3,
            )
            return None

        @prop.inplace.setter
        def _(instance: Any, value: Any) -> None:
            warnings.warn(
                f"writing to deprecated field {type(instance).__name__}.{name}",
                DeprecationWarning,
                stacklevel=3,
            )

        @prop.inplace.expression
        @classmethod
        def _(cls: type) -> Any:
            warnings.warn(
                f"referencing deprecated class field {cls.__name__}.{name}",
                DeprecationWarning,
                stacklevel=5,
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
