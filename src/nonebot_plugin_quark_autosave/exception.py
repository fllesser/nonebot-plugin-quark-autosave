from nonebot import logger


class QuarkAutosaveException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        logger.error(message)
