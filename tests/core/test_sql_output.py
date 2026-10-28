"""Tests for SQLAlchemy Core SQL behavior of DeprecatedColumn.

Verifies that deprecated columns are omitted from statements generated from the
whole table, and that explicit references render the real column unchanged.
"""

import pytest
from sqlalchemy import (
    Column,
    ColumnDefault,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    insert,
    select,
    union,
    update,
)
from sqlalchemy.exc import NoSuchColumnError

from sqlalchemy_deprecated_column import DeprecatedColumn


@pytest.fixture
def metadata():
    metadata = MetaData()
    Table(
        "my_model",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String),
        DeprecatedColumn("deprecated_name", String),
    )
    Table(
        "child",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("parent_id", ForeignKey("my_model.id")),
    )
    return metadata


@pytest.fixture
def table(metadata):
    return metadata.tables["my_model"]


@pytest.fixture(autouse=True)
def create_schema(engine, table):
    table.metadata.create_all(engine)


# Each case executes one statement generated from the whole table `t`.
GENERATED_STATEMENTS = [
    pytest.param(lambda conn, t: conn.execute(select(t)), id="select(table)"),
    pytest.param(lambda conn, t: conn.execute(t.select()), id="table.select()"),
    pytest.param(lambda conn, t: conn.execute(select(t.alias())), id="select(table.alias())"),
    pytest.param(lambda conn, t: conn.execute(select(select(t).subquery())), id="select(subquery)"),
    pytest.param(lambda conn, t: conn.execute(select(select(t).cte())), id="select(cte)"),
    pytest.param(lambda conn, t: conn.execute(select(select(t).exists())), id="select(exists)"),
    pytest.param(lambda conn, t: conn.execute(union(select(t), select(t))), id="union"),
    pytest.param(
        lambda conn, t: conn.execute(select(t.join(t.metadata.tables["child"]))), id="join"
    ),
    pytest.param(
        lambda conn, t: conn.execute(insert(t).values(name="alice")), id="insert().values()"
    ),
    pytest.param(
        lambda conn, t: conn.execute(insert(t), [{"name": "alice"}, {"name": "bob"}]),
        id="insert() executemany",
    ),
    pytest.param(
        lambda conn, t: conn.execute(insert(t).values(name="alice").returning(t)),
        id="insert().returning(table)",
    ),
    pytest.param(
        lambda conn, t: conn.execute(update(t).values(name="bob").returning(t)),
        id="update().returning(table)",
    ),
]


class TestOmittedFromGeneratedSql:
    """The deprecated column never appears in statements generated from the whole table."""

    @pytest.mark.parametrize("execute", GENERATED_STATEMENTS)
    def test_column_absent(self, table, conn, capsql, execute):
        execute(conn, table)

        [sql] = capsql.records
        assert "deprecated_name" not in sql


class TestPythonSideDefaults:
    """Python-side defaults are ignored, so they cannot add the column back to INSERT/UPDATE."""

    # Each case builds the deprecated column with an INSERT and an UPDATE default.
    @pytest.fixture(
        params=[
            pytest.param(
                lambda: DeprecatedColumn(
                    "deprecated_name", String, default="default-value", onupdate="onupdate-value"
                ),
                id="default=",
            ),
            pytest.param(
                lambda: DeprecatedColumn(
                    "deprecated_name",
                    String,
                    insert_default="default-value",
                    onupdate="onupdate-value",
                ),
                id="insert_default=",
            ),
            pytest.param(
                # SQLAlchemy types ColumnDefault by its __init__ (`for_update` only),
                # although `arg` is accepted positionally by __new__.
                lambda: DeprecatedColumn(
                    "deprecated_name",
                    String,
                    ColumnDefault("default-value"),  # pyright: ignore[reportArgumentType]
                    ColumnDefault("onupdate-value", for_update=True),  # pyright: ignore[reportCallIssue]
                ),
                id="positional ColumnDefault",
            ),
        ]
    )
    def table(self, request):
        return Table(
            "my_model",
            MetaData(),
            Column("id", Integer, primary_key=True),
            Column("name", String),
            request.param(),
        )

    def test_column_absent_from_insert(self, table, conn, capsql):
        conn.execute(insert(table).values(name="alice"))

        [sql] = capsql.records
        assert "deprecated_name" not in sql

    def test_column_absent_from_update(self, table, conn, capsql):
        conn.execute(update(table).values(name="bob"))

        [sql] = capsql.records
        assert "deprecated_name" not in sql


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestExplicitReference:
    """Explicit references render the real column — the SQL is not rewritten."""

    def test_column_rendered_when_selected_directly(self, table, conn, capsql):
        conn.execute(select(table.c.deprecated_name))

        [sql] = capsql.records
        assert "my_model.deprecated_name" in sql

    def test_column_rendered_in_where_clause(self, table, conn, capsql):
        conn.execute(select(table).where(table.c.deprecated_name == "alice"))

        [sql] = capsql.records
        assert "WHERE my_model.deprecated_name = ?" in sql

    def test_value_written_when_column_written_explicitly_in_insert(self, table, conn):
        conn.execute(insert(table).values(id=1, deprecated_name="test-value"))

        stored = conn.execute(select(table.c.deprecated_name)).scalar_one()
        assert stored == "test-value"

    def test_value_written_when_column_written_explicitly_in_update(self, table, conn):
        conn.execute(insert(table).values(id=1))
        conn.execute(update(table).values(deprecated_name="updated-value"))

        stored = conn.execute(select(table.c.deprecated_name)).scalar_one()
        assert stored == "updated-value"


class TestResultRow:
    """Result rows of statements generated from the whole table."""

    def test_row_has_no_deprecated_column_attribute(self, table, conn):
        """Limitation: row.deprecated_name raises AttributeError after select(table)."""
        conn.execute(insert(table).values(name="alice"))

        row = conn.execute(select(table)).one()

        assert list(row._mapping) == ["id", "name"]
        with pytest.raises(AttributeError):
            _ = row.deprecated_name

    def test_row_mapping_has_no_deprecated_column_key(self, table, conn):
        """Limitation: row._mapping["deprecated_name"] raises NoSuchColumnError."""
        conn.execute(insert(table).values(name="alice"))

        row = conn.execute(select(table)).one()

        with pytest.raises(NoSuchColumnError):
            _ = row._mapping["deprecated_name"]


class TestAfterColumnDropped:
    """Statements generated from the whole table keep working once the column is dropped."""

    @pytest.fixture(autouse=True)
    def create_schema(self, engine, table):
        """The code still declares the column, but the database no longer has it."""
        table.metadata.create_all(engine)
        with engine.begin() as conn:
            conn.exec_driver_sql("ALTER TABLE my_model DROP COLUMN deprecated_name")

    @pytest.mark.parametrize("execute", GENERATED_STATEMENTS)
    def test_statement_succeeds(self, table, conn, execute):
        execute(conn, table)
