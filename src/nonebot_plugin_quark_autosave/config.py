from nonebot import get_driver, get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    quark_autosave_endpoint: str = "http://127.0.0.1:5005"
    quark_autosave_token: str | None = None
    quark_auto_save_path_base: str = "QuarkAutoSave"


# 配置加载
plugin_config: Config = get_plugin_config(Config)
global_config = get_driver().config

# 全局名称
NICKNAME: str = next(iter(global_config.nickname), "")
