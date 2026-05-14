"""Tests for SQLAlchemy Core SQL behavior of DeprecatedColumn.

Verifies that deprecated columns never appear in generated SELECT, WHERE,
or INSERT statements and that NULL is substituted when they are referenced explicitly.
"""

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, select, update

from sqlalchemy_deprecated_column import DeprecatedColumn


@pytest.fixture
def table(engine):
    metadata = MetaData()
    t = Table(
        "my_model",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String),
        DeprecatedColumn("deprecated_name", String),
    )
    metadata.create_all(engine)
    return t


class TestSqlOutput:
    """Deprecated columns never appear in generated SQL output."""

    def test_deprecated_column_absent_from_select_sql(self, table, conn, capsql):
        conn.execute(select(table))

        [sql] = capsql.records
        assert "deprecated_name" not in sql

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_null_substituted_when_column_selected_directly(self, table, conn, capsql):
        """NULL is rendered in the SELECT clause instead of the deprecated column data."""
        conn.execute(select(table.c.deprecated_name))

        [sql] = capsql.records
        assert "NULL" in sql
        assert "my_model.deprecated_name" not in sql

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_deprecated_column_absent_from_where_clause(self, table, conn, capsql):
        """NULL is rendered in the WHERE clause instead of the deprecated column name."""
        conn.execute(select(table).where(table.c.deprecated_name == "alice"))

        [sql] = capsql.records
        assert "deprecated_name" not in sql

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_deprecated_column_supports_sql_expressions(self, table, conn, capsql):
        """Callers can use .is_(None) on a deprecated column without a runtime error."""
        conn.execute(select(table).where(table.c.deprecated_name.is_(None)))

        [sql] = capsql.records
        assert "deprecated_name" not in sql

    def test_deprecated_column_absent_from_auto_insert_sql(self, table, conn, capsql):
        """Auto-INSERT never includes the deprecated column."""
        conn.execute(table.insert().values(name="alice"))

        [sql] = capsql.records
        assert "deprecated_name" not in sql

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_null_substituted_when_column_written_explicitly_in_insert(self, table, conn, capsql):
        """NULL is written to the deprecated column instead of the user-supplied value."""
        conn.execute(table.insert().values(deprecated_name="test-value"))

        [sql] = capsql.records
        assert "NULL" in sql
        assert "test-value" not in sql

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_null_substituted_when_column_written_explicitly_in_update(self, table, conn, capsql):
        """NULL is written to the deprecated column instead of the user-supplied value."""
        conn.execute(update(table).values(deprecated_name="test-value"))

        [sql] = capsql.records
        assert "NULL" in sql
        assert "test-value" not in sql
