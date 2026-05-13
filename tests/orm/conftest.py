import pytest
from sqlalchemy.orm import Session


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s
        s.rollback()
