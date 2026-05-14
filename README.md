# sqlalchemy-deprecated-column

[![PyPi](https://img.shields.io/pypi/v/sqlalchemy-deprecated-column.svg)](https://pypi.python.org/pypi/sqlalchemy-deprecated-column/)
[![PyVersions](https://img.shields.io/pypi/pyversions/sqlalchemy-deprecated-column.svg)](https://pypi.python.org/pypi/sqlalchemy-deprecated-column/)
[![Coverage](https://codecov.io/gh/jakub-bacic/sqlalchemy-deprecated-column/graph/badge.svg)](https://codecov.io/gh/jakub-bacic/sqlalchemy-deprecated-column)
[![License](https://img.shields.io/github/license/jakub-bacic/sqlalchemy-deprecated-column.svg)](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/blob/main/LICENSE)

Safely remove SQLAlchemy columns through a gradual deprecation process.
Inspired by [django-deprecate-fields](https://github.com/3YOURMIND/django-deprecate-fields).

## Installation

```bash
pip install sqlalchemy-deprecated-column
```

While the project is pre-1.0, breaking changes may land in **minor** releases (e.g. `0.1.x` → `0.2.0`), following the SemVer convention for `0.y.z` versions. Patch releases (`0.1.3` → `0.1.4`) remain backwards-compatible. To avoid surprise breakage, pin to a specific minor version.

## How it works

Removing a column from a live database requires coordination between code and schema changes. Dropping the column in a single step would break any running application instances that still reference it. This library lets you do this safely in three steps:

1. **Deprecate**: replace `mapped_column()` with `deprecated_column()` (ORM) or `Column()` with `DeprecatedColumn()` (Core) and run an Alembic migration. The column stays in the database but becomes nullable if it wasn't already.
2. **Deploy**: the column is hidden from all generated SQL. Any remaining code that references the column gets a `DeprecationWarning` at runtime (or raises `ColumnDeprecatedError` if `raise_on_access=True`), making stale references easy to find and remove.
3. **Remove**: once all references are gone, delete the deprecated column definition and run a final migration to drop the column from the database.

## Usage

### ORM

`deprecated_column()` is a drop-in replacement for `mapped_column()` and accepts the same arguments. For columns declared with only a bare `Mapped[T]` annotation, add `deprecated_column()` with no arguments.

**Before:**

```python
class User(Base):
    ...
    old_username: Mapped[str] = mapped_column(String(200), index=True)
    old_email: Mapped[str]
```

**After:**

```python
from sqlalchemy_deprecated_column import deprecated_column

class User(Base):
    ...
    old_username: Mapped[str] = deprecated_column(String(200), index=True)
    old_email: Mapped[str] = deprecated_column()
```

While the column is deprecated the library:

- **Hides it from the ORM**: the column is excluded from all generated SQL queries — existing application code stays compatible even after the column is eventually dropped from the database.
- **Warns on instance read**: `instance.old_username` returns `None` and emits a `DeprecationWarning` naming the model and column, so the call site is easy to locate.
- **Warns on class-level reference**: `User.old_username` (e.g. in filter expressions) emits a `DeprecationWarning` and evaluates to SQL `NULL`.
- **Warns on write and discards the value**: `instance.old_username = "x"` emits a `DeprecationWarning` and silently drops the value, so no stale data is written to the database.

### Core

`DeprecatedColumn()` is a drop-in replacement for `Column()` in Core `Table` definitions and accepts the same arguments.

**Before:**

```python
from sqlalchemy import Column, String, Table, MetaData

metadata = MetaData()
users = Table(
    "users",
    metadata,
    # other columns...
    Column("old_username", String(200)),
)
```

**After:**

```python
from sqlalchemy import Column, String, Table, MetaData
from sqlalchemy_deprecated_column import DeprecatedColumn

metadata = MetaData()
users = Table(
    "users",
    metadata,
    # other columns...
    DeprecatedColumn("old_username", String(200)),
)
```

While the column is deprecated the library:

- **Hides it from SELECT**: `select(users)` excludes the column — it will not appear in the query or in result rows.
- **Warns on explicit SELECT**: `select(users.c.old_username)` emits a `DeprecationWarning` at compile time and substitutes `NULL` in the query, so no data is fetched from the database.
- **Warns on WHERE reference**: using the column in a filter expression (e.g. `users.c.old_username == "x"`) emits a `DeprecationWarning` at expression-build time and substitutes `NULL`.
- **Hides it from auto-INSERT/UPDATE**: when the column is not explicitly referenced, it is excluded from generated INSERT and UPDATE statements entirely.
- **Warns on explicit INSERT/UPDATE**: explicitly passing the column in `.values()` emits a `DeprecationWarning` and substitutes `NULL` for the supplied value.

> [!IMPORTANT]
> Unlike the ORM, explicit INSERT/UPDATE statements that reference the deprecated column (e.g. `insert(users).values(old_username="x")`) cannot have the column name stripped from the generated SQL. The value is replaced with `NULL` and a `DeprecationWarning` is emitted, but the column name remains in the query. Use the warning to locate and remove the remaining explicit reference.

## Options

### raise_on_access

Pass `raise_on_access=True` to raise a `ColumnDeprecatedError` on any access instead of emitting a warning. This works for both ORM and Core and is useful when you want to enforce that all stale references are removed — for example, by letting the exception surface in tests or CI:

```python
# ORM (inside a model class)
old_username: Mapped[str] = deprecated_column(String(200), raise_on_access=True)

# Core (inside a Table definition)
DeprecatedColumn("old_username", String(200), raise_on_access=True)
```

## Alembic integration

Add the following **at the top of `alembic/env.py`, before any model or metadata imports**:

```python
import sqlalchemy_deprecated_column
sqlalchemy_deprecated_column.configure(alembic_mode=True)
```

In Alembic mode, `deprecated_column()` acts as `mapped_column(nullable=True)` and `DeprecatedColumn()` acts as `Column(nullable=True)`. Alembic will:

- **Not** generate `DROP COLUMN` for deprecated columns.
- **Generate `ALTER TABLE … DROP NOT NULL`** if the column was originally non-nullable. This is needed because once the column is deprecated it is no longer included in `INSERT` statements — a `NOT NULL` column without a value would cause those inserts to fail.

## Requirements

- Python 3.10+
- SQLAlchemy 2.0+

## License

The code in this project is licensed under MIT license. See [LICENSE](./LICENSE) for more information.
