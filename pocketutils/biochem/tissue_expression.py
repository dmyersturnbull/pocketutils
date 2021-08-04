from __future__ import annotations

from typing import Callable, Optional

import pandas as pd

from pocketutils.core import PathLike
from pocketutils.core.exceptions import LookupFailedError
from pocketutils.core.web_resource import WebResource


class TissueTable(pd.DataFrame):
    """
    Contains a Pandas DataFrame of tissue- and cell type-level expression for genes from the Human Protein Atlas.

    Example:
        tt = TissueTable()
        tt.tissue('MKNK2') # returns a DataFrame with mean expression of MKNK2 per tissue type. MKN2 is the HGNC symbol.
    """

    URL = "https://www.proteinatlas.org/download/normal_tissue.tsv.zip"
    MEMBER_NAME = "normal_tissue.tsv"
    DEFAULT_PATH = "normal_tissue.tsv.gz"

    @classmethod
    def load(
        cls,
        path: Optional[PathLike] = None,
        filter_fn: Callable[[pd.DataFrame], pd.DataFrame] = pd.DataFrame.dropna,
    ) -> TissueTable:
        """
        Gets a DataFrame of Human Protein Atlas tissue expression data,
        indexed by Gene name and with the 'Gene' and 'Reliability' columns dropped.
        The expression level ('Level') is replaced using this map: {'Not detected': 0, 'Low': 1, 'Medium': 2, 'High': 3}.
        Downloads the file from http://www.proteinatlas.org/download/normal_tissue.tsv.zip
        and reloads from normal_tissue.tsv.gz thereafter.
        """
        if path is None:
            path = TissueTable.DEFAULT_PATH
        resource = WebResource(TissueTable.URL, TissueTable.MEMBER_NAME, path)
        resource.download()
        tissue = pd.read_csv(path, sep="\t")
        tissue = tissue.drop("Gene", axis=1).drop("Reliability", axis=1)
        tissue = filter_fn(tissue)
        tissue["Level"] = (
            tissue["Level"]
            .map({"Not detected": 0, "Low": 1, "Medium": 2, "High": 3}.get)
            .astype(float)
        )
        return TissueTable(tissue.set_index("Gene name"))

    def level(self, gene_name: str, group_by: str) -> TissueTable:
        """Returns a DataFrame of the mean expression levels by tissue or cell type."""
        if gene_name not in self.index.get_level_values("Gene name"):
            raise LookupFailedError(f"Gene with HGNC symbol {gene_name} not found.")
        gene = self[self.index.get_level_values("Gene name") == gene_name]
        if gene is None:
            raise AssertionError(f"Gene is None for gene_name {gene_name}, groupby {group_by}")
        return TissueTable(gene.groupby(group_by).mean().sort_values("Level", ascending=False))

    def tissue(self, name: str) -> TissueTable:
        return self.level(name, group_by="Tissue")

    def cell_type(self, name: str) -> TissueTable:
        return self.level(name, group_by="Cell type")


__all__ = ["TissueTable"]
