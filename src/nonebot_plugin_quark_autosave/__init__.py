from typing import Literal

from nonebot import require
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata, inherit_supported_adapters
from nonebot.typing import T_State

from nonebot_plugin_quark_autosave.client import QASClient

require("nonebot_plugin_alconna")
from .config import Config

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
        Args["pattern_idx?", Literal[0, 1, 2, 3]],
        Args["inner?", Literal["是", "否"]],
        Args["add_startfid?", Literal["是", "否"]],
    ),
    permission=SUPERUSER,
)


@qas.handle()
async def _(
    shareurl: Match[str],
    taskname: Match[str],
    pattern_idx: Match[Literal[0, 1, 2, 3]],
    inner: Match[Literal["是", "否"]],
    add_startfid: Match[Literal["是", "否"]],
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


@qas.got_path("taskname", "请输入任务名称")
async def _(taskname: str, state: T_State):
    state["taskname"] = taskname


@qas.got_path("shareurl", "请输入分享链接")
async def _(shareurl: str, state: T_State):
    state["shareurl"] = shareurl


@qas.got_path("pattern_idx", "请输入模式索引(0, 1, 2, 3)")
async def _(pattern_idx: Literal[0, 1, 2, 3], state: T_State):
    state["pattern_idx"] = pattern_idx


@qas.got_path("inner", "是否以二级目录作为视频文件夹")
async def _(inner: Literal["是", "否"], state: T_State):
    state["inner"] = inner == "是"


@qas.got_path("add_startfid", prompt="是否添加起始文件ID")
async def _(add_startfid: Literal["是", "否"], state: T_State):
    state["add_startfid"] = add_startfid == "是"


@qas.handle()
async def _(state: T_State):
    shareurl = state["shareurl"]
    taskname = state["taskname"]
    pattern_idx = state["pattern_idx"]
    inner = state["inner"]
    add_startfid = state["add_startfid"]

    async with QASClient() as client:
        task = await client.add_task(
            shareurl=shareurl,
            taskname=taskname,
            pattern_idx=pattern_idx,
            inner=inner,
            add_startfid=add_startfid,
        )
    await qas.finish(f"🎉 添加任务成功 🎉\n{task}")
