"""Tests for raise_on_access=True behavior of DeprecatedColumn.

When raise_on_access is True, using a deprecated column in an expression raises
ColumnDeprecatedError instead of emitting a DeprecationWarning.
"""

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, insert, select, update

from sqlalchemy_deprecated_column import ColumnDeprecatedError, DeprecatedColumn


@pytest.fixture
def table(engine):
    metadata = MetaData()
    t = Table(
        "my_model",
        metadata,
        Column("id", Integer, primary_key=True),
        DeprecatedColumn("old_field", String, raise_on_access=True),
    )
    metadata.create_all(engine)
    return t


class TestRaiseOnAccess:
    """raise_on_access=True raises ColumnDeprecatedError instead of warning."""

    def test_no_raise_when_defining_table(self):
        """No error fires during Table(...) construction."""
        metadata = MetaData()
        Table(
            "my_model",
            metadata,
            Column("id", Integer, primary_key=True),
            DeprecatedColumn("old_field", String, raise_on_access=True),
        )

    def test_select_column_raises(self, table):
        with pytest.raises(
            ColumnDeprecatedError,
            match="reading deprecated column my_model.old_field",
        ):
            select(table.c.old_field).compile()

    def test_where_clause_raises(self, table):
        with pytest.raises(
            ColumnDeprecatedError,
            match="referencing deprecated column my_model.old_field",
        ):
            select(table).where(table.c.old_field == "alice")

    def test_expression_raises(self, table):
        with pytest.raises(
            ColumnDeprecatedError,
            match="referencing deprecated column my_model.old_field",
        ):
            select(table).where(table.c.old_field.is_(None))

    def test_insert_raises(self, table):
        with pytest.raises(
            ColumnDeprecatedError,
            match="writing to deprecated column my_model.old_field",
        ):
            insert(table).values(old_field="test").compile()

    def test_update_raises(self, table):
        with pytest.raises(
            ColumnDeprecatedError,
            match="writing to deprecated column my_model.old_field",
        ):
            update(table).values(old_field="test").compile()
