import pytest


@pytest.fixture
def conn(engine):
    with engine.connect() as c:
        yield c
