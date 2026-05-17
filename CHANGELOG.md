# Changelog

## [0.4.0](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/compare/v0.3.0...v0.4.0) (2026-05-17)


### Features

* add DeprecatedColumn for SQLAlchemy Core Table definitions ([#22](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/issues/22)) ([f35e8f2](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/commit/f35e8f2ec84a6467e1f7a0a86fa138a88f8531b4))


### Bug Fixes

* project Core deprecated columns as NULL in SELECT so result rows remain accessible ([#24](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/issues/24)) ([e3b2aaf](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/commit/e3b2aaf323492c43c1d2744c1977c3c850d38c46))


### Documentation

* mark Core feature as experimental ([#26](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/issues/26)) ([69b4e60](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/commit/69b4e6014569592f52aff8e5cc7c9651d61a7660))
* update README for Core DeprecatedColumn ([#25](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/issues/25)) ([a9a0af5](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/commit/a9a0af5451a52e1b4178347cf48aacc12efeb35e))

## [0.3.0](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/compare/v0.2.0...v0.3.0) (2026-05-07)


### Features

* add raise_on_access option to deprecated_column() ([#21](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/issues/21)) ([ba4ca0b](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/commit/ba4ca0bf3592507e5b05d32d51b5d184d7591eb5))
* remove positional argument support from configure() ([#19](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/issues/19)) ([cf51269](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/commit/cf5126965a23b5683c2055d07cd134a876a53b26))

## [0.2.0](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/compare/v0.1.4...v0.2.0) (2026-05-06)


### Features

* deprecate positional argument in configure() ([#17](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/issues/17)) ([a398795](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/commit/a3987955843c3b8a3d6ffa76b0ea8318dfaca40c))

## [0.1.4](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/compare/v0.1.3...v0.1.4) (2026-04-17)


### Documentation

* add keywords for PyPI discoverability ([#14](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/issues/14)) ([f05dbfa](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/commit/f05dbfae12751daaaa309af15e1f80cf58e4369b))

## [0.1.3](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/compare/v0.1.2...v0.1.3) (2026-04-17)


### Documentation

* improve README and fix project urls ([18b836d](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/commit/18b836dbcab7d1612f733774b7008fb5408468dd))

## [0.1.2](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/compare/v0.1.1...v0.1.2) (2026-04-16)


### Bug Fixes

* deprecation warnings point at SQLAlchemy internals when triggered from __init__ ([#8](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/issues/8)) ([6c8af0e](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/commit/6c8af0ebfadf7042b7ca2cd0bd8f68c7f411388a))

## [0.1.1](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/compare/sqlalchemy-deprecated-column-v0.1.0...sqlalchemy-deprecated-column-v0.1.1) (2026-04-16)


### Bug Fixes

* correct stacklevel so deprecation warnings point to the caller ([#2](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/issues/2)) ([e76beaa](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/commit/e76beaa65f0caf0581e16c3e257c5e8577695e64))

## 0.1.0 (2026-04-16)


### Features

* initial release ([1496266](https://github.com/jakub-bacic/sqlalchemy-deprecated-column/commit/1496266dd6f7c015ad32bae0e8127fe7e87737a6))
