"""Tests for raise_on_access=True behaviour of deprecated_column().

When raise_on_access is True, accessing a deprecated field raises
ColumnDeprecatedError instead of emitting a DeprecationWarning.
"""

import pytest
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sqlalchemy_deprecated_column import ColumnDeprecatedError, deprecated_column


@pytest.fixture
def model_cls():
    class Base(DeclarativeBase):
        pass

    class MyModel(Base):
        __tablename__ = "my_model"
        id: Mapped[int] = mapped_column(primary_key=True)
        old_field: Mapped[str] = deprecated_column(String, raise_on_access=True)

    return MyModel


@pytest.fixture
def model(model_cls):
    return model_cls()


class TestRaiseOnAccess:
    """raise_on_access=True raises ColumnDeprecatedError instead of warning."""

    def test_read_raises(self, model):
        with pytest.raises(
            ColumnDeprecatedError, match="accessing deprecated field MyModel.old_field"
        ):
            _ = model.old_field

    def test_write_raises(self, model):
        with pytest.raises(
            ColumnDeprecatedError, match="writing to deprecated field MyModel.old_field"
        ):
            model.old_field = "value"

    def test_class_read_raises(self, model_cls):
        with pytest.raises(
            ColumnDeprecatedError, match="referencing deprecated class field MyModel.old_field"
        ):
            _ = model_cls.old_field
