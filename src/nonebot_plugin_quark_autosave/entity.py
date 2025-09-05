from datetime import datetime
from typing import Any, Generic, Literal, TypeAlias, TypeVar

import pydantic
from pydantic import BaseModel, Field

from .config import plugin_config
from .exception import QuarkAutosaveException

PYDANTIC_V2 = pydantic.__version__ >= "2.0.0"

T = TypeVar("T", bound=BaseModel)


def conditional_validator(field_name: str):
    """根据 Pydantic 版本选择合适的验证器装饰器"""

    def decorator(func):
        if PYDANTIC_V2:
            from pydantic import field_validator

            return field_validator(field_name, mode="before")(func)
        else:
            from pydantic import validator

            return validator(field_name, pre=True, always=True)(func)

    return decorator


# type 泛化类型
class QASResult(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    message: str | None = None

    def data_or_raise(self):
        if self.success:
            assert self.data is not None
            return self.data
        else:
            raise QuarkAutosaveException(self.message or "未知错误")


class FirstFile(BaseModel):
    fid: str


class Share(BaseModel):
    title: str
    share_type: int
    share_id: str
    pwd_id: str
    share_url: str
    url_type: int
    first_fid: str
    expired_type: int
    file_num: int
    created_at: int
    updated_at: int
    expired_at: int
    expired_left: int
    audit_status: int
    status: int
    click_pv: int
    save_pv: int
    download_pv: int
    first_file: dict[str, Any]


class FileItem(BaseModel):
    fid: str
    # 文件名
    file_name: str
    updated_at: int
    # 正则处理后的文件名
    file_name_re: str | None = None
    # 已经保存到夸克网盘的文件名
    file_name_saved: str | None = None

    @property
    def updated_at_str(self) -> str:
        return datetime.fromtimestamp(self.updated_at).strftime("%Y-%m-%d %H:%M:%S")

    @property
    def regex_result(self) -> str:
        return f"{self.file_name} -> {self.file_name_re or f'{self.file_name_saved} (已存盘)'}"


class SharePath(BaseModel):
    fid: str
    name: str


class DetailInfo(BaseModel):
    is_owner: int
    share: Share
    file_list: list[FileItem] = Field(alias="list")
    paths: list[SharePath] = Field(default_factory=list)
    stoken: str

    @property
    def last_update_file_fid(self) -> str:
        return max(self.file_list, key=lambda x: x.updated_at).fid

    def display_file_list(self, start_fid: str | None = None, limit: int = 10) -> str:
        """显示文件列表

        Args:
            limit (int, optional): 显示的文件数量. Defaults to 10.

        Returns:
            str: 文件列表
        """
        # 如果 start_fid 不为空，则过滤掉小于 start_fid 的文件
        if start_fid:
            self.file_list = [file for file in self.file_list if file.fid >= start_fid]
        res_lst = [file.regex_result for file in self.file_list]
        # 取前10个
        res_lst = res_lst[:limit]
        # 0. 文件名 -> 正则处理后的文件名
        return "\n".join(f"{i}. {result}" for i, result in enumerate(res_lst))


class AlistPlugin(BaseModel):
    url: str
    token: str
    storage_id: str


class SmartStrmPlugin(BaseModel):
    webhook: str
    strmtask: str
    xlist_path_fix: str


class AlistStrmPlugin(BaseModel):
    url: str
    cookie: str
    config_id: str


class AlistStrmGenPlugin(BaseModel):
    url: str
    token: str
    storage_id: str
    strm_save_dir: str
    strm_replace_host: str


class AlistSyncPlugin(BaseModel):
    url: str
    token: str
    quark_storage_id: str
    save_storage_id: str
    tv_mode: str


class Aria2Plugin(BaseModel):
    host_port: str
    secret: str
    dir: str


class EmbyPlugin(BaseModel):
    url: str
    token: str


class PlexPlugin(BaseModel):
    url: str
    token: str
    quark_root_path: str


class FnvPlugin(BaseModel):
    base_url: str
    app_name: str
    username: str
    password: str
    secret_string: str
    api_key: str
    token: str | None = None


class Plugins(BaseModel):
    alist: AlistPlugin
    smartstrm: SmartStrmPlugin
    alist_strm: AlistStrmPlugin
    alist_strm_gen: AlistStrmGenPlugin
    alist_sync: AlistSyncPlugin
    aria2: Aria2Plugin
    emby: EmbyPlugin
    plex: PlexPlugin
    fnv: FnvPlugin


class MagicRegexItem(BaseModel):
    pattern: str
    replace: str


PatternIdx: TypeAlias = Literal[0, 1, 2, 3]


class MagicRegex(BaseModel):
    tv_regex: MagicRegexItem = Field(
        alias="$TV_REGEX",
        default=MagicRegexItem(
            pattern=".*?([Ss]\\d{1,2})?(?:[第EePpXx\\.\\-\\_\\( ]{1,2}|^)(\\d{1,3})(?!\\d).*?\\.(mp4|mkv)",
            replace="\\1E\\2.\\3",
        ),
    )
    black_word: MagicRegexItem = Field(
        alias="$BLACK_WORD",
        default=MagicRegexItem(
            pattern="^(?!.*纯享)(?!.*加更)(?!.*超前企划)(?!.*训练室)(?!.*蒸蒸日上).*",
            replace="",
        ),
    )
    show_magic: MagicRegexItem = Field(
        alias="$SHOW_MAGIC",
        default=MagicRegexItem(
            pattern="^(?!.*纯享)(?!.*加更)(?!.*抢先)(?!.*预告).*?第\\d+期.*",
            replace="{II}.{TASKNAME}.{DATE}.第{E}期{PART}.{EXT}",
        ),
    )
    tv_magic: MagicRegexItem = Field(
        alias="$TV_MAGIC",
        default=MagicRegexItem(pattern="", replace="{TASKNAME}.{SXX}E{E}.{EXT}"),
    )

    @classmethod
    def patterns(cls) -> list[str]:
        patterns = MagicRegex()
        return [
            patterns.tv_regex.pattern,
            patterns.black_word.pattern,
            patterns.show_magic.pattern,
            patterns.tv_magic.pattern,
        ]

    @classmethod
    def patterns_str(cls) -> str:
        # 加上索引
        return "\n".join(f"{i}. {pattern}" for i, pattern in enumerate(cls.patterns()))

    @classmethod
    def patterns_alias(cls) -> list[str]:
        return [
            "$TV_REGEX",
            "$BLACK_WORD",
            "$SHOW_MAGIC",
            "$TV_MAGIC",
        ]

    @classmethod
    def patterns_alias_str(cls) -> str:
        return "\n".join(f" - {i}. {alias}" for i, alias in enumerate(cls.patterns_alias()))

    @classmethod
    def get_pattern_alias(cls, pattern_idx: PatternIdx) -> str:
        match pattern_idx:
            case 0:
                return "$TV_REGEX"
            case 1:
                return "$BLACK_WORD"
            case 2:
                return "$SHOW_MAGIC"
            case 3:
                return "$TV_MAGIC"


class Addition(BaseModel):
    smartstrm: dict[str, Any] = Field(default_factory=dict)
    alist_strm_gen: dict[str, Any] = Field(default_factory=lambda: {"auto_gen": False})
    alist_sync: dict[str, Any] = Field(
        default_factory=lambda: {"enable": True, "save_path": "", "verify_path": "", "full_path_mode": False}
    )
    aria2: dict[str, Any] = Field(default_factory=lambda: {"auto_download": False, "pause": False})
    emby: dict[str, Any] = Field(default_factory=lambda: {"try_match": False, "media_id": ""})
    fnv: dict[str, Any] = Field(default_factory=lambda: {"auto_refresh": False, "mdb_name": ""})

    def __str__(self):
        return (
            f" - smartstrm: {self.smartstrm}\n"
            f" - alist_strm_gen: {self.alist_strm_gen}\n"
            f" - alist_sync: {self.alist_sync}\n"
            f" - aria2: {self.aria2}\n"
            f" - emby: {self.emby}\n"
            f" - fnv: {self.fnv}"
        )


class TaskItem(BaseModel):
    taskname: str
    shareurl: str
    savepath: str
    pattern: str = Field(default="$TV_REGEX")
    replace: str = ""
    enddate: str = ""
    addition: Addition | None = None
    ignore_extension: bool = False
    runweek: list[Literal[1, 2, 3, 4, 5, 6, 7]] = [5, 6, 7]
    startfid: str | None = None

    def __str__(self):
        return (
            f"任务名称: {self.taskname}\n"
            f"分享链接: {self.shareurl}\n"
            f"保存路径: {self.savepath}\n"
            f"匹配规则: {self.pattern}\n"
            f"替换规则: {self.replace}\n"
            f"结束日期: {self.enddate if self.enddate else '始终有效'}\n"
            f"运行周期: {self.runweek}\n"
            f"附加配置:\n{self.addition}\n"
            f"忽略扩展名: {self.ignore_extension}\n"
            f"起始文件: {self.startfid}"
        )

    @classmethod
    def template(
        cls,
        taskname: str,
        shareurl: str,
        pattern_idx: PatternIdx = 0,
    ) -> "TaskItem":
        return cls(
            taskname=taskname,
            shareurl=shareurl,
            savepath=f"/{plugin_config.quark_auto_save_path_base}/{taskname}",
            pattern=MagicRegex.get_pattern_alias(pattern_idx),
        )

    def set_pattern(self, pattern_idx: PatternIdx):
        self.pattern = MagicRegex.get_pattern_alias(pattern_idx)


class ShareDetailPayload(BaseModel):
    shareurl: str
    stoken: str = ""
    task: TaskItem
    magic_regex: MagicRegex = Field(default_factory=MagicRegex)


class PushConfig(BaseModel):
    QUARK_SIGN_NOTIFY: bool
    GOBOT_URL: str
    GOBOT_QQ: str
    GOBOT_TOKEN: str


class CloudSaver(BaseModel):
    server: str
    username: str
    password: str
    token: str


class PanSou(BaseModel):
    server: str


class Source(BaseModel):
    cloudsaver: CloudSaver
    pansou: PanSou


class TaskPluginsConfigDefault(BaseModel):
    smartstrm: dict[str, Any] = {}
    alist_strm_gen: dict[str, Any]
    alist_sync: dict[str, Any]
    aria2: dict[str, Any]
    emby: dict[str, Any]
    fnv: dict[str, Any]


class AutosaveData(BaseModel):
    cookie: list[str]
    push_config: PushConfig
    plugins: Plugins
    magic_regex: MagicRegex
    tasklist: list[TaskItem] = Field(default_factory=list)
    crontab: str
    source: Source
    api_token: str
    task_plugins_config_default: TaskPluginsConfigDefault


def model_dump(data: BaseModel):
    if PYDANTIC_V2:
        return data.model_dump()
    return data.dict()


def model_dump_json(data: BaseModel):
    if PYDANTIC_V2:
        return data.model_dump_json()
    return data.json()
