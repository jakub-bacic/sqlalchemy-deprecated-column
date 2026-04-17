# sqlalchemy-deprecated-column

[![PyPi](https://img.shields.io/pypi/v/sqlalchemy-deprecated-column.svg)](https://pypi.python.org/pypi/sqlalchemy-deprecated-column/)
[![PyVersions](https://img.shields.io/pypi/pyversions/sqlalchemy-deprecated-column.svg)](https://pypi.python.org/pypi/sqlalchemy-deprecated-column/)
[![Coverage](https://codecov.io/gh/jakub-bacic/sqlalchemy-deprecated-column/graph/badge.svg)](https://codecov.io/gh/jakub-bacic/sqlalchemy-deprecated-column)
[![License](https://img.shields.io/github/license/jakub-bacic/sqlalchemy-deprecated-column.svg)](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/blob/main/LICENSE)

Safely remove SQLAlchemy ORM columns through a gradual deprecation process.
Inspired by [django-deprecate-fields](https://github.com/3YOURMIND/django-deprecate-fields).

## Installation

```bash
pip install sqlalchemy-deprecated-column
```

## How it works

Removing a column from a live database requires coordination between code and schema changes. Dropping the column in a single step would break any running application instances that still reference it. `deprecated_column()` lets you do this safely in three steps:

1. **Deprecate**: replace `mapped_column()` with `deprecated_column()` and run an Alembic migration. The column stays in the database but becomes nullable if it wasn't already.
2. **Deploy**: the column is hidden from the ORM — it no longer appears in any generated SQL. Any remaining code that reads or writes the column gets a `DeprecationWarning` at runtime, making stale references easy to find and remove.
3. **Remove**: once all references are gone, delete the `deprecated_column()` definition from the model and run a final migration to drop the column from the database.

## Usage

`deprecated_column()` is a drop-in replacement for `mapped_column()` and accepts the same arguments. For columns declared with only a bare `Mapped[T]` annotation, add `deprecated_column()` with no arguments.

**Before:**

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String)
    old_username: Mapped[str] = mapped_column(String(200), index=True)
    old_email: Mapped[str]
```

**After:**

```python
from sqlalchemy_deprecated_column import deprecated_column

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String)
    old_username: Mapped[str] = deprecated_column(String(200), index=True)
    old_email: Mapped[str] = deprecated_column()
```

While the column is deprecated the library:

- **Hides it from the ORM**: the column is excluded from all generated SQL queries — existing application code stays compatible even after the column is eventually dropped from the database.
- **Warns on instance read**: `instance.old_username` returns `None` and emits a `DeprecationWarning` naming the model and column, so the call site is easy to locate.
- **Warns on class-level reference**: `User.old_username` (e.g. in filter expressions) emits a `DeprecationWarning` and evaluates to SQL `NULL`.
- **Warns on write and discards the value**: `instance.old_username = "x"` emits a `DeprecationWarning` and silently drops the value, so no stale data is written to the database.

## Alembic integration

Add the following **at the top of `alembic/env.py`, before any model imports**:

```python
import sqlalchemy_deprecated_column
sqlalchemy_deprecated_column.configure(alembic_mode=True)

# model imports must come after configure()
from myapp import mymodel
target_metadata = mymodel.Base.metadata
```

In Alembic mode, `deprecated_column()` acts as `mapped_column(nullable=True)`. Alembic will:

- **Not** generate `DROP COLUMN` for deprecated columns.
- **Generate `ALTER TABLE … DROP NOT NULL`** if the column was originally non-nullable. This is needed because once the column is deprecated the ORM stops including it in `INSERT` statements — a `NOT NULL` column without a value would cause those inserts to fail.

## Requirements

- Python 3.10+
- SQLAlchemy 2.0+

## License

The code in this project is licensed under MIT license. See [LICENSE](./LICENSE) for more information.
