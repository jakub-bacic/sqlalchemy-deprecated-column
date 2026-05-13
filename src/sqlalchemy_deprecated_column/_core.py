from __future__ import annotations

import warnings
import weakref
from typing import Any, cast

from sqlalchemy import Column, null
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.sql.type_api import TypeDecorator

from ._shared import ColumnDeprecatedError, config, find_stack_level


class _DeprecatedTypeWrapper(TypeDecorator[Any]):
    """Substitutes NULL and emits a deprecation warning on any read, write, or expression use."""

    impl = NullType  # required class-level declaration; overridden per-instance in __init__
    cache_ok = False

    def __init__(self, column: DeprecatedColumn) -> None:
        super().__init__()
        self.impl = column.type
        self._column_ref: weakref.ref[DeprecatedColumn] = weakref.ref(column)

    @property
    def column(self) -> DeprecatedColumn:
        col = self._column_ref()
        assert col is not None
        return col

    def column_expression(self, column: Any) -> Any:
        self.column.emit("reading")
        return null()

    def bind_expression(self, bindparam: Any) -> Any:
        self.column.emit("writing to")
        return null()

    class comparator_factory(TypeDecorator.Comparator[Any]):  # type: ignore[reportIncompatibleMethodOverride]
        def emit(self) -> None:
            cast(_DeprecatedTypeWrapper, self.type).column.emit()

        def operate(self, op: Any, *other: Any, **kwargs: Any) -> Any:
            self.emit()
            return null().comparator.operate(op, *other, **kwargs)

        def reverse_operate(self, op: Any, other: Any, **kwargs: Any) -> Any:
            self.emit()
            return null().comparator.reverse_operate(op, other, **kwargs)


class DeprecatedColumn(Column[Any]):
    """Drop-in replacement for Column() inside Core Table definitions.

    In normal mode, the column is excluded from auto-generated SELECT statements
    and any explicit reference emits a DeprecationWarning with
    NULL substituted in the SQL.

    In Alembic mode (after configure(alembic_mode=True)), returns a plain nullable
    Column so Alembic generates correct migrations.

    Pass raise_on_access=True to raise ColumnDeprecatedError instead of warning.
    """

    inherit_cache = False

    def __new__(cls, *args: Any, raise_on_access: bool = False, **kwargs: Any) -> Column[Any]:
        if config.alembic_mode:
            kwargs["nullable"] = True
            return Column(*args, **kwargs)
        return super().__new__(cls)

    def __init__(self, *args: Any, raise_on_access: bool = False, **kwargs: Any) -> None:
        self._raise_on_access = raise_on_access
        kwargs["nullable"] = True
        super().__init__(*args, **kwargs)
        self._omit_from_statements = True
        self.type = _DeprecatedTypeWrapper(self)

    def emit(self, verb: str = "referencing") -> None:
        msg = f"{verb} deprecated column {self.table.name}.{self.name}"
        if self._raise_on_access:
            raise ColumnDeprecatedError(msg)
        warnings.warn(msg, DeprecationWarning, stacklevel=find_stack_level())
