# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to pocketutils
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/pocketutils
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path


def load(parts):
    if isinstance(parts, str):
        parts = [parts]
    return Path(Path(__file__).parent.parent.parent, "resources", "core", *parts)
