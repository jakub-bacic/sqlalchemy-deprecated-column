"""Tests for raise_on_access=True behavior of DeprecatedColumn.

Mirrors test_access.py: every explicit reference that would emit a DeprecationWarning
raises ColumnDeprecatedError instead — grouped by the SQL context in which the column
is referenced. Statements that only reference the whole table, and explicit writes
via ``.values()``, do not raise.
"""

import pytest
from sqlalchemy import (
    Column,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    func,
    insert,
    select,
    update,
)

from sqlalchemy_deprecated_column import ColumnDeprecatedError, DeprecatedColumn

MESSAGE = "referencing deprecated column my_model.old_field"


@pytest.fixture
def table():
    metadata = MetaData()
    return Table(
        "my_model",
        metadata,
        Column("id", Integer, primary_key=True),
        DeprecatedColumn("old_field", String, raise_on_access=True),
    )


class TestSelectClause:
    """Referencing the column directly in a SELECT clause."""

    def test_raises(self, table):
        with pytest.raises(ColumnDeprecatedError, match=MESSAGE):
            select(table.c.old_field).compile()

    def test_raises_when_labeled(self, table):
        with pytest.raises(ColumnDeprecatedError, match=MESSAGE):
            select(table.c.old_field.label("alias")).compile()

    def test_raises_when_used_in_function(self, table):
        with pytest.raises(ColumnDeprecatedError, match=MESSAGE):
            select(func.coalesce(table.c.old_field, "default")).compile()

    def test_raises_when_selected_from_alias(self, table):
        """The message names the original table, not the anonymous alias."""
        with pytest.raises(ColumnDeprecatedError, match=MESSAGE):
            select(table.alias().c.old_field).compile()


class TestWhereClause:
    """Referencing the column in a WHERE clause."""

    def test_no_raise_until_compiled(self, table):
        select(table).where(table.c.old_field == "value")

    def test_raises(self, table):
        with pytest.raises(ColumnDeprecatedError, match=MESSAGE):
            select(table).where(table.c.old_field == "value").compile()

    def test_raises_when_column_is_right_operand(self, table):
        with pytest.raises(ColumnDeprecatedError, match=MESSAGE):
            select(table).where("prefix-" + table.c.old_field == "value").compile()


class TestOrderByClause:
    """Referencing the column in an ORDER BY clause."""

    def test_raises(self, table):
        with pytest.raises(ColumnDeprecatedError, match=MESSAGE):
            select(table).order_by(table.c.old_field).compile()


class TestExecution:
    """Errors are raised on execution, not only on explicit compile()."""

    @pytest.fixture(autouse=True)
    def create_schema(self, engine, table):
        table.metadata.create_all(engine)

    def test_raises_on_every_execution(self, table, conn):
        """Statements referencing the column bypass the SQL cache, so the error repeats."""
        stmt = select(table.c.old_field)

        for _ in range(2):
            with pytest.raises(ColumnDeprecatedError, match=MESSAGE):
                conn.execute(stmt)


class TestWithoutRaising:
    """Statements that do not raise."""

    def test_no_raise_when_defining_table(self):
        Table(
            "my_model",
            MetaData(),
            Column("id", Integer, primary_key=True),
            DeprecatedColumn("old_field", String, raise_on_access=True),
        )

    def test_no_raise_when_creating_indexes(self, engine):
        """Index DDL renders the column, but creating the schema is not a reference."""
        metadata = MetaData()
        table = Table(
            "my_model",
            metadata,
            Column("id", Integer, primary_key=True),
            DeprecatedColumn("old_field", String, index=True, raise_on_access=True),
        )
        Index("ix_my_model_lower_old_field", func.lower(table.c.old_field))

        metadata.create_all(engine)

    def test_no_raise_when_selecting_whole_table(self, table):
        select(table).compile()

    def test_no_raise_when_writing_in_insert(self, table):
        """Limitation: column names in INSERT/UPDATE are not intercepted."""
        insert(table).values(old_field="test").compile()

    def test_no_raise_when_writing_in_update(self, table):
        """Limitation: column names in INSERT/UPDATE are not intercepted."""
        update(table).values(old_field="test").compile()
