from pathlib import Path

import pandas as pd
import pytest

from pocketutils.core.web_resource import *


class TestWebResource:
    pass
    # TODO: certificate problem
    """"
    def test(self):
        # TODO incomplete coverage
        path = Path("tt.txt.gz")
        t = WebResource(
            "https://www.proteinatlas.org/download/normal_tissue.tsv.zip",
            "normal_tissue.tsv",
            path,
        )
        try:
            t.download(redownload=True)

            df = pd.read_csv(path, sep="\t")
            # note: this isn't a great test; the # of rows can change
            assert len(df) == 1118517
            assert t.datetime_downloaded()
            assert t.exists()
            t.delete()
            assert not t.exists()
        finally:
            if path.exists():
                try:
                    path.unlink()
                except OSError:
                    print(f"Warning: could not delete {path.absolute()}")
    """


if __name__ == "__main__":
    pytest.main()
