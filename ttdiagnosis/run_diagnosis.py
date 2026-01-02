
import os
import json
import logging
from ttdiagnosis.ttdiagnosis import TTDiagnosis


logger = logging.getLogger(__name__)


async def run_diagnosis(silent=False):
    ttdiagnosis = TTDiagnosis()
    diagnostic = await ttdiagnosis.run()
    if not silent:
        logger.debug(json.dumps(diagnostic, indent=4))

    rsp = await ttdiagnosis.send()
    if rsp:
        logger.debug(rsp.json())

if __name__ == "__main__":
    run_diagnosis()
