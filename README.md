# pocketutils

[![Version status](https://img.shields.io/pypi/status/pocketutils?label=status)](https://pypi.org/project/pocketutils)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python version compatibility](https://img.shields.io/pypi/pyversions/pocketutils?label=Python)](https://pypi.org/project/pocketutils)
[![Version on Docker Hub](https://img.shields.io/docker/v/dmyersturnbull/pocketutils?color=green&label=Docker%20Hub)](https://hub.docker.com/repository/docker/dmyersturnbull/pocketutils)
[![Version on Github](https://img.shields.io/github/v/release/dmyersturnbull/pocketutils?include_prereleases&label=GitHub)](https://github.com/dmyersturnbull/pocketutils/releases)
[![Version on PyPi](https://img.shields.io/pypi/v/pocketutils?label=PyPi)](https://pypi.org/project/pocketutils)  
[![Build (Actions)](https://img.shields.io/github/workflow/status/dmyersturnbull/pocketutils/Build%20&%20test?label=Tests)](https://github.com/dmyersturnbull/pocketutils/actions)
[![Documentation status](https://readthedocs.org/projects/pocketutils/badge)](https://pocketutils.readthedocs.io/en/stable/)
[![Coverage (coveralls)](https://coveralls.io/repos/github/dmyersturnbull/pocketutils/badge.svg?branch=main&service=github)](https://coveralls.io/github/dmyersturnbull/pocketutils?branch=main)
[![Maintainability (Code Climate)](https://api.codeclimate.com/v1/badges/eea2b741dbbbb74ad18a/maintainability)](https://codeclimate.com/github/dmyersturnbull/pocketutils/maintainability)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/dmyersturnbull/pocketutils/badges/quality-score.png?b=main)](https://scrutinizer-ci.com/g/dmyersturnbull/pocketutils/?branch=main)

Adorable little Python functions for you to copy or import.

`pip install pocketutils`. To get the optional packages, use:
`pip install pocketutils[tools,biochem,misc,notebooks,plotting]`


[Apache](https://spdx.org/licenses/Apache-2.0.html)-licensed. To


Among the more useful are `zip_strict`, `frozenlist`, `SmartEnum`, `is_lambda`, `strip_paired_brackets`,
`sanitize_path_node`, `TomlData`, `NestedDocDict`, `PrettyRecordFactory`, `parallel_with_cursor`,
`loop_timing`, `HashableFile`, `QueryExecutor`, `WebResource`, `get_env_info`, `git_description`, `git_hash`,
`delete_surefire`, `roman_to_arabic`, `pretty_float`, `pretty_function`, `round_to_sigfigs`,
`prompt_yes_no`, and `stream_cmd_call`.

Also has functions for plotting, machine learning, and bioinformatics.
Some of the more useful are `ConfusionMatrix`, `DecisionFrame`,
[`PeakFinder`](https://en.wikipedia.org/wiki/Topographic_prominence), `AtcParser` (for PubChem ATC codes),
`WellBase1` (for multiwell plates), and [`TissueTable`](https://www.proteinatlas.org/).

[See the docs 📚](https://pocketutils.readthedocs.io/en/stable/), or just
[browse the code](https://github.com/dmyersturnbull/pocketutils/tree/main/pocketutils).

[New issues](https://github.com/dmyersturnbull/pocketutils/issues) and pull requests are welcome.
Please refer to the [contributing guide](https://github.com/dmyersturnbull/pocketutils/blob/main/CONTRIBUTING.md)
and [security policy](https://github.com/dmyersturnbull/pocketutils/blob/main/SECURITY.md).  
Generated with tyrannosaurus: `tyrannosaurus new tyrannosaurus`
