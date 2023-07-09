# Changelog for pocketutils

Adheres to [Semantic Versioning 2.0](https://semver.org/spec/v2.0.0.html) and
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.10.0] - unreleased

### Changed

- A lot

## [0.9.0] - 2022-08-11

### Removed

- Deprecated methods
- `SmartEnum` (use `CleverEnum` instead)
- Memory cache class
- `FilesysTools.new_webresource`

### Changed

- Moved `WebResource` to `misc` package
- Renamed `UnitTools.concentration_to_micromolar` to `parse_molarity`

### Fixed

- `FigSaver` `as_type` constructor arg
- Gene ontology download working with new URLs

## [0.8.0] - 2021-10-11

### Added

- `FilesysTools.get_info`
- `UnitTools.approx_time_wrt`

### Changed

- Renamed functions in `PathTools`
- Path sanitization is more flexible
- defusedxml is now required
- json code uses `orjson`
- Renamed `extract_group_1` to `extract_group` and improved

### Removed

- Some deprecated functions
- `s` from `OpenMode`
- jsonpickle and dill

## [0.7.1] - 2021-10-10

### Added

- `ReflectionTools`
- `resources`
- `typer_utils`
- methods to `FancyLoguruExtras`

### Changed

- `FancyLoguru` adds methods to the logger by default

### Removed

- `HashValidationFailedError` (use `HashValidationError`)

### Fixed

- Re-added `LoopTools` to `AllTools`
- `FancyLoguruDefaults` format names
- `FancyLoguru.config_levels` default args

## [0.7.0] - 2021-10-06

### Added

- `list_package_versions`
- `enum.py`

### Changed

- `get_env_info` includes more

### Removed

- About half of the deprecated functions

## [0.6.0] - 2021-10-05

### Added

- fancy loguru

### Changed

- Deprecated a lot of code
- A few misc backwards-incompatible changes

## [0.5.0] - 2021-06-08

### Added:

- `flex` arg on `parse_bool`

### Changed:

- Major version bumps; mainly jsonpickle to v2
- `PrettyRecordFactory` now puts the status first and can use emojis
- `NestedDotDict.read_json` and `NestedDotDict.parse_json` now convert top-level list to a dict
- Updated Numpy to 1.20+ and jsonpickle to 2.0.

### Removed:

- `hasher.py` (the new `hashers.py` remains)
- Dockerfile

### Fixed:

- Check workflow issue
- Bumped dev dep versions
- Readthedocs with py3.9

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
