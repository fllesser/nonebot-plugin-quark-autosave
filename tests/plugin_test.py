from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message  # noqa: F401
from nonebug import App
import pytest


def make_onebot_event(message: Message) -> GroupMessageEvent:
    from random import randint
    from time import time

    from nonebot.adapters.onebot.v11.event import Sender

    message_id = randint(1000000000, 9999999999)
    user_id = randint(1000000000, 9999999999)
    group_id = randint(1000000000, 9999999999)

    event = GroupMessageEvent(
        time=int(time()),
        sub_type="normal",
        self_id=123456,
        post_type="message",
        message_type="group",
        message_id=message_id,
        user_id=user_id,
        group_id=group_id,
        raw_message=message.extract_plain_text(),
        message=message,
        original_message=message,
        sender=Sender(user_id=user_id, nickname="TestUser"),
        font=123456,
    )
    return event


@pytest.mark.asyncio
async def test_load(app: App):
    from nonebot import require

    require("nonebot_plugin_quark_autosave")
