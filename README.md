# pocketutils

[![Version status](https://img.shields.io/pypi/status/pocketutils?label=status)](https://pypi.org/project/pocketutils)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python version compatibility](https://img.shields.io/pypi/pyversions/pocketutils?label=Python)](https://pypi.org/project/pocketutils)
[![Version on Docker Hub](https://img.shields.io/docker/v/dmyersturnbull/pocketutils?color=green&label=Docker%20Hub)](https://hub.docker.com/repository/docker/dmyersturnbull/pocketutils)
[![Version on Github](https://img.shields.io/github/v/release/dmyersturnbull/pocketutils?include_prereleases&label=GitHub)](https://github.com/dmyersturnbull/pocketutils/releases)
[![Version on PyPi](https://img.shields.io/pypi/v/pocketutils?label=PyPi)](https://pypi.org/project/pocketutils)
[![Build (Actions)](https://img.shields.io/github/actions/workflow/status/dmyersturnbull/pocketutils/push-main.yml?label=Tests)](https://github.com/dmyersturnbull/pocketutils/actions)
[![Documentation status](https://readthedocs.org/projects/pocketutils/badge)](https://pocketutils.readthedocs.io/en/stable/)
[![Coverage (coveralls)](https://coveralls.io/repos/github/dmyersturnbull/pocketutils/badge.svg?branch=main&service=github)](https://coveralls.io/github/dmyersturnbull/pocketutils?branch=main)
[![Maintainability (Code Climate)](https://api.codeclimate.com/v1/badges/eea2b741dbbbb74ad18a/maintainability)](https://codeclimate.com/github/dmyersturnbull/pocketutils/maintainability)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/dmyersturnbull/pocketutils/badges/quality-score.png?b=main)](https://scrutinizer-ci.com/g/dmyersturnbull/pocketutils/?branch=main)

Adorable little Python functions for you to copy or import,
[Apache](https://spdx.org/licenses/Apache-2.0.html)-licensed.

`pip install pocketutils[compression,encoding,formats,units,misc]`

### Basic usage

```python
import sys
from datetime import timedelta
from pocketutils import Tools, SmartIo, FrozeList, FrozeSet, FrozeDict

my_dict = FrozeDict({"5": "10"})
hash(my_dict)
assert my_dict == my_dict
assert not (my_dict < my_dict)  # orderable!
inside_a_set = {my_dict}  # hashable!

SmartIo.read_bytes("compressed.xz")  # infers compress by filename extension
data = SmartIo.read_text("text.zst")  # zstd, lz4, brotli, snappy, xz, ...
SmartIo.write(data, "compressed.zst", atomic=True)  # atomic requires it to finish

Tools.zip_strict([1, 2, 3], [5, 6])  # error <-- lengths must match
Tools.strip_brackets("( (xy)")  # "(xy" <-- strips paired only
Tools.sanitize_path("x\ty")  # "xy"  <-- very robust cross-platform sanitization
Tools.delete_surefire("my_file")  # <-- Attempts to fix permissions if needed
Tools.git_description("my_repo")  # <-- get git repo info
Tools.pretty_function(lambda s: None)  # "<λ(1)> <-- decent name for any object
Tools.roman_to_arabic("XIV")  # 14  <-- inverse function too
Tools.pretty_timedelta(delta_sec=timedelta(seconds=60 * 2 + 5))  # "02:05"  <-- handles days too
Tools.round_to_sigfigs(135.3, 2)  # "140"  <-- rounding to sigfigs
Tools.pretty_float(-float("-inf"))  # "−∞"  <-- proper unicode, no trailing 0s
Tools.stream_cmd_call(["cat", "big-file"])  # <-- buffer never fills
Tools.strip_quotes("'hello'")  # "hello"
Tools.truncate("looong string", n=10)  # "looong st…"
Tools.parse_bool("true")  # True
Tools.parse_bool_flex("yes")  # True
Tools.look(item, "purchase.buyer.first_name")  # None if purchase or buyer is None
Tools.friendly_size(n_bytes=2 * 14)  # "16.38 kb"
Tools.is_probable_null("NaN")  # True
Tools.is_true_iterable("kitten")  # False
Tools.or_null(lambda: None)  # None if it fails
Tools.trash("unwanted_file.txt")  # move to os-specific trash
Tools.pretty_dict({"contents": {"greeting": "hi"}})  # indented
Tools.save_diagnostics(Tools.get_env_info())  # record diagnostic info
Tools.is_lambda(lambda: None)  # True
Tools.longest(["a", "a+b"])  # "a+b"  # anything with len
Tools.only([1, 2])  # error -- multiple items
Tools.first(iter([]))  # None <-- better than try: next(iter(x)) except:...
Tools.trace_signals(sink=sys.stderr)  # log traceback on all signals
Tools.trace_exit(sink=sys.stderr)  # log traceback on exit
Tools.required_args(lambda a, b, c: None)  # reflection
# lots of others
```

Better yet, import specific sets of tools; e.g.:

```python
from pocketutils import FilesysTools

FilesysTools.delete_surefire("bad-path")
```

[See the docs 📚](https://github.io/dmyersturnbull/pocketutils), or just
[browse the code](https://github.com/dmyersturnbull/pocketutils/tree/main/pocketutils).
[New issues](https://github.com/dmyersturnbull/pocketutils/issues) and pull requests are welcome.
Please refer to the [contributing guide](https://github.com/dmyersturnbull/pocketutils/blob/main/CONTRIBUTING.md)
and [security policy](https://github.com/dmyersturnbull/pocketutils/blob/main/SECURITY.md).
Generated with tyrannosaurus: `tyrannosaurus new tyrannosaurus`
