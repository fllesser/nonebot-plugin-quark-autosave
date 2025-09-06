from collections.abc import Callable
from functools import wraps

from nonebot.matcher import current_matcher


class QuarkAutosaveException(Exception):
    pass


def handle_exception():
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except QuarkAutosaveException as e:
                matcher = current_matcher.get()
                await matcher.finish(str(e))

        return wrapper

    return decorator
