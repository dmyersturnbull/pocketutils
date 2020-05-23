import pytest
from pathlib import Path
from dscience.biochem.tissue_expression import *


class TestTissueExpression:
    def test(self):
        try:
            t = TissueTable.load()
            assert len(t) > 0
            assert t.tissue("MKNK2") is not None
        finally:
            if Path(TissueTable.DEFAULT_PATH).exists():
                Path(TissueTable.DEFAULT_PATH).unlink()
            if Path(TissueTable.DEFAULT_PATH + ".info").exists():
                Path(TissueTable.DEFAULT_PATH + ".info").unlink()


if __name__ == "__main__":
    pytest.main()
