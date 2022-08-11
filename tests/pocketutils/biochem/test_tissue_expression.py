import logging
import os
from pathlib import Path

import pytest

from pocketutils.biochem.tissue_expression import TissueTable
from pocketutils.tools.common_tools import CommonTools

logger = logging.getLogger("pocketutils.test")
run_integration = CommonTools.parse_bool(
    os.environ.get("POCKETUTILS_RUN_INTEGRATION_TESTS", "false")
)


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
