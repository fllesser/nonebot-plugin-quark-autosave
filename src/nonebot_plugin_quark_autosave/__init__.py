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
from .entity import MagicRegex, PatternIdx, RunWeek, TaskItem

__plugin_meta__ = PluginMetadata(
    name="Quark Auto Save",
    description="配合 quark-auto-save(https://github.com/Cp0204/quark-auto-save), 快速添加自动保存任务",
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
        Args["pattern_idx?", Literal["0", "1", "2", "3", "4"]],
        Args["inner?", Literal["1", "0"]],
        Args["startfid_idx?", int],
        Args["runweek?", str],
    ),
    permission=SUPERUSER,
)

TASK_KEY = "QUARK_AUTO_SAVE_TASK"


def Task() -> TaskItem:
    def _get_task(state: T_State) -> TaskItem:
        return state[TASK_KEY]

    return Depends(_get_task)


@qas.handle()
async def _(
    shareurl: Match[str],
    taskname: Match[str],
    pattern_idx: Match[Literal["0", "1", "2", "3"]],
    inner: Match[Literal["1", "0"]],
    startfid_idx: Match[int],
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
    if startfid_idx.available:
        qas.set_path_arg("startfid_idx", startfid_idx.result)
    if runweek.available:
        qas.set_path_arg("runweek", runweek.result)


@qas.got_path("taskname", "请输入任务名称")
async def _(taskname: str, state: T_State):
    state["taskname"] = taskname


@qas.got_path("shareurl", "请输入分享链接")
async def _(shareurl: str, state: T_State):
    state["shareurl"] = shareurl
    state[TASK_KEY] = TaskItem.template(state["taskname"], shareurl)


@qas.got_path("pattern_idx", f"请输入模式索引: \n{MagicRegex.display_patterns_alias()}")
async def _(pattern_idx: Literal["0", "1", "2", "3", "4"], task: TaskItem = Task()):
    idx: PatternIdx = cast(PatternIdx, int(pattern_idx))
    task.set_pattern(idx)
    async with QASClient() as client:
        detail = await client.get_share_detail(task)
        task.detail_info = detail
        await qas.send(f"转存预览:\n{task.display_file_list()}")


@qas.got_path("inner", "是(1)否(0)以二级目录作为视频文件夹")
async def _(inner: Literal["1", "0"], task: TaskItem = Task()):
    if inner == "1":
        task.shareurl = f"{task.shareurl}#/list/share/{task.detail().share.first_fid}"

    async with QASClient() as client:
        detail = await client.get_share_detail(task)
        task.detail_info = detail
        await qas.send(f"转存预览:\n{task.display_file_list()}")


@qas.got_path("startfid_idx", prompt="请输入起始文件索引(注: 只会转存更新时间在起始文件之后的文件)")
async def _(startfid_idx: int, task: TaskItem = Task()):
    task.set_startfid(startfid_idx)
    await qas.send(f"转存预览:\n{task.display_file_list()}")


@qas.got_path("runweek", "请输入运行周期(1-7), 如 67 代表每周六、日运行")
async def _(runweek: str, task: TaskItem = Task()):
    if matched := re.match(r"^[1-7]*$", runweek):
        task.runweek = cast(RunWeek, sorted({int(week) for week in matched.group(0)}))
    else:
        await qas.reject_path("runweek", "请输入正确的运行周期")


@qas.handle()
async def _(task: TaskItem = Task()):
    async with QASClient() as client:
        task = await client.add_task(task)
    await qas.finish(f"🎉 添加任务成功 🎉\n{task}")
