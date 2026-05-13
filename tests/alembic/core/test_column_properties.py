"""Tests for column-level schema properties of DeprecatedColumn in alembic_mode.

In alembic_mode, DeprecatedColumn returns a plain Column so Alembic can track
migrations. These tests verify the resulting column properties for Core Table definitions.
"""

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table

from sqlalchemy_deprecated_column import DeprecatedColumn


@pytest.fixture
def table():
    metadata = MetaData()
    return Table(
        "my_model",
        metadata,
        Column("id", Integer, primary_key=True),
        DeprecatedColumn("nullable_field", String),
        DeprecatedColumn("unique_nullable_field", String, unique=True),
        DeprecatedColumn("non_nullable_field", String, nullable=False),
    )


class TestColumnProperties:
    """Column properties exposed to Alembic when alembic_mode is enabled."""

    def test_table_columns(self, table):
        """All DeprecatedColumns are present in the table in alembic_mode."""
        assert set(table.c.keys()) == {
            "id",
            "nullable_field",
            "unique_nullable_field",
            "non_nullable_field",
        }

    def test_nullable_field(self, table):
        col = table.c["nullable_field"]

        assert isinstance(col.type, String)
        assert col.nullable is True

    def test_unique_nullable_field(self, table):
        col = table.c["unique_nullable_field"]

        assert isinstance(col.type, String)
        assert col.nullable is True
        assert col.unique is True

    def test_non_null_field(self, table):
        """DeprecatedColumn forces nullable=True even when nullable=False is passed.

        The column must be nullable in the DB so it can be dropped later without
        a NOT NULL constraint violation.
        """
        col = table.c["non_nullable_field"]

        assert isinstance(col.type, String)
        assert col.nullable is True
