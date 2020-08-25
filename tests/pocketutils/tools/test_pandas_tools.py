import pandas as pd
import pytest

from pocketutils.core.exceptions import LengthError
from pocketutils.tools.pandas_tools import PandasTools

raises = pytest.raises


class TestPandasTools:
    def test_cfirst(self):
        df = pd.DataFrame([pd.Series({"abc": "xxx", "xyz": "qqq"})])
        assert list(df.columns.values) == ["abc", "xyz"]
        assert list(PandasTools.cfirst(df, ["xyz", "abc"]).columns.values) == ["xyz", "abc"]
        assert list(PandasTools.cfirst(df, ["xyz"]).columns.values) == ["xyz", "abc"]

    def test_df_to_dict(self):
        df = pd.DataFrame([pd.Series({"abc": "xxx", "xyz": "qqq"})])
        assert PandasTools.df_to_dict(df) == {"xxx": "qqq"}
        with raises(LengthError):
            assert PandasTools.df_to_dict(df[["abc"]]) == {"abc": "xxx", "xyz": "qqq"}
        df = pd.DataFrame([pd.Series({"abc": "xxx", "xyz": "qqq", "lll": "www"})])
        with raises(LengthError):
            assert PandasTools.df_to_dict(df)

    def test_series_to_df(self):
        df = PandasTools.series_to_df(pd.Series({"abc": "xxx", "xyz": "qqq"}), "abc")
        assert len(df) == 2
        assert list(df.columns) == ["abc"]


if __name__ == "__main__":
    pytest.main()
