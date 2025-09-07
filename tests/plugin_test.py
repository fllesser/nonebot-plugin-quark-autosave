from nonebug import App
import pytest


@pytest.mark.asyncio
async def test_load(app: App):
    from nonebot import require

    require("nonebot_plugin_quark_autosave")
