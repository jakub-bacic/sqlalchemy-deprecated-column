"""Tests for Alembic migration diffs produced by deprecated_column().

Each test defines a Before model (current DB state) and an After model (code
after deprecation) and asserts on the ops that Alembic's compare_metadata
would generate.
"""

from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sqlalchemy_deprecated_column import deprecated_column


def diff_schemas(engine, before_metadata, after_metadata):
    """Create a DB from before_metadata and return flattened compare_metadata ops.

    compare_metadata returns a mixed structure: table-level ops are plain tuples
    at the top level, while column-level ops are grouped in inner lists per table:

        [
            [  # column changes for "my_model"
                ("modify_nullable", None, "my_model", "col", {}, False, True),
            ],
            ("add_table", ...),  # table-level op
        ]

    This function flattens that into a uniform list of op tuples so tests can
    iterate or index without handling both shapes.
    """
    before_metadata.create_all(engine)
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        diffs = compare_metadata(ctx, after_metadata)
    return [op for item in diffs for op in (item if isinstance(item, list) else [item])]


class TestMigrationDiff:
    """Alembic compare_metadata produces correct diffs for deprecated columns."""

    def test_no_migration_when_db_has_deprecated_column(self, engine):
        """No migration ops are generated when the DB column is already nullable."""

        class BeforeBase(DeclarativeBase):
            pass

        class Before(BeforeBase):
            __tablename__ = "my_model"
            id: Mapped[int] = mapped_column(primary_key=True)
            old_field: Mapped[str | None] = mapped_column(String, nullable=True)

        class AfterBase(DeclarativeBase):
            pass

        class After(AfterBase):
            __tablename__ = "my_model"
            id: Mapped[int] = mapped_column(primary_key=True)
            old_field: Mapped[str | None] = deprecated_column(String, nullable=True)

        ops = diff_schemas(engine, BeforeBase.metadata, AfterBase.metadata)
        assert ops == []

    def test_drop_not_null_generated_for_non_null_deprecated_field(self, engine):
        """A DROP NOT NULL migration is generated when the DB column is NOT NULL.

        Deprecating a non-nullable column requires making it nullable first so
        existing rows aren't affected when the column is eventually dropped.
        """

        class BeforeBase(DeclarativeBase):
            pass

        class Before(BeforeBase):
            __tablename__ = "my_model"
            id: Mapped[int] = mapped_column(primary_key=True)
            old_field: Mapped[str] = mapped_column(String, nullable=False)

        class AfterBase(DeclarativeBase):
            pass

        class After(AfterBase):
            __tablename__ = "my_model"
            id: Mapped[int] = mapped_column(primary_key=True)
            old_field: Mapped[str] = deprecated_column(String, nullable=False)

        ops = diff_schemas(engine, BeforeBase.metadata, AfterBase.metadata)
        assert len(ops) == 1

        op, schema, table, column, _, was_nullable, becomes_nullable = ops[0]
        assert op == "modify_nullable"
        assert table == "my_model"
        assert column == "old_field"
        assert was_nullable is False
        assert becomes_nullable is True

    def test_extra_arguments_are_forwarded(self, engine):
        """Extra arguments (e.g. index=True) are forwarded to mapped_column so
        Alembic sees the column unchanged apart from nullability — no spurious
        DROP INDEX op is generated.
        """

        class BeforeBase(DeclarativeBase):
            pass

        class Before(BeforeBase):
            __tablename__ = "my_model"
            id: Mapped[int] = mapped_column(primary_key=True)
            old_field: Mapped[str] = mapped_column(String, nullable=False, index=True)

        class AfterBase(DeclarativeBase):
            pass

        class After(AfterBase):
            __tablename__ = "my_model"
            id: Mapped[int] = mapped_column(primary_key=True)
            old_field: Mapped[str] = deprecated_column(String, nullable=False, index=True)

        ops = diff_schemas(engine, BeforeBase.metadata, AfterBase.metadata)
        assert len(ops) == 1

        op, schema, table, column, _, was_nullable, becomes_nullable = ops[0]
        assert op == "modify_nullable"
