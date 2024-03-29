# SPDX-FileCopyrightText: Copyright 2020-2023, Contributors to typed-dfs
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/typed-dfs
# SPDX-License-Identifier: Apache-2.0
import inspect

import numpy as np
import pytest
from pocketutils.tools.json_tools import JsonTools, NanInfHandling


class TestJsonTools:
    def test_preserve_inf(self):
        matrix = np.zeros((2, 2))
        # assert (JsonTools.prepare(matrix) == matrix.astype(str)).all()
        matrix = np.asarray([[2, float("inf")], [float("inf"), 2]])
        # assert (JsonTools.preserve_inf(matrix) == matrix.astype(str)).all()
        # TODO: nested tests

    def test_new_default(self):
        class X:
            def __str__(self):
                return "from-str"

            def __repr__(self):
                return "from-repr"

        default = JsonTools.new_default()
        x = default(None)
        assert x is None
        assert default(X()) == "from-str"
        default = JsonTools.new_default(last=repr)
        assert default(X()) == "from-repr"

        def fixer(obj):
            if isinstance(obj, X):
                return "gotcha!"

        default = JsonTools.new_default(fixer)
        assert default(X()) == "gotcha!"

    def test_to_json(self):
        assert JsonTools.encoder().as_str("hi") == '"hi"\n'
        assert JsonTools.encoder().as_str(["hi", "bye"]) == '[\n  "hi",\n  "bye"\n]\n'
        data = {
            "list": [
                {
                    "numbers": {
                        1: np.asarray([float("inf"), 0]),
                        2: np.asarray([1, 1]),
                        3: np.half(float("inf")),
                        4: np.half(float("-inf")),
                        5: float("inf"),
                        6: float("-inf"),
                        7: 1,
                    },
                },
            ],
        }
        encoder = JsonTools.encoder(
            inf_handling=NanInfHandling.convert_to_str,
            nan_handling=NanInfHandling.convert_to_str,
        )
        x = encoder.as_str(data)
        assert (
            x
            == inspect.cleandoc(
                """
            {
              "list": [
                {
                  "numbers": {
                    "1": [
                      "inf",
                      "0.0"
                    ],
                    "2": [
                      1,
                      1
                    ],
                    "3": "inf",
                    "4": "-inf",
                    "5": "inf",
                    "6": "-inf",
                    "7": 1
                  }
                }
              ]
            }
            """,
            )
            + "\n"
        )


if __name__ == "__main__":
    pytest.main()
