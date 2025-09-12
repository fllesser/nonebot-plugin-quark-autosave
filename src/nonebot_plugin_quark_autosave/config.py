from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    qas_endpoint: str = "http://127.0.0.1:5005"
    qas_token: str | None = None
    qas_path_base: str = "夸克自动转存"


# 配置加载
plugin_config: Config = get_plugin_config(Config)
