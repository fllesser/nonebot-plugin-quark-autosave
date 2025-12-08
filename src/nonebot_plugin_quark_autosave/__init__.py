import re
from typing import Literal, cast

from nonebot import logger, require, on_command  # noqa: F401
from nonebot.params import Depends, CommandArg, RegexMatched  # noqa: F401
from nonebot.plugin import PluginMetadata, inherit_supported_adapters
from nonebot.typing import T_State
from nonebot.matcher import Matcher
from nonebot.adapters import Message
from nonebot.permission import SUPERUSER

require("nonebot_plugin_alconna")
from .model import RunWeek, TaskItem, MagicRegex, PatternIdx
from .client import QASClient
from .config import Config
from .exception import handle_exception

__plugin_meta__ = PluginMetadata(
    name="夸克自动转存",
    description="配合 quark-auto-save(https://github.com/Cp0204/quark-auto-save) 使用, 支持添加，删除，列出，运行任务",
    usage="qas",
    type="application",  # library
    homepage="https://github.com/fllesser/nonebot-plugin-quark-autosave",
    config=Config,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
    # supported_adapters={"~onebot.v11"}, # 仅 onebot
    extra={"author": "fllesser <fllessive@mail.com>"},
)

from arclet.alconna import Args, Alconna
from nonebot_plugin_alconna import Match, on_alconna

# https://pan.quark.cn/s/203e7e764160?pwd=FLtm#/list/share/aabc9f149afc425bb8a81a51402bb5a1
SHARE_URL_REGEX = r"https://pan\.quark\.cn/s/[0-9a-zA-Z]+(?:\?pwd=[0-9a-zA-Z]+)?(?:#/list/share/[0-9a-zA-Z]+)?"

qas = on_alconna(
    Alconna(
        "qas",
        Args["taskname?", str],
        Args["shareurl?", f"re:{SHARE_URL_REGEX}"],
        Args["pattern_idx?", Literal["0", "1", "2", "3", "4"]],
        Args["inner?", Literal["1", "0"]],
        Args["startfid_idx?", int],
        Args["runweek?", str],
    ),
    permission=SUPERUSER,
    block=True,
)


TASK_KEY = "QUARK_AUTO_SAVE_TASK"


def Task() -> TaskItem:
    def _get_task(state: T_State) -> TaskItem:
        return state[TASK_KEY]

    return Depends(_get_task)


@qas.handle()
async def _(
    taskname: Match[str],
    shareurl: Match[str],
):
    if taskname.available:
        qas.set_path_arg("taskname", taskname.result)

    if shareurl.available:
        qas.set_path_arg("shareurl", shareurl.result)


@qas.got_path("taskname", "请输入任务名称")
async def _(taskname: str, state: T_State):
    state["taskname"] = taskname


@qas.got_path("shareurl", "请输入分享链接")
async def _(shareurl: str, state: T_State):
    state["shareurl"] = shareurl
    state[TASK_KEY] = TaskItem.template(state["taskname"], shareurl)


@qas.got_path("pattern_idx", f"请输入模式索引: \n{MagicRegex.display_patterns_alias()}")
@handle_exception()
async def _(pattern_idx: Literal["0", "1", "2", "3", "4"], task: TaskItem = Task()):
    idx: PatternIdx = cast(PatternIdx, int(pattern_idx))
    task.set_pattern(idx)

    async with QASClient() as client:
        detail = await client.get_share_detail(task)
        task.detail_info = detail

    if "#/list/share/" in task.shareurl:
        qas.set_path_arg("inner", "0")
    else:
        await qas.send(f"转存预览:\n{task.display_file_list()}")


@qas.got_path("inner", "是(1)否(0)以二级目录作为视频文件夹")
@handle_exception()
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
@handle_exception()
async def _(task: TaskItem = Task()):
    async with QASClient() as client:
        task = await client.add_task(task)
    await qas.finish(f"🎉 添加任务成功 🎉\n{task}")


# https://pan.quark.cn/s/92ddebc99a01
# @on_regex(f"{SHARE_URL_REGEX}", permission=SUPERUSER, priority=10).handle()
# @handle_exception()
# async def _(matched: re.Match[str] = RegexMatched()):
#     shareurl = matched.group(0)
#     logger.info(f"收到分享链接: {shareurl}")
#     # 询问用户是否使用模版


@on_command(("qas", "run"), permission=SUPERUSER).handle()
@handle_exception()
async def _(matcher: Matcher, args: Message = CommandArg()):
    task_idx = args.extract_plain_text()
    task_idx = int(task_idx) if task_idx.isdigit() else None

    async with QASClient() as client:
        async for res in client.run_script(task_idx):
            await matcher.send(res)


@on_command(("qas", "list"), permission=SUPERUSER).handle()
@handle_exception()
async def _(matcher: Matcher):
    async with QASClient() as client:
        tasks = await client.list_tasks()
        task_strs = "\n".join(f"{i}. {task.display_simple()}" for i, task in enumerate(tasks, 1))
        await matcher.send(f"当前任务列表:\n{task_strs}")


@on_command(("qas", "del"), permission=SUPERUSER).handle()
@handle_exception()
async def _(matcher: Matcher, args: Message = CommandArg()):
    task_idx = args.extract_plain_text()
    if not task_idx.isdigit():
        await matcher.finish("必需指定有效的任务索引")

    task_idx = int(task_idx)

    async with QASClient() as client:
        task_name = await client.delete_task(task_idx)
    await matcher.finish(f"删除任务 {task_name} 成功")
