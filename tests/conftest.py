from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

import sqlalchemy_deprecated_column as sdf


@pytest.fixture
def engine():
    return create_engine("sqlite://")


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s
        s.rollback()


@pytest.fixture(autouse=True)
def reset_config():
    sdf.configure()
    yield


class SQLCaptureFixture:
    def __init__(self) -> None:
        self.records: list[str] = []

    def _capture(self, conn, cursor, statement, parameters, context, executemany) -> None:
        self.records.append(statement)


@pytest.fixture
def capsql() -> Generator[SQLCaptureFixture]:
    cap = SQLCaptureFixture()
    event.listen(Engine, "before_cursor_execute", cap._capture)
    yield cap
    event.remove(Engine, "before_cursor_execute", cap._capture)
