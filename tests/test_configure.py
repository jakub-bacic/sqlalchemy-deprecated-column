"""Tests for the configure() entry point."""

import pytest

from sqlalchemy_deprecated_column import configure
from sqlalchemy_deprecated_column.deprecated_column import _config


class TestKeyword:
    def test_default_disables_alembic_mode(self):
        configure()
        assert _config.alembic_mode is False

    def test_keyword_true_enables_alembic_mode(self):
        configure(alembic_mode=True)
        assert _config.alembic_mode is True


class TestPositionalDeprecation:
    def test_positional_still_applies_value(self):
        with pytest.warns(DeprecationWarning):
            configure(True)
        assert _config.alembic_mode is True

    def test_positional_emits_deprecation_warning(self):
        with pytest.warns(DeprecationWarning) as record:
            configure(True)

        (warning,) = record
        assert str(warning.message) == (
            "Passing alembic_mode as a positional argument "
            "is deprecated and will be removed in 0.3.0; "
            "use configure(alembic_mode=...) instead."
        )
        assert warning.filename == __file__

    def test_too_many_positional_raises(self):
        with pytest.raises(TypeError, match="at most 1 positional argument"):
            configure(True, False)  # type: ignore[call-arg]
