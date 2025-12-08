import httpx
import respx
import pytest
from fake import SUPER_USER_ID, fake_private_message_event_v11
from nonebot import get_adapter
from nonebug import App
from nonebot.compat import model_dump
from nonebot.adapters.onebot.v11 import Bot, Adapter


def tasks_example():
    from nonebot_plugin_quark_autosave.model import TaskItem

    return [
        TaskItem.template("戏台", "https://pan.quark.cn/s/cd50a720b85f", pattern_idx=1),
        TaskItem.template("冰女", "https://pan.quark.cn/s/3ca9c76abd12", pattern_idx=2),
        TaskItem.template("基地第三季", "https://pan.quark.cn/s/e06704643151", pattern_idx=3),
    ]


@pytest.fixture(scope="session", autouse=True)
@respx.mock(base_url="http://quark-auto-save:5005")
def mock_qas_server():
    from nonebot_plugin_quark_autosave.model import AutosaveData

    tasks = tasks_example()

    respx.get("/data").mock(
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


@respx.mock
@pytest.mark.asyncio
async def test_add_task(app: App):
    from nonebot_plugin_quark_autosave.model import TaskItem, DetailInfo, MagicRegex

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
            {
                "fid": f"{i}{i}{i}",
                "file_name": f"{i}.mp4",
                "updated_at": i * 1000,
                "file_name_re": None,
                "file_name_saved": None,
            }
            for i in range(30)
        ],
        "paths": [],
        "stoken": "",
    }
    detail_info = DetailInfo(**detail_info_json)

    respx.post("/get_share_detail").mock(
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

        # 输入任务名称和分享链接
        event = fake_private_message_event_v11(
            message="qas 基地第三季 https://pan.quark.cn/s/e06704643151", user_id=SUPER_USER_ID
        )
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            f"请输入模式索引: \n{MagicRegex.display_patterns_alias()}",
        )

        task = TaskItem.template("基地第三季", "https://pan.quark.cn/s/e06704643151")
        task.detail_info = detail_info

        # 输入模式索引
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

        # 输入是否以二级目录作为视频文件夹
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

        # 输入起始文件索引
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

        # 输入错误的运行周期
        event = fake_private_message_event_v11(message="运行周期", user_id=SUPER_USER_ID)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            "请输入正确的运行周期",
        )

        # 输入正确的运行周期
        event = fake_private_message_event_v11(message="67", user_id=SUPER_USER_ID)
        task.runweek = [6, 7]
        respx.post("/api/add_task").mock(
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


@respx.mock
async def test_list_tasks(app: App):
    tasks = tasks_example()
    input = "qas.list"
    task_strs = "\n".join(f"{i}. {task.display_simple()}" for i, task in enumerate(tasks, 1))
    output = f"当前任务列表:\n{task_strs}"

    async with app.test_matcher() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)

        event = fake_private_message_event_v11(message=input, user_id=SUPER_USER_ID)
        ctx.receive_event(bot, event)

        ctx.should_call_send(
            event,
            output,
        )


@respx.mock
async def test_delete_task(app: App):
    tasks = tasks_example()
    cmd_arg = 1
    input = f"qas.del {cmd_arg}"
    output = f"删除任务 {tasks[cmd_arg - 1].taskname} 成功"

    respx.post("/update").mock(
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

        event = fake_private_message_event_v11(message=input, user_id=SUPER_USER_ID)
        ctx.receive_event(bot, event)

        ctx.should_call_send(event, output)


async def test_delete_task_without_index(app: App):
    input = "qas.del"
    output = "必需指定有效的任务索引"

    async with app.test_matcher() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)

        event = fake_private_message_event_v11(message=input, user_id=SUPER_USER_ID)
        ctx.receive_event(bot, event)

        ctx.should_call_send(event, output)


@respx.mock
async def test_delete_task_with_invalid_index(app: App):
    input = "qas.del 1000"
    output = "QAS: 任务索引 1000 无效"

    async with app.test_matcher() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)

        event = fake_private_message_event_v11(message=input, user_id=SUPER_USER_ID)
        ctx.receive_event(bot, event)

        ctx.should_call_send(event, output)


@respx.mock
async def test_run_script(app: App):
    input = "qas.run"
    output = (
        "🧩 载入插件\n"
        "SmartStrm 触发任务: 连接成功 v0.0.7\n"
        "转存账号: 安谧的老虎\n"
        "#1------------------\n"
        "任务名称: 基地第三季\n"
        "分享链接: https://pan.quark.cn/s/e06704643151#/list/share/4afa4cd5bf0e4e7bb1a2ccef8f094d74\n"
        "保存路径: /夸克自动转存/基地3\n"
        "正则匹配: tv_regex\n"
        "运行周期: WK[5] ~\n"
    )

    # 期望发送
    hoped_send = [
        "🧩 载入插件\nSmartStrm 触发任务: 连接成功 v0.0.7\n转存账号: 安谧的老虎",
        "任务名称: 基地第三季\n保存路径: /夸克自动转存/基地3\n正则匹配: tv_regex\n运行周期: WK[5] ~",
    ]

    respx.post("/run_script_now").mock(
        return_value=httpx.Response(
            200,
            text=output,
        )
    )

    async with app.test_matcher() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)

        event = fake_private_message_event_v11(message=input, user_id=SUPER_USER_ID)
        ctx.receive_event(bot, event)
        for line in hoped_send:
            ctx.should_call_send(event, line)


@respx.mock
async def test_run_script_with_index(app: App):
    cmd_arg = 1
    input = f"qas.run {cmd_arg}"
    output = f"任务 {cmd_arg} 运行成功"
    task_idx = cmd_arg - 1

    tasks = tasks_example()
    task_in_dict = model_dump(tasks[task_idx])
    del task_in_dict["runweek"]
    respx.post("/run_script_now", json={"tasklist": [task_in_dict]}).mock(
        return_value=httpx.Response(
            200,
            text=output,
        )
    )

    async with app.test_matcher() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)

        event = fake_private_message_event_v11(message=input, user_id=SUPER_USER_ID)
        ctx.receive_event(bot, event)

        ctx.should_call_send(event, output)


@respx.mock
async def test_http_exception(app: App):
    input = "qas.list"
    output = "请求失败, 详见后台输出"

    respx.get("/data").mock(return_value=httpx.Response(500))

    async with app.test_matcher() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)

        event = fake_private_message_event_v11(message=input, user_id=SUPER_USER_ID)
        ctx.receive_event(bot, event)

        ctx.should_call_send(event, output)


@respx.mock
async def test_qas_exception(app: App):
    input = "qas.list"
    output = "测试QAS异常"

    respx.get("/data").mock(
        return_value=httpx.Response(
            300,
            json={"success": False, "message": output},
        )
    )

    async with app.test_matcher() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)

        event = fake_private_message_event_v11(message=input, user_id=SUPER_USER_ID)
        ctx.receive_event(bot, event)

        ctx.should_call_send(event, f"QAS: {output}")
