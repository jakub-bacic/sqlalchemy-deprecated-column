"""Tests for Alembic migration diffs produced by DeprecatedColumn in Core tables.

Each test defines Before and After metadata (current DB state vs code after
deprecation) and asserts on the ops that Alembic's compare_metadata generates.
"""

from sqlalchemy import Column, Integer, MetaData, String, Table

from sqlalchemy_deprecated_column import DeprecatedColumn


class TestMigrationDiff:
    """Alembic compare_metadata produces correct diffs for DeprecatedColumn in Core tables."""

    def test_no_migration_when_db_has_deprecated_column(self, diff_schemas):
        """No migration ops are generated when the DB column is already nullable."""
        before_metadata = MetaData()
        Table(
            "my_model",
            before_metadata,
            Column("id", Integer, primary_key=True),
            Column("old_field", String, nullable=True),
        )

        after_metadata = MetaData()
        Table(
            "my_model",
            after_metadata,
            Column("id", Integer, primary_key=True),
            DeprecatedColumn("old_field", String, nullable=True),
        )

        ops = diff_schemas(before_metadata, after_metadata)
        assert ops == []

    def test_drop_not_null_generated_for_non_null_deprecated_column(self, diff_schemas):
        """A DROP NOT NULL migration is generated when the DB column is NOT NULL.

        Deprecating a non-nullable column requires making it nullable first so
        existing rows aren't affected when the column is eventually dropped.
        """
        before_metadata = MetaData()
        Table(
            "my_model",
            before_metadata,
            Column("id", Integer, primary_key=True),
            Column("old_field", String, nullable=False),
        )

        after_metadata = MetaData()
        Table(
            "my_model",
            after_metadata,
            Column("id", Integer, primary_key=True),
            DeprecatedColumn("old_field", String, nullable=False),
        )

        ops = diff_schemas(before_metadata, after_metadata)
        assert len(ops) == 1

        op, schema, table, column, _, was_nullable, becomes_nullable = ops[0]
        assert op == "modify_nullable"
        assert table == "my_model"
        assert column == "old_field"
        assert was_nullable is False
        assert becomes_nullable is True

    def test_extra_arguments_are_forwarded(self, diff_schemas):
        """Extra arguments (e.g. index=True) are forwarded so no spurious ops are generated."""
        before_metadata = MetaData()
        Table(
            "my_model",
            before_metadata,
            Column("id", Integer, primary_key=True),
            Column("old_field", String, nullable=False, index=True),
        )

        after_metadata = MetaData()
        Table(
            "my_model",
            after_metadata,
            Column("id", Integer, primary_key=True),
            DeprecatedColumn("old_field", String, nullable=False, index=True),
        )

        ops = diff_schemas(before_metadata, after_metadata)
        assert len(ops) == 1

        op, schema, table, column, _, was_nullable, becomes_nullable = ops[0]
        assert op == "modify_nullable"
        assert was_nullable is False
        assert becomes_nullable is True
