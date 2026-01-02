from ttdiagnosis.run_diagnosis import run_diagnosis
import logging
import time
import signal
import sys

import asyncio

from ttgateway.http_handler import HttpHandler
from ttgateway.config import config

PERIOD = 1200 # 20 min
running = False

logger = logging.getLogger(__name__)
http_handler = None

def config_logger():
    _logger = logging.getLogger()
    _logger.setLevel(logging.DEBUG)
    if _logger.hasHandlers():
        _logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - ' +
            '%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
    logging.getLogger("urllib3").setLevel(logging.INFO)
    logging.getLogger('asyncio').setLevel(logging.INFO)

def start_backend_handler():
    global http_handler
    http_handler = HttpHandler()
    http_handler.setLevel(http_handler.config_level)

    http_handler.start()
    _logger = logging.getLogger()
    _logger.addHandler(http_handler)

def stop_backend_handler():
    global http_handler

    _logger = logging.getLogger()
    _logger.removeHandler(http_handler)
    http_handler.stop()


def int_handler(signal, frame):
    global running
    logger.info("Int signal received")
    running = False

def hup_handler(signal, frame):
    global http_handler
    logger.info("Hup signal received")
    config.read()
    http_handler.update_credentials()
    http_handler.setLevel(http_handler.config_level)
    logger.debug(f"Log level set to {http_handler.config_level}")

def run():
    config_logger()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:

        loop.run_until_complete(run_diagnosis(silent=False))
    except:
        logger.exception("Error executing diagnosis")

async def _loop():
    global running

    start_backend_handler()

    signal.signal(signal.SIGINT, int_handler)
    signal.signal(signal.SIGHUP, hup_handler)
    running = True

    # Wait 60s for heimdall init
    next_time = time.monotonic() + 60
    while running:
        curr_time = time.monotonic()
        if curr_time >= next_time:
            while next_time <= curr_time:
                next_time = next_time + PERIOD
            logger.info("Executing diagnosis")
            try:
                await run_diagnosis(silent=True)
            except:
                logger.exception("Error executing diagnosis")
        await asyncio.sleep(2)

    stop_backend_handler()

def start():
    config_logger()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(_loop())
    except:
        logger.exception("Error executing diagnosis")

    sys.exit(0)

