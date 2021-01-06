# Changelog for pocketutils

Adheres to [Semantic Versioning 2.0](https://semver.org/spec/v2.0.0.html) and
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).


## [0.4.0 - 2021-01-05

### Changed:
- Bumped numpy from `>=1.18, <2.0` to `>=1.19, <2.0`.
  Historically Numpy minor updates have introduced problems in downstream code.
  Because 1.19 is more likely to be used now anyway, this new version restriction
  is more likely to fix problems. Any issue with this would simply result in a
  version conflict.
- Made `NestedDotDict` use `orjson`, which is now a core dependency.
  The python3 `json` package has serious issues and does not produce valid JSON.
  This is a backwards-incompatible change only in the sense of reading or writing
  in exactly the same (invalid) format that was used in 0.4.0.
- Upgraded build to tyrannosaurus 0.8.4, revamping Github workflows, etc.
- Deprecated `PathLike.isinstance` and `pathlike_isinstance`.
  They were causing [an error in Python 3.9](https://github.com/dmyersturnbull/pocketutils/issues/2)
  Callers should now use `PathLikeUtils.isinstance`.

### Removed:
- Dropped support for Python 3.7

### Added:
- A few small functions in `StringTools`

### Fixed
- Python 3.9 compatibility


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
