# sqlalchemy-deprecated-column

A SQLAlchemy utility that lets you deprecate ORM and Core columns safely.

## Project structure

```
src/sqlalchemy_deprecated_column/
  __init__.py           # re-exports public API
  _core.py              # DeprecatedColumn for Core Table definitions
  _orm.py               # deprecated_column() for ORM mapped models
  _shared.py            # shared config
tests/
  core/                 # Core (Table/Column) tests
  orm/                  # ORM (mapped_column) tests
  alembic/
    core/               # Alembic migration tests for Core
    orm/                # Alembic migration tests for ORM
```

## Commands

```bash
uv run pytest          # run tests
uv run pyright         # type check
uv run ruff check      # lint
```

## Backward compatibility

This is a published library — prefer backward compatible changes to the public API. The public API surface is exactly these four symbols, re-exported from `__init__.py`:

- `deprecated_column` — drop-in for `mapped_column()` in ORM models
- `DeprecatedColumn` — drop-in for `Column()` in Core `Table` definitions
- `configure` — sets global options (e.g. `alembic_mode`)
- `ColumnDeprecatedError` — raised when `raise_on_access=True`

Unless the user explicitly asks for a breaking change, avoid:
- Removing or renaming public symbols.
- Changing the signature of `deprecated_column()`, `DeprecatedColumn()`, or `configure()` in a breaking way.
- Changing the deprecation warning message format, as users may assert against it in their own tests.

## Releases

Releases are automated via release-please — don't bump `version` in `pyproject.toml` or edit `CHANGELOG.md` by hand. Commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, etc.) since release-please uses them to determine version bumps and changelog entries.

## Documentation

`README.md` is the public-facing documentation. Keep it up to date when changing the public API, adding new features, or changing existing behavior — usage examples, behavior bullet points, and the Alembic section should all reflect the current state of the library.

Docstrings on public symbols are also part of the documentation. Keep the style consistent with `README.md`: same terminology, same level of detail for equivalent concepts.

Use **US English** throughout — both in `README.md` and in docstrings (e.g. "behavior" not "behaviour", "recognize" not "recognise").

## Key design decisions

- **`deprecated_column()` is a drop-in for `mapped_column()`** — accepts the same arguments, which are intentionally ignored in normal mode (only forwarded to `mapped_column` in alembic_mode).
- **`DeprecatedColumn` is a drop-in for `Column()`** — accepts the same arguments and forwards them to `Column.__init__()` in both modes; `nullable` is forced to `True`.
- **`conftest.py` resets config between tests** — the `reset_config` autouse fixture calls `sdc.configure()` to restore defaults, preventing state leaking between tests.
