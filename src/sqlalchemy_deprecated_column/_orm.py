from __future__ import annotations

import warnings
from typing import Any

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql.compiler import SQLCompiler
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.types import NullType

from ._shared import ColumnDeprecatedError, config, find_stack_level


class _ClassReference(ColumnElement[Any]):
    """SQL expression returned by a class-level reference (e.g. ``User.old_field``)."""

    # Disables SQL caching, so every execution compiles the statement and raises.
    inherit_cache = False
    type = NullType()

    def __init__(self, message: str) -> None:
        self.message = message


@compiles(_ClassReference)
def compile_class_reference(element: _ClassReference, compiler: SQLCompiler, **kw: Any) -> str:
    # The column is not mapped, so there is no correct SQL to render. Raising
    # keeps statements such as `delete(User).where(User.old_field.is_(None))`
    # from running with a wrong condition.
    raise ColumnDeprecatedError(element.message)


class _DeprecatedColumn:
    def __init__(self, *_args: Any, raise_on_access: bool = False, **_kwargs: Any) -> None:
        self._raise_on_access = raise_on_access

    def __set_name__(self, owner: type, name: str) -> None:
        raise_on_access = self._raise_on_access

        def _emit(msg: str) -> None:
            if raise_on_access:
                raise ColumnDeprecatedError(msg)
            warnings.warn(msg, DeprecationWarning, stacklevel=find_stack_level())

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
            # Raises only when a statement that uses it is compiled: declarative,
            # dataclasses and the model constructor also read the attribute.
            return _ClassReference(f"referencing deprecated class field {cls.__name__}.{name}")

        setattr(owner, name, prop)


def deprecated_column(*args: Any, raise_on_access: bool = False, **kwargs: Any) -> Any:
    """Drop-in replacement for mapped_column() that marks the column as deprecated.

    In normal mode the column is excluded from the ORM mapper entirely:
    it will not appear in SELECT, INSERT, UPDATE, or RETURNING statements.
    Instance reads return None and emit a DeprecationWarning; writes emit a
    warning and are silently discarded. A statement that uses a class-level
    reference (e.g. ``User.old_email == "x"``) raises ``ColumnDeprecatedError``
    when it is compiled or executed.

    Pass ``raise_on_access=True`` to raise ``ColumnDeprecatedError`` on
    instance reads and writes instead of emitting a warning.

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
    if config.alembic_mode:
        kwargs["nullable"] = True
        return mapped_column(*args, **kwargs)
    return _DeprecatedColumn(*args, raise_on_access=raise_on_access, **kwargs)
