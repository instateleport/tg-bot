import os

from loguru import logger

from config import PROJECT_PATH

LOGGING_FILE_PATH = os.path.join(PROJECT_PATH, 'logs.log')
logger.add(
    LOGGING_FILE_PATH,
    compression='zip',
    rotation='10 days',
    level='INFO'
)