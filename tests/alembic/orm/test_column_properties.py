"""Tests for column-level schema properties of deprecated_column() in alembic_mode.

In alembic_mode, deprecated columns are visible to Alembic's schema inspection so
it can track them in migrations. These tests verify the resulting column properties:
type, nullability, uniqueness, and custom naming.
"""

import pytest
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sqlalchemy_deprecated_column import deprecated_column


@pytest.fixture
def model_cls():
    class Base(DeclarativeBase):
        pass

    class MyModel(Base):
        __tablename__ = "my_model"
        id: Mapped[int] = mapped_column(primary_key=True)

        nullable_field: Mapped[str | None] = deprecated_column(String)
        unique_nullable_field: Mapped[str] = deprecated_column(String, unique=True)

        non_nullable_field: Mapped[str] = deprecated_column(String, nullable=False)

        custom_name: Mapped[str | None] = deprecated_column("different_name", String)
        inferred_type: Mapped[int] = deprecated_column()

    return MyModel


class TestColumnProperties:
    """Column properties exposed to Alembic when alembic_mode is enabled."""

    def test_table_columns(self, model_cls):
        """All deprecated columns are present in the mapped table in alembic_mode."""
        assert set(model_cls.__table__.c.keys()) == {
            "id",
            "nullable_field",
            "unique_nullable_field",
            "non_nullable_field",
            "different_name",  # custom name
            "inferred_type",
        }

    def test_nullable_field(self, model_cls):
        col = model_cls.__table__.c["nullable_field"]

        assert isinstance(col.type, String)
        assert col.nullable is True

    def test_unique_nullable_field(self, model_cls):
        col = model_cls.__table__.c["unique_nullable_field"]

        assert isinstance(col.type, String)
        assert col.nullable is True
        assert col.unique is True

    def test_non_null_field(self, model_cls):
        """deprecated_column forces nullable=True even when nullable=False is passed.

        The column must be nullable in the DB so it can be dropped later without
        a NOT NULL constraint violation.
        """
        col = model_cls.__table__.c["non_nullable_field"]

        assert isinstance(col.type, String)
        assert col.nullable is True

    def test_custom_name(self, model_cls):
        col = model_cls.__table__.c["different_name"]

        assert isinstance(col.type, String)
        assert col.nullable is True

    def test_inferred_type(self, model_cls):
        """The column type is inferred from the Mapped[] annotation when not specified."""
        col = model_cls.__table__.c["inferred_type"]

        assert isinstance(col.type, Integer)
        assert col.nullable is True
