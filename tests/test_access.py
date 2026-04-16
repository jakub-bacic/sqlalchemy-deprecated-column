"""Tests for runtime access behaviour of deprecated fields.

Covers instance reads, class-level reads, and instance writes — each of which
should return None and emit a DeprecationWarning.
"""

import pytest
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sqlalchemy_deprecated_column import deprecated_column


@pytest.fixture
def model_cls():
    class Base(DeclarativeBase):
        pass

    class MyModel(Base):
        __tablename__ = "my_model"
        id: Mapped[int] = mapped_column(primary_key=True)
        old_field: Mapped[str] = deprecated_column(String)

    return MyModel


@pytest.fixture
def model(model_cls):
    return model_cls()


class TestRead:
    """Reading a deprecated field on a model instance."""

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_returns_none(self, model):
        assert model.old_field is None

    def test_emits_deprecation_warning(self, model):
        with pytest.warns(DeprecationWarning) as record:
            _ = model.old_field

        (warning,) = record
        assert str(warning.message) == "accessing deprecated field MyModel.old_field"
        assert warning.filename == __file__


class TestClassRead:
    """Reading a deprecated field directly on the model class."""

    def test_emits_deprecation_warning(self, model_cls):
        with pytest.warns(DeprecationWarning) as record:
            _ = model_cls.old_field

        (warning,) = record
        assert str(warning.message) == "referencing deprecated class field MyModel.old_field"
        assert warning.filename == __file__


class TestWrite:
    """Writing to a deprecated field via direct assignment."""

    def test_emits_deprecation_warning(self, model):
        with pytest.warns(DeprecationWarning) as record:
            model.old_field = "value"

        (warning,) = record
        assert str(warning.message) == "writing to deprecated field MyModel.old_field"
        assert warning.filename == __file__


class TestInit:
    """Constructing a model instance that has a deprecated field."""

    def test_no_warning_when_deprecated_field_not_passed(self, model_cls, recwarn):
        model_cls(id=12)

        assert not recwarn.list

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_ignores_value_of_deprecated_field(self, model_cls):
        """The value is simply discarded without a runtime error."""
        instance = model_cls(old_field="some_value")

        assert instance.old_field is None
