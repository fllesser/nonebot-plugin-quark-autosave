from fake import SUPER_USER_ID, fake_private_message_event_v11
import httpx
from nonebot import get_adapter
from nonebot.adapters.onebot.v11 import Adapter, Bot
from nonebot.compat import model_dump
from nonebug import App
import pytest
import respx


@respx.mock(assert_all_called=True, base_url="http://debian:5005")
@pytest.mark.asyncio
async def test_add_task(app: App, respx_mock: respx.MockRouter):
    from nonebot_plugin_quark_autosave.model import DetailInfo, MagicRegex, TaskItem

    task = TaskItem.template("基地第三季", "https://pan.quark.cn/s/e06704643151")

    detail_info_json = {
        "is_owner": 1,
        "share": {
            "title": "基地第三季",
            "share_type": 1,
            "share_id": "https://pan.quark.cn/s/e06704643151",
            "pwd_id": "",
            "share_url": "",
            "url_type": 1,
            "first_fid": "",
            "expired_type": 1,
            "file_num": 0,
            "created_at": 0,
            "updated_at": 0,
            "expired_at": 0,
            "expired_left": 0,
            "audit_status": 1,
            "status": 1,
            "click_pv": 0,
            "save_pv": 0,
            "download_pv": 0,
            "first_file": {},
        },
        "list": [
            {"fid": "111", "file_name": "1.mp4", "updated_at": 111, "file_name_re": None, "file_name_saved": None},
            {"fid": "222", "file_name": "2.mp4", "updated_at": 222, "file_name_re": None, "file_name_saved": None},
            {"fid": "333", "file_name": "3.mp4", "updated_at": 333, "file_name_re": None, "file_name_saved": None},
        ],
        "paths": [],
        "stoken": "",
    }
    detail_info = DetailInfo(**detail_info_json)

    task.detail_info = detail_info

    respx_mock.post("/get_share_detail").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "data": detail_info_json,
            },
        )
    )

    async with app.test_matcher() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)

        event = fake_private_message_event_v11(
            message="qas 基地第三季 https://pan.quark.cn/s/e06704643151", user_id=SUPER_USER_ID
        )
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            f"请输入模式索引: \n{MagicRegex.display_patterns_alias()}",
        )

        event = fake_private_message_event_v11(message="0", user_id=SUPER_USER_ID)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            f"转存预览:\n{task.display_file_list()}",
        )
        ctx.should_call_send(
            event,
            "是(1)否(0)以二级目录作为视频文件夹",
        )
        event = fake_private_message_event_v11(message="1", user_id=SUPER_USER_ID)

        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            f"转存预览:\n{task.display_file_list()}",
        )
        ctx.should_call_send(
            event,
            "请输入起始文件索引(注: 只会转存更新时间在起始文件之后的文件)",
        )

        event = fake_private_message_event_v11(message="1", user_id=SUPER_USER_ID)
        task.set_startfid(1)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            f"转存预览:\n{task.display_file_list()}",
        )
        ctx.should_call_send(
            event,
            "请输入运行周期(1-7), 如 67 代表每周六、日运行",
        )

        event = fake_private_message_event_v11(message="67", user_id=SUPER_USER_ID)
        task.runweek = [6, 7]
        respx_mock.post("/api/add_task").mock(
            return_value=httpx.Response(
                200,
                json={
                    "success": True,
                    "data": model_dump(task),
                },
            )
        )
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            f"🎉 添加任务成功 🎉\n{task}",
        )


def mock_data(respx_mock: respx.MockRouter):
    from nonebot_plugin_quark_autosave.model import AutosaveData, TaskItem

    tasks = [
        TaskItem.template("基地第一季", "https://pan.quark.cn/s/e06704643151", pattern_idx=1),
        TaskItem.template("基地第二季", "https://pan.quark.cn/s/e06704643151", pattern_idx=2),
        TaskItem.template("基地第三季", "https://pan.quark.cn/s/e06704643151", pattern_idx=3),
    ]

    respx_mock.get("/data").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "data": model_dump(
                    AutosaveData(
                        cookie=[],
                        api_token="",
                        crontab="",
                        tasklist=tasks,
                        magic_regex={},
                        source={},
                        push_config={},
                        plugins={},
                        task_plugins_config_default={},
                    )
                ),
            },
        )
    )

    return tasks


@respx.mock(assert_all_called=True, base_url="http://debian:5005")
@pytest.mark.asyncio
async def test_list_tasks(app: App, respx_mock: respx.MockRouter):
    tasks = mock_data(respx_mock)

    async with app.test_matcher() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)

        event = fake_private_message_event_v11(message="qas.list", user_id=SUPER_USER_ID)
        ctx.receive_event(bot, event)

        task_strs = "\n".join(f"{i}. {task.display_simple()}" for i, task in enumerate(tasks, 1))
        ctx.should_call_send(
            event,
            f"当前任务列表:\n{task_strs}",
        )


@respx.mock(assert_all_called=True, base_url="http://debian:5005")
async def test_delete_task(app: App, respx_mock: respx.MockRouter):
    tasks = mock_data(respx_mock)

    respx_mock.post("/update").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "message": "更新成功",
            },
        )
    )

    async with app.test_matcher() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)

        event = fake_private_message_event_v11(message="qas.del 1", user_id=SUPER_USER_ID)
        ctx.receive_event(bot, event)

        ctx.should_call_send(
            event,
            f"删除任务 {tasks[0].taskname} 成功",
        )


@respx.mock(assert_all_called=True, base_url="http://debian:5005")
async def test_run_script(app: App, respx_mock: respx.MockRouter):
    respx_mock.post("/run_script_now").mock(
        return_value=httpx.Response(
            200,
            text="运行成功",
        )
    )

    async with app.test_matcher() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)

        event = fake_private_message_event_v11(message="qas.run", user_id=SUPER_USER_ID)
        ctx.receive_event(bot, event)

        ctx.should_call_send(event, "运行成功")
