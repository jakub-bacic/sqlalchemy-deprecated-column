# sqlalchemy-deprecated-column

A SQLAlchemy utility that lets you deprecate ORM columns safely.

## Project structure

```
src/sqlalchemy_deprecated_column/   # package source
tests/                              # pytest tests
```

## Commands

```bash
uv run pytest          # run tests
uv run pyright         # type check
uv run ruff check      # lint
```

## Backward compatibility

This is a published library — prefer backward compatible changes to the public API (`deprecated_column`, `configure`). The public API surface is exactly these two symbols, re-exported from `__init__.py`. Unless the user explicitly asks for a breaking change, avoid:
- Removing or renaming public symbols.
- Changing the signature of `deprecated_column()` or `configure()` in a breaking way.
- Changing the deprecation warning message format, as users may assert against it in their own tests.

## Releases

Releases are automated via release-please — don't bump `version` in `pyproject.toml` or edit `CHANGELOG.md` by hand. Commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, etc.) since release-please uses them to determine version bumps and changelog entries.

## Key design decisions

- **`deprecated_column()` is a drop-in for `mapped_column()`** — accepts the same arguments, which are intentionally ignored in normal mode (only forwarded to `mapped_column` in alembic_mode).
- **`conftest.py` resets config between tests** — the `reset_config` autouse fixture calls `sdc.configure()` to restore defaults, preventing state leaking between tests.
