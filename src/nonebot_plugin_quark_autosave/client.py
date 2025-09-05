from typing import Literal
from typing_extensions import deprecated

import httpx
from nonebot import logger

from .config import plugin_config
from .entity import AutosaveData, DetailInfo, PatternIdx, QASResult, ShareDetailPayload, TaskItem, model_dump
from .exception import QuarkAutosaveException


class QASClient:
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            base_url=plugin_config.quark_autosave_endpoint,
            params={"token": plugin_config.quark_autosave_token},
        )
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.client.aclose()

    async def remove_task(self, url: str):
        pass

    async def list_tasks(self):
        data = await self.get_data()
        return data.tasklist

    async def update(self, data: AutosaveData):
        await self.client.post("/update", json=model_dump(data))

    async def run_once(self):
        pass

    async def add_task(self, task: TaskItem):
        response = await self.client.post("/api/add_task", json=model_dump(task))
        logger.debug(f"添加任务: {response.text}")
        resp_json = response.json()
        logger.debug(f"添加任务: {resp_json}")
        if response.status_code >= 500:
            raise QuarkAutosaveException(f"服务端错误: {response.status_code}")
        result = QASResult[TaskItem](**resp_json)
        return result.data_or_raise()

    # 弃用
    @deprecated("使用 add_task 代替")
    async def add_task_old(
        self,
        taskname: str,
        shareurl: str,
        pattern_idx: PatternIdx = 0,
        inner: bool = True,
        add_startfid: bool = True,
        runweek: list[Literal[1, 2, 3, 4, 5, 6, 7]] = [5, 6, 7],
    ):
        """添加任务

        Args:
            taskname (str): 任务名
            shareurl (str): 分享链接
            pattern_idx (int, optional): 模式索引. Defaults to 0. available: 0, 1, 2, 3
            inner (bool, optional): 是否下一级目录. Defaults to True.
        """

        task = TaskItem.template(taskname, shareurl, pattern_idx)

        detail = await self.get_share_detail(task)

        if inner:
            inner_url = f"{task.shareurl}#/list/share/{detail.share.first_fid}"
            task = TaskItem.template(taskname=taskname, shareurl=inner_url, pattern_idx=pattern_idx)
            detail = await self.get_share_detail(task)

        if add_startfid:
            task.startfid = detail.last_update_file_fid

        task.runweek = runweek

        response = await self.client.post("/api/add_task", json=model_dump(task))
        resp_json = response.json()
        logger.debug(f"添加任务: {resp_json}")
        if response.status_code >= 500:
            raise QuarkAutosaveException(f"服务端错误: {response.status_code}")
        result = QASResult[TaskItem](**resp_json)
        return result.data_or_raise()

    async def create_task(self, taskname: str, shareurl: str):
        task = TaskItem.template(taskname, shareurl)

        detail = await self.get_share_detail(task)
        # share_url + #/list/share/ + first_fid 暂时取第一个文件夹
        inner_url = f"{task.shareurl}#/list/share/{detail.share.first_fid}"
        new_task = TaskItem.template(taskname, inner_url)
        inner_detail = await self.get_share_detail(new_task)
        # 取最后更新时间的文件 fid 作为 文件起始
        new_task.startfid = inner_detail.last_update_file_fid
        data = await self.get_data()
        data.tasklist.append(new_task)

    async def get_share_detail(self, task: TaskItem):
        """获取分享链接详情

        Args:
            task (TaskItem): 任务

        Returns:
            DetailInfo: 分享详情
        """
        payload = ShareDetailPayload(
            shareurl=task.shareurl,
            task=task,
        )
        response = await self.client.post("/get_share_detail", json=model_dump(payload))
        if response.status_code >= 500:
            raise QuarkAutosaveException(f"服务端错误: {response.status_code}")
        resp_json = response.json()
        logger.debug(f"获取分享详情: {resp_json}")
        result = QASResult[DetailInfo](**resp_json)
        return result.data_or_raise()

    async def get_data(self):
        """获取 QuarkAutosave 数据

        Returns:
            QuarkAutosaveData: QuarkAutosave 数据
        """
        response = await self.client.get("/data")
        if response.status_code > 500:
            raise QuarkAutosaveException(f"服务端错误: {response.status_code}")
        resp_json = response.json()
        # logger.debug(f"获取 QuarkAutosave 数据: {resp_json}")
        result = QASResult[AutosaveData](**resp_json)
        return result.data_or_raise()
