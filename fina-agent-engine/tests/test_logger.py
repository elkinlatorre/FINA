import pytest
from app.core.logger import get_logger
import logging

def test_get_logger():
    logger = get_logger("TEST_LOGGER")
    assert logger.name == "TEST_LOGGER"
    assert logger.level == logging.INFO or logger.level == logging.DEBUG
