from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, TypeVar, Union

import pandas as pd

from pocketutils.core import PathLike
from pocketutils.core.exceptions import LengthError
from pocketutils.tools.base_tools import BaseTools

V = TypeVar("V")


class PandasTools(BaseTools):
    @classmethod
    def cfirst(cls, df: pd.DataFrame, cols: Union[str, int, Sequence[str]]) -> pd.DataFrame:
        """
        Moves some columns of a Pandas dataframe to the front, returning a copy.

        Returns:
             A copy of the dataframe with col_seq as the first columns
        """
        if isinstance(cols, str) or isinstance(cols, int):
            cols = [cols]
        if len(df) == 0:  # will break otherwise
            return df
        else:
            return df[cols + [c for c in df.columns if c not in cols]]

    @classmethod
    def df_to_dict(cls, d: pd.DataFrame) -> Dict[Any, Any]:
        if len(d.columns) != 2:
            raise LengthError(
                f"Need exactly 2 columns (key, value); got {len(d.columns)}",
                minimum=2,
                maximum=2,
            )
        keys, values = d.columns[0], d.columns[1]
        return {getattr(r, keys): getattr(r, values) for r in d.itertuples()}

    @classmethod
    def csv_to_dict(cls, path: PathLike) -> Dict[Any, Any]:
        d = pd.read_csv(Path(path))
        return cls.df_to_dict(d)

    @classmethod
    def dict_to_df(
        cls, dct: Mapping[Any, Any], keys: str = "name", values: str = "value"
    ) -> pd.DataFrame:
        dct = dict(dct)
        return (
            pd.DataFrame.from_dict(dct, orient="index")
            .reset_index()
            .rename(columns={"index": keys, 0: values})
        )

    @classmethod
    def dict_to_csv(
        cls,
        dct: Mapping[Any, Any],
        path: PathLike,
        keys: str = "name",
        values: str = "value",
    ) -> None:
        cls.dict_to_df(dct, keys, values).to_csv(Path(path))

    @classmethod
    def series_to_df(cls, series, column: str) -> pd.DataFrame:
        return pd.DataFrame(series).reset_index(drop=True).rename(columns={0: column})


__all__ = ["PandasTools"]
