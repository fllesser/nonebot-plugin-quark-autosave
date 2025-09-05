import re
from typing import Literal, cast

from nonebot import logger, require  # noqa: F401
from nonebot.params import Depends
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata, inherit_supported_adapters
from nonebot.typing import T_State

require("nonebot_plugin_alconna")
from .client import QASClient
from .config import Config
from .entity import MagicRegex, PatternIdx, TaskItem

__plugin_meta__ = PluginMetadata(
    name="Quark Auto Save",
    description="配合 quark-auto-save, 快速添加自动保存任务",
    usage="qas",
    type="application",  # library
    homepage="https://github.com/fllesser/nonebot-plugin-quark-autosave",
    config=Config,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
    # supported_adapters={"~onebot.v11"}, # 仅 onebot
    extra={"author": "fllesser <fllessive@mail.com>"},
)

from arclet.alconna import Alconna, Args
from nonebot_plugin_alconna import Match, on_alconna

# 快速添加 auto save 任务
qas = on_alconna(
    Alconna(
        "qas",
        Args["taskname?", str],
        Args["shareurl?", str],
        Args["pattern_idx?", Literal["0", "1", "2", "3"]],
        Args["inner?", Literal["1", "0"]],
        Args["add_startfid?", Literal["1", "0"]],
        Args["runweek?", str],
    ),
    permission=SUPERUSER,
)

TASK_KEY = "QUARK_AUTO_SAVE_TASK"


def Task() -> TaskItem:
    return Depends(_get_task)


def _get_task(state: T_State) -> TaskItem:
    return state[TASK_KEY]


@qas.handle()
async def _(
    shareurl: Match[str],
    taskname: Match[str],
    pattern_idx: Match[Literal["0", "1", "2", "3"]],
    inner: Match[Literal["是", "否"]],
    add_startfid: Match[Literal["是", "否"]],
    runweek: Match[str],
):
    if shareurl.available:
        qas.set_path_arg("shareurl", shareurl.result)
    if taskname.available:
        qas.set_path_arg("taskname", taskname.result)
    if pattern_idx.available:
        qas.set_path_arg("pattern_idx", pattern_idx.result)
    if inner.available:
        qas.set_path_arg("inner", inner.result)
    if add_startfid.available:
        qas.set_path_arg("add_startfid", add_startfid.result)
    if runweek.available:
        qas.set_path_arg("runweek", runweek.result)


@qas.got_path("taskname", "请输入任务名称")
async def _(taskname: str, state: T_State):
    state["taskname"] = taskname


@qas.got_path("shareurl", "请输入分享链接")
async def _(shareurl: str, state: T_State):
    state["shareurl"] = shareurl
    state[TASK_KEY] = TaskItem.template(state["taskname"], shareurl)


@qas.got_path("pattern_idx", f"请输入模式索引: \n{MagicRegex.patterns_alias_str()}")
async def _(pattern_idx: Literal["0", "1", "2", "3"], task: TaskItem = Task()):
    idx: PatternIdx = cast(PatternIdx, int(pattern_idx))
    task.set_pattern(idx)
    async with QASClient() as client:
        detail = await client.get_share_detail(task)
        await qas.send(f"处理预览:\n{detail.display_file_list()}")


@qas.got_path("inner", "是(1)否(0)以二级目录作为视频文件夹")
async def _(inner: Literal["1", "0"], task: TaskItem = Task()):
    async with QASClient() as client:
        detail = await client.get_share_detail(task)
        if inner == "1":
            task.shareurl = f"{task.shareurl}#/list/share/{detail.share.first_fid}"
        else:
            task.shareurl = task.shareurl
        detail = await client.get_share_detail(task)
        await qas.send(f"处理预览:\n{detail.display_file_list()}")


@qas.got_path("add_startfid", prompt="是(1)否(0)添加起始文件ID")
async def _(add_startfid: Literal["1", "0"], task: TaskItem = Task()):
    if add_startfid == "1":
        async with QASClient() as client:
            detail = await client.get_share_detail(task)
            task.startfid = detail.last_update_file_fid
        await qas.send(f"处理预览:\n{detail.display_file_list(task.startfid)}")


@qas.got_path("runweek", "请输入运行周期(1-7), 如 67 代表每周六、日运行")
async def _(runweek: str, task: TaskItem = Task()):
    pattern = r"^[1-7]*$"
    if matched := re.match(pattern, runweek):
        task.runweek = cast(list[Literal[1, 2, 3, 4, 5, 6, 7]], sorted({int(week) for week in matched.group(0)}))
    else:
        await qas.reject_path("runweek")


@qas.handle()
async def _(task: TaskItem = Task()):
    async with QASClient() as client:
        task = await client.add_task(task)
    await qas.finish(f"🎉 添加任务成功 🎉\n{task}")
