import os
from pathlib import Path
import logging

import pytest

from pocketutils.biochem.tissue_expression import *

logger = logging.getLogger("pocketutils.test")
run_integration = os.environ.get("POCKETUTILS_RUN_INTEGRATION_TESTS", "").lower() in [
    "true",
    "1",
    "yes",
]


class TestTissueExpression:
    def test(self):
        if not run_integration:
            logger.info("Skipping TissueTable integration test")
            return
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
