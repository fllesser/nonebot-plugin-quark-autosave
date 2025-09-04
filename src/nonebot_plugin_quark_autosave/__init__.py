from nonebot import require
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata, inherit_supported_adapters
from nonebot.typing import T_State

from nonebot_plugin_quark_autosave.client import QASClient
from nonebot_plugin_quark_autosave.entity import PatternIdx

require("nonebot_plugin_uninfo")
require("nonebot_plugin_alconna")
require("nonebot_plugin_localstore")
require("nonebot_plugin_apscheduler")
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="名称",
    description="描述",
    usage="用法",
    type="application",  # library
    homepage="https://github.com/fllesser/nonebot-plugin-quark-autosave",
    config=Config,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna", "nonebot_plugin_uninfo"),
    # supported_adapters={"~onebot.v11"}, # 仅 onebot
    extra={"author": "fllesser <your@mail.com>"},
)

from arclet.alconna import Alconna, Args, Option
from nonebot_plugin_alconna import Match, on_alconna

# 快速添加 auto save 任务
qas = on_alconna(
    Alconna(
        "qas",
        Args["url?", str],
        Args["taskname?", str],
        Args["pattern_idx?", PatternIdx],
        Option("-i|--inner"),
        Option("-a|--add_startfid"),
    ),
    permission=SUPERUSER,
)


@qas.handle()
async def _(
    url: Match[str], taskname: Match[str], pattern_idx: Match[int], inner: Match[bool], add_startfid: Match[bool]
):
    if url.available:
        qas.set_path_arg("url", url.result)
    if taskname.available:
        qas.set_path_arg("taskname", taskname.result)
    if pattern_idx.available:
        qas.set_path_arg("pattern_idx", pattern_idx.result)
    if inner.available:
        qas.set_path_arg("inner", inner.result)
    if add_startfid.available:
        qas.set_path_arg("add_startfid", add_startfid.result)


@qas.got_path("url", "请输入分享链接")
async def _(url: str, state: T_State):
    state["url"] = url


@qas.got_path("taskname", "请输入任务名称")
async def _(taskname: str, state: T_State):
    state["taskname"] = taskname


@qas.got_path("pattern_idx", "请输入模式索引")
async def _(pattern_idx: PatternIdx, state: T_State):
    state["pattern_idx"] = pattern_idx


@qas.got_path("inner", "是否以二级目录作为视频文件夹")
async def _(inner: bool, state: T_State):
    state["inner"] = inner


@qas.got_path("add_startfid", "是否添加起始文件ID")
async def _(add_startfid: bool, state: T_State):
    state["add_startfid"] = add_startfid


@qas.handle()
async def _(state: T_State):
    url = state["url"]
    taskname = state["taskname"]
    pattern_idx = state["pattern_idx"]
    inner = state["inner"]
    add_startfid = state["add_startfid"]

    async with QASClient() as client:
        task = await client.add_task(
            shareurl=url,
            taskname=taskname,
            pattern_idx=pattern_idx,
            inner=inner,
            add_startfid=add_startfid,
        )
    await qas.finish(f"添加任务成功: {task}")
