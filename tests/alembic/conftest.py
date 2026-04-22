import pytest
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext

import sqlalchemy_deprecated_column as sdc


@pytest.fixture(autouse=True)
def enable_alembic_mode():
    sdc.configure(alembic_mode=True)


@pytest.fixture
def diff_schemas(engine):
    """Return a callable that creates a DB from before_metadata and returns
    flattened compare_metadata ops against after_metadata.

    compare_metadata returns a mixed structure: table-level ops are plain tuples
    at the top level, while column-level ops are grouped in inner lists per table:

        [
            [  # column changes for "my_model"
                ("modify_nullable", None, "my_model", "col", {}, False, True),
            ],
            ("add_table", ...),  # table-level op
        ]

    The returned callable flattens that into a uniform list of op tuples so tests
    can iterate or index without handling both shapes.
    """

    def _diff(before_metadata, after_metadata):
        before_metadata.create_all(engine)
        with engine.connect() as conn:
            ctx = MigrationContext.configure(conn)
            diffs = compare_metadata(ctx, after_metadata)
        return [op for item in diffs for op in (item if isinstance(item, list) else [item])]

    return _diff
