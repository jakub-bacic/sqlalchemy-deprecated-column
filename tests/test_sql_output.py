"""Tests for SQLAlchemy schema and SQL behaviour of deprecated_column().

Verifies that deprecated columns are excluded from the table definition and
never appear in generated SELECT, WHERE, or INSERT statements.
"""

import pytest
from sqlalchemy import String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sqlalchemy_deprecated_column import deprecated_column


@pytest.fixture
def model_cls():
    class Base(DeclarativeBase):
        pass

    class MyModel(Base):
        __tablename__ = "my_model"
        id: Mapped[int] = mapped_column(primary_key=True)

        name: Mapped[str] = mapped_column(String)
        deprecated_name: Mapped[str] = deprecated_column(String)

    return MyModel


@pytest.fixture(autouse=True)
def create_schema(engine, model_cls):
    model_cls.metadata.create_all(engine)


class TestSqlOutput:
    """Deprecated columns are hidden from the SQLAlchemy table and SQL output."""

    def test_table_columns(self, model_cls):
        """deprecated_column is absent from the mapped table's column set."""
        assert set(model_cls.__table__.c.keys()) == {"id", "name"}

    def test_deprecated_column_absent_from_select_sql(self, model_cls, session, capsql):
        stmt = select(model_cls)
        session.execute(stmt)

        [sql] = capsql.records
        assert "deprecated_name" not in sql

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_deprecated_column_absent_from_where_clause(self, model_cls, session, capsql):
        stmt = select(model_cls).where(model_cls.deprecated_name == "my-value")
        session.execute(stmt)

        [sql] = capsql.records
        assert "deprecated_name" not in sql

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_deprecated_column_supports_sql_expressions(self, model_cls, session, capsql):
        """Ensure callers can write queries against a deprecated field without a runtime error."""
        stmt = select(model_cls).where(model_cls.deprecated_name.is_(None))
        session.execute(stmt)

        [sql] = capsql.records
        assert "deprecated_name" not in sql

    def test_deprecated_column_absent_from_insert_sql(self, model_cls, session, capsql):
        session.add(model_cls(name="test"))
        session.flush()

        [sql] = capsql.records
        assert "deprecated_name" not in sql
