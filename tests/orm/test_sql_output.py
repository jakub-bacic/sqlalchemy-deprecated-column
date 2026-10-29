"""Tests for SQLAlchemy schema and SQL behavior of deprecated_column().

Verifies that deprecated columns never appear in generated SELECT or INSERT
statements, and that statements using a class-level reference raise.
"""

import pytest
from sqlalchemy import String, delete, func, insert, select, update
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sqlalchemy_deprecated_column import ColumnDeprecatedError, deprecated_column


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
    """Deprecated columns never appear in generated SQL output."""

    def test_deprecated_column_absent_from_select_sql(self, model_cls, session, capsql):
        stmt = select(model_cls)
        session.execute(stmt)

        [sql] = capsql.records
        assert "deprecated_name" not in sql

    def test_deprecated_column_absent_from_insert_sql(self, model_cls, session, capsql):
        session.add(model_cls(name="test"))
        session.flush()

        [sql] = capsql.records
        assert "deprecated_name" not in sql


class TestClassLevelReference:
    """Statements that use a class-level reference raise when compiled."""

    MESSAGE = "referencing deprecated class field MyModel.deprecated_name"

    @pytest.mark.parametrize(
        "build",
        [
            pytest.param(lambda m: select(m).where(m.deprecated_name == "x"), id="where"),
            pytest.param(lambda m: select(m).where(m.deprecated_name.is_(None)), id="is_none"),
            pytest.param(lambda m: select(m).filter_by(deprecated_name="x"), id="filter_by"),
            pytest.param(lambda m: select(m).order_by(m.deprecated_name), id="order_by"),
            pytest.param(lambda m: select(m.deprecated_name), id="columns"),
            pytest.param(lambda m: select(func.count(m.deprecated_name)), id="function"),
            pytest.param(lambda m: update(m).values(deprecated_name="x"), id="update_values"),
            pytest.param(lambda m: insert(m).values(deprecated_name="x"), id="insert_values"),
            pytest.param(lambda m: delete(m).where(m.deprecated_name.is_(None)), id="delete"),
        ],
    )
    def test_execute_raises(self, model_cls, session, capsql, build):
        stmt = build(model_cls)

        with pytest.raises(ColumnDeprecatedError, match=self.MESSAGE):
            session.execute(stmt)
        assert not capsql.records

    def test_raises_on_every_execution(self, model_cls, session):
        stmt = select(model_cls).where(model_cls.deprecated_name == "x")

        for _ in range(2):
            with pytest.raises(ColumnDeprecatedError, match=self.MESSAGE):
                session.execute(stmt)

    def test_compile_raises(self, model_cls):
        stmt = select(model_cls).where(model_cls.deprecated_name == "x")

        with pytest.raises(ColumnDeprecatedError, match=self.MESSAGE):
            str(stmt)

    def test_delete_keeps_rows(self, model_cls, session):
        session.add_all([model_cls(name="a"), model_cls(name="b")])
        session.flush()

        with pytest.raises(ColumnDeprecatedError):
            session.execute(delete(model_cls).where(model_cls.deprecated_name.is_(None)))
        assert session.scalar(select(func.count()).select_from(model_cls)) == 2
