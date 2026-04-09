import pytest

import sqlalchemy_deprecated_column as sdf


@pytest.fixture(autouse=True)
def enable_alembic_mode():
    sdf.configure(alembic_mode=True)
