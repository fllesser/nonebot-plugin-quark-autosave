# import json

# from nonebot import logger


# async def test_get_data():
#     from nonebot_plugin_quark_autosave.client import QASClient

#     async with AutoSaveCl   ient() as client:
#         data = await client.get_data()
#     logger.info(data)


# async def test_get_share_detail():
#     from nonebot_plugin_quark_autosave.client import QASClient

#     async with AutoSaveClient() as client:
#         await client.create_task("基地第三季哈哈哈", "https://pan.quark.cn/s/e06704643151")


# async def test_update():
#     from nonebot_plugin_quark_autosave.client import AutoSaveClient
#     from nonebot_plugin_quark_autosave.config import data_dir

#     async with AutoSaveClient() as client:
#         with open(
#             data_dir / "update_playload.json",
#         ) as f:
#             data = json.load(f)
#             await client.client.post("/update", json=data)


async def test_add_task():
    from nonebot_plugin_quark_autosave.client import QASClient

    async with QASClient() as client:
        await client.add_task("基地第三季测试", "https://pan.quark.cn/s/e06704643151")
