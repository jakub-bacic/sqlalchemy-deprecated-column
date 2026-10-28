from __future__ import annotations

import warnings
from typing import Any

from sqlalchemy import Column
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.compiler import SQLCompiler

from ._shared import ColumnDeprecatedError, config, find_stack_level


class DeprecatedColumn(Column[Any]):
    """Drop-in replacement for Column() inside Core Table definitions.

    In normal mode, the column is omitted from statements that SQLAlchemy
    generates from the whole table (e.g. ``select(table)``, INSERT without
    explicit values, ``returning(table)``), including aliases, subqueries and
    CTEs built from them. Any explicit reference (e.g. ``table.c.old_field``
    in SELECT, WHERE or ORDER BY) emits a DeprecationWarning when the
    statement is compiled; the query still uses the real column. Indexes and
    constraints defined on the column do not count as references. Python-side
    ``default``, ``insert_default`` and ``onupdate`` are ignored.

    In Alembic mode (after configure(alembic_mode=True)), returns a plain nullable
    Column so Alembic generates correct migrations.

    Pass raise_on_access=True to raise ColumnDeprecatedError instead of warning.
    """

    # Disables SQL caching for statements that explicitly reference the column,
    # so the warning is emitted on every execution, not only the first.
    inherit_cache = False

    def __new__(cls, *args: Any, raise_on_access: bool = False, **kwargs: Any) -> Column[Any]:
        # SQLAlchemy also calls this for alias and subquery proxies, so
        # configure() must run before any table is used, not only defined.
        if config.alembic_mode:
            kwargs["nullable"] = True
            return Column(*args, **kwargs)
        return super().__new__(cls)

    def __init__(self, *args: Any, raise_on_access: bool = False, **kwargs: Any) -> None:
        self._raise_on_access = raise_on_access
        kwargs["nullable"] = True
        # Older SQLAlchemy versions do not accept `insert_default`; it is
        # dropped together with the other Python-side defaults below.
        kwargs.pop("insert_default", None)
        # Set on every instance, including the proxies SQLAlchemy builds through
        # this class for aliases and subqueries, so they are omitted as well.
        kwargs["_omit_from_statements"] = True
        super().__init__(*args, **kwargs)
        # Python-side defaults would add the column back into generated INSERT
        # and UPDATE statements. Cleared after init, as they can also be passed
        # positionally (e.g. `ColumnDefault(...)`).
        self.default = None
        self.onupdate = None

    def _emit(self) -> None:
        # Proxies (e.g. alias.c.old_field) report the original Table column.
        origin = next(
            (c for c in self.base_columns if isinstance(c, DeprecatedColumn)),
            self,
        )
        msg = f"referencing deprecated column {origin.table.name}.{origin.name}"
        if origin._raise_on_access:
            raise ColumnDeprecatedError(msg)
        warnings.warn(msg, DeprecationWarning, stacklevel=find_stack_level())


@compiles(DeprecatedColumn)
def compile_deprecated_column(element: DeprecatedColumn, compiler: SQLCompiler, **kw: Any) -> str:
    # DDL (e.g. CREATE INDEX) renders column expressions through a compiler that
    # has no statement; creating the schema is not a reference to the column.
    if compiler.statement is not None:
        element._emit()  # pyright: ignore[reportPrivateUsage]
    return compiler.visit_column(element, **kw)
