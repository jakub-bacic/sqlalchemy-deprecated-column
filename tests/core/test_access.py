"""Tests for warning behavior when a deprecated column is referenced in queries.

Covers table construction (no warning) and query construction (warning emitted
with correct message and caller filename) — grouped by the SQL context in which
the column is referenced.
"""

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, insert, select, update

from sqlalchemy_deprecated_column import DeprecatedColumn


@pytest.fixture
def table():
    metadata = MetaData()
    return Table(
        "my_model",
        metadata,
        Column("id", Integer, primary_key=True),
        DeprecatedColumn("old_field", String),
    )


class TestSelectClause:
    """Referencing the column directly in a SELECT clause."""

    def test_emits_deprecation_warning(self, table):
        with pytest.warns(DeprecationWarning) as record:
            select(table.c.old_field).compile()

        (warning,) = record
        assert str(warning.message) == "reading deprecated column my_model.old_field"
        assert warning.filename == __file__

    def test_emits_deprecation_warning_when_labeled(self, table):
        with pytest.warns(DeprecationWarning) as record:
            select(table.c.old_field.label("alias")).compile()

        (warning,) = record
        assert str(warning.message) == "reading deprecated column my_model.old_field"
        assert warning.filename == __file__


class TestWhereClause:
    """Referencing the column in a WHERE clause."""

    def test_emits_deprecation_warning(self, table):
        with pytest.warns(DeprecationWarning) as record:
            select(table).where(table.c.old_field == "value")

        (warning,) = record
        assert str(warning.message) == "referencing deprecated column my_model.old_field"
        assert warning.filename == __file__

    def test_emits_deprecation_warning_when_column_is_right_operand(self, table):
        with pytest.warns(DeprecationWarning) as record:
            select(table).where("prefix-" + table.c.old_field == "value")

        (warning,) = record
        assert str(warning.message) == "referencing deprecated column my_model.old_field"
        assert warning.filename == __file__

    def test_emits_deprecation_warning_when_column_is_labeled(self, table):
        labeled = table.c.old_field.label("alias")
        with pytest.warns(DeprecationWarning) as record:
            select(table).where(labeled == "value")

        (warning,) = record
        assert str(warning.message) == "referencing deprecated column my_model.old_field"
        assert warning.filename == __file__


class TestInsertStatement:
    """Referencing the column explicitly in an INSERT statement."""

    def test_emits_deprecation_warning(self, table):
        with pytest.warns(DeprecationWarning) as record:
            insert(table).values(old_field="test").compile()

        (warning,) = record
        assert str(warning.message) == "writing to deprecated column my_model.old_field"
        assert warning.filename == __file__


class TestUpdateStatement:
    """Referencing the column explicitly in an UPDATE statement."""

    def test_emits_deprecation_warning(self, table):
        with pytest.warns(DeprecationWarning) as record:
            update(table).values(old_field="test").compile()

        (warning,) = record
        assert str(warning.message) == "writing to deprecated column my_model.old_field"
        assert warning.filename == __file__


class TestTableDefinition:
    """Table construction does not trigger deprecation warnings."""

    def test_no_warning_when_defining_table(self, recwarn):
        metadata = MetaData()
        Table(
            "my_model",
            metadata,
            Column("id", Integer, primary_key=True),
            DeprecatedColumn("old_field", String),
        )
        assert not recwarn.list
