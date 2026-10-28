"""Tests for warning behavior when a deprecated column is referenced in queries.

Explicit references emit a DeprecationWarning when the statement is compiled
(or executed) — grouped by the SQL context in which the column is referenced.
Statements that only reference the whole table, and explicit writes via
``.values()``, do not warn.
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

from sqlalchemy_deprecated_column import DeprecatedColumn

MESSAGE = "referencing deprecated column my_model.old_field"


@pytest.fixture
def table():
    metadata = MetaData()
    return Table(
        "my_model",
        metadata,
        Column("id", Integer, primary_key=True),
        DeprecatedColumn("old_field", String),
    )


def assert_single_warning(record):
    (warning,) = record
    assert str(warning.message) == MESSAGE
    assert warning.filename == __file__


class TestSelectClause:
    """Referencing the column directly in a SELECT clause."""

    def test_emits_deprecation_warning(self, table):
        with pytest.warns(DeprecationWarning) as record:
            select(table.c.old_field).compile()

        assert_single_warning(record)

    def test_emits_deprecation_warning_when_labeled(self, table):
        with pytest.warns(DeprecationWarning) as record:
            select(table.c.old_field.label("alias")).compile()

        assert_single_warning(record)

    def test_emits_deprecation_warning_when_used_in_function(self, table):
        with pytest.warns(DeprecationWarning) as record:
            select(func.coalesce(table.c.old_field, "default")).compile()

        assert_single_warning(record)

    def test_emits_deprecation_warning_when_selected_from_alias(self, table):
        """The message names the original table, not the anonymous alias."""
        aliased = table.alias()
        with pytest.warns(DeprecationWarning) as record:
            select(aliased.c.old_field).compile()

        assert_single_warning(record)


class TestWhereClause:
    """Referencing the column in a WHERE clause."""

    def test_no_warning_until_compiled(self, table, recwarn):
        select(table).where(table.c.old_field == "value")

        assert not recwarn.list

    def test_emits_deprecation_warning(self, table):
        with pytest.warns(DeprecationWarning) as record:
            select(table).where(table.c.old_field == "value").compile()

        assert_single_warning(record)

    def test_emits_deprecation_warning_when_column_is_right_operand(self, table):
        with pytest.warns(DeprecationWarning) as record:
            select(table).where("prefix-" + table.c.old_field == "value").compile()

        assert_single_warning(record)


class TestOrderByClause:
    """Referencing the column in an ORDER BY clause."""

    def test_emits_deprecation_warning(self, table):
        with pytest.warns(DeprecationWarning) as record:
            select(table).order_by(table.c.old_field).compile()

        assert_single_warning(record)


class TestExecution:
    """Warnings are emitted on execution, not only on explicit compile()."""

    @pytest.fixture(autouse=True)
    def create_schema(self, engine, table):
        table.metadata.create_all(engine)

    def test_emits_deprecation_warning_on_every_execution(self, table, conn):
        """Statements referencing the column bypass the SQL cache, so the warning repeats."""
        stmt = select(table.c.old_field)

        for _ in range(2):
            with pytest.warns(DeprecationWarning) as record:
                conn.execute(stmt)

            assert_single_warning(record)


class TestWithoutWarning:
    """Statements that do not warn."""

    def test_no_warning_when_defining_table(self, recwarn):
        metadata = MetaData()
        Table(
            "my_model",
            metadata,
            Column("id", Integer, primary_key=True),
            DeprecatedColumn("old_field", String),
        )
        assert not recwarn.list

    def test_no_warning_when_creating_indexes(self, engine, recwarn):
        """Index DDL renders the column, but creating the schema is not a reference."""
        metadata = MetaData()
        table = Table(
            "my_model",
            metadata,
            Column("id", Integer, primary_key=True),
            DeprecatedColumn("old_field", String, index=True),
        )
        Index("ix_my_model_lower_old_field", func.lower(table.c.old_field))

        metadata.create_all(engine)

        assert not recwarn.list

    def test_no_warning_when_selecting_whole_table(self, table, recwarn):
        select(table).compile()

        assert not recwarn.list

    def test_no_warning_when_writing_in_insert(self, table, recwarn):
        """Limitation: column names in INSERT/UPDATE are not intercepted."""
        insert(table).values(old_field="test").compile()

        assert not recwarn.list

    def test_no_warning_when_writing_in_update(self, table, recwarn):
        """Limitation: column names in INSERT/UPDATE are not intercepted."""
        update(table).values(old_field="test").compile()

        assert not recwarn.list
