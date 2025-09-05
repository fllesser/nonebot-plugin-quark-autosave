import httpx
from nonebot import logger

from .config import plugin_config
from .entity import AutosaveData, DetailInfo, QASResult, ShareDetailPayload, TaskItem, model_dump
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
        """更新 QuarkAutosave 数据

        Args:
            data (AutosaveData): QuarkAutosave 数据
        """
        await self.client.post("/update", json=model_dump(data))

    async def run_once(self):
        pass

    async def add_task(self, task: TaskItem):
        """添加自动转存任务到 QuarkAutosave

        Args:
            task (TaskItem): 自动转存任务

        Returns:
            TaskItem: 自动转存任务
        """
        response = await self.client.post("/api/add_task", json=model_dump(task))
        resp_json = response.json()
        if response.status_code >= 500:
            raise QuarkAutosaveException(f"服务端错误: {response.status_code}")
        result = QASResult[TaskItem](**resp_json)
        return result.data_or_raise()

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
