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

    async def delete_task(self, task_idx: int):
        """删除任务"""
        data = await self.get_data()
        if 0 < task_idx <= len(data.tasklist):
            task_item = data.tasklist.pop(task_idx - 1)
            await self.update(data)
            return task_item.taskname
        else:
            raise QuarkAutosaveException(f"任务索引 {task_idx} 无效")

    async def list_tasks(self):
        """获取任务列表"""
        data = await self.get_data()
        return data.tasklist

    async def update(self, data: AutosaveData):
        """更新 QuarkAutosave 数据"""
        response = await self.client.post("/update", json=model_dump(data))
        if response.status_code >= 500:
            raise QuarkAutosaveException(f"服务端错误: {response.status_code}")
        resp_json = response.json()
        logger.debug(f"更新 QuarkAutosave 数据: {resp_json}")

    async def run_script(self):
        """运行转存脚本"""
        async with self.client.stream("POST", "/run_script_now", json={}) as response:
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
        """添加自动转存任务到 QuarkAutosave"""
        response = await self.client.post("/api/add_task", json=model_dump(task))
        resp_json = response.json()
        if response.status_code >= 500:
            raise QuarkAutosaveException(f"服务端错误: {response.status_code}")
        result = QASResult[TaskItem](**resp_json)
        return result.data_or_raise()

    async def get_share_detail(self, task: TaskItem):
        """获取分享链接详情"""
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
        """获取 QuarkAutosave 数据"""
        response = await self.client.get("/data")
        if response.status_code > 500:
            raise QuarkAutosaveException(f"服务端错误: {response.status_code}")
        resp_json = response.json()
        result = QASResult[AutosaveData](**resp_json)
        return result.data_or_raise()
