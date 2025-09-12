from typing import Any

import httpx
from nonebot import logger
from nonebot.compat import model_dump

from .config import plugin_config
from .exception import QASException
from .model import AutosaveData, DetailInfo, ShareDetailPayload, TaskItem


class QASClient:
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            base_url=plugin_config.qas_endpoint,
            params={"token": plugin_config.qas_token},
        )
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.client.aclose()

    async def delete_task(self, task_idx: int):
        """
        删除任务

        Args:
            task_idx (int): 任务索引

        Returns:
            TaskItem: 删除后的任务

        Raises:
            QASException: 任务索引无效
        """
        data = await self.get_data()

        if 0 < task_idx <= len(data.tasklist):
            task_item = data.tasklist.pop(task_idx - 1)
            await self.update(data)
            return task_item.taskname
        else:
            raise QASException(f"任务索引 {task_idx} 无效")

    async def list_tasks(self):
        """
        获取任务列表

        Returns:
            list[TaskItem]: 任务列表
        """
        data = await self.get_data()
        return data.tasklist

    async def update(self, data: AutosaveData) -> str:
        """
        更新 QuarkAutosave 数据

        Args:
            data (AutosaveData): 数据

        Returns:
            str: 更新后的数据

        Raises:
            QASException: 更新失败
        """
        response = await self.client.post("/update", json=model_dump(data))
        return self._check_response(response)["message"]

    async def run_script(self, task_idx: int | None = None):
        """
        运行转存脚本

        Args:
            task_idx (int | None, optional): 任务索引. Defaults to None.

        Yields:
            str: 转存结果
        """
        payload = {}
        if task_idx is not None:
            data = await self.get_data()
            task_idx = (task_idx - 1) % len(data.tasklist)
            task_in_dict = model_dump(data.tasklist[task_idx])
            del task_in_dict["runweek"]
            payload["tasklist"] = [task_in_dict]

        async with self.client.stream("POST", "/run_script_now", json=payload) as response:
            response.raise_for_status()
            task_res: list[str] = []

            async for chunk in response.aiter_lines():
                if chunk := chunk.removeprefix("data:").replace("=", "").strip():
                    if chunk.startswith("#") and len(task_res) > 0:
                        yield "\n".join(task_res)
                        task_res.clear()
                        continue
                    if chunk.startswith("分享链接"):
                        continue
                    task_res.append(chunk)

            if len(task_res) > 0:
                yield "\n".join(task_res)

    async def add_task(self, task: TaskItem):
        """
        添加自动转存任务到 QuarkAutosave

        Args:
            task (TaskItem): 任务

        Returns:
            TaskItem: 添加后的任务
        """
        response = await self.client.post("/api/add_task", json=model_dump(task))
        return TaskItem(**self._check_response(response))

    async def get_share_detail(self, task: TaskItem):
        """
        获取分享链接详情

        Args:
            task (TaskItem): 任务

        Returns:
            DetailInfo: 分享链接详情
        """
        payload = ShareDetailPayload(
            shareurl=task.shareurl,
            task=task,
        )

        response = await self.client.post("/get_share_detail", json=model_dump(payload))
        response.raise_for_status()
        return DetailInfo(**self._check_response(response))

    async def get_data(self):
        """
        获取 QuarkAutosave 数据
        """
        response = await self.client.get("/data")
        return AutosaveData(**self._check_response(response))

    def _check_response(self, response: httpx.Response) -> dict[str, Any]:
        """
        检查响应是否成功

        Args:
            response (httpx.Response): 响应

        Raises:
            QASException: 响应失败
        """
        if response.status_code >= 500:
            response.raise_for_status()
        resp_json = response.json()
        if bool(resp_json.get("success")):
            return resp_json.get("data", resp_json)
        logger.error(f"status: {response.status_code}, response: {resp_json}")
        raise QASException(
            resp_json.get("message") or resp_json.get("data", {"error": "未知错误"}).get("error", "未知错误")
        )
