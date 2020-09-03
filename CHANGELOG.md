# Changelog for pocketutils

Adheres to [Semantic Versioning 2.0](https://semver.org/spec/v2.0.0.html) and
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.4.0] - unreleased


## [0.3.0] - 2020-09-02

### Changed:
- Moved `core.io` to `core.input_output` to fix namespace conflicts.
- Made `NestedDotDict` implement `Mapping` and changed its methods


## [0.2.0] - 2020-09-01

### Removed:
- `db` subpackage
- `toml_data` module. Use `NestedDotDict` instead.

### Changed:
- Made `tools` require the `tools` optional package


## [0.1.0] - 2020-08-06

### Added:
- Current codebase
