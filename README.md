<div align="center">
    <a href="https://v2.nonebot.dev/store">
    <img src="https://raw.githubusercontent.com/fllesser/nonebot-plugin-template/refs/heads/resource/.docs/NoneBotPlugin.svg" width="310" alt="logo"></a>

## ✨ nonebot-plugin-quark-autosave ✨

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/fllesser/nonebot-plugin-quark-autosave.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-quark-autosave">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-quark-autosave.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="python">
<a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/badge/code%20style-ruff-black?style=flat-square&logo=ruff" alt="ruff">
</a>
<a href="https://github.com/astral-sh/uv">
    <img src="https://img.shields.io/badge/package%20manager-uv-black?style=flat-square&logo=uv" alt="uv">
</a>
<a href="https://results.pre-commit.ci/latest/github/fllesser/nonebot-plugin-quark-autosave/master">
    <img src="https://results.pre-commit.ci/badge/github/fllesser/nonebot-plugin-quark-autosave/master.svg" alt="pre-commit" />
</a>
<a href="https://codecov.io/gh/fllesser/nonebot-plugin-quark-autosave" >
    <img src="https://codecov.io/gh/fllesser/nonebot-plugin-quark-autosave/graph/badge.svg?token=55rXGtMLMx" alt="codecov" />
</a>
</div>

## 📖 介绍

配合 [quark-auto-save](https://github.com/Cp0204/quark-auto-save) 使用, 快速添加 quark 自动转存任务

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-quark-autosave --upgrade
使用 **pypi** 源安装

    nb plugin install nonebot-plugin-quark-autosave --upgrade -i "https://pypi.org/simple"
使用**清华源**安装

    nb plugin install nonebot-plugin-quark-autosave --upgrade -i "https://pypi.tuna.tsinghua.edu.cn/simple"


</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details open>
<summary>uv</summary>

    uv add nonebot-plugin-quark-autosave
安装仓库 master 分支

    uv add git+https://github.com/fllesser/nonebot-plugin-quark-autosave@master
</details>

<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-quark-autosave
安装仓库 master 分支

    pdm add git+https://github.com/fllesser/nonebot-plugin-quark-autosave@master
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-quark-autosave
安装仓库 master 分支

    poetry add git+https://github.com/fllesser/nonebot-plugin-quark-autosave@master
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_quark_autosave"]

</details>

<details>
<summary>使用 nbr 安装(使用 uv 管理依赖可用)</summary>

[nbr](https://github.com/fllesser/nbr) 是一个基于 uv 的 nb-cli，可以方便地管理 nonebot2

    nbr plugin install nonebot-plugin-quark-autosave
使用 **pypi** 源安装

    nbr plugin install nonebot-plugin-quark-autosave -i "https://pypi.org/simple"
使用**清华源**安装

    nbr plugin install nonebot-plugin-quark-autosave -i "https://pypi.tuna.tsinghua.edu.cn/simple"

</details>


## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

|    配置项     | 必填  |         默认值          |                       说明                       |
| :-----------: | :---: | :---------------------: | :----------------------------------------------: |
| qas_endpoint  |  否   | "http://127.0.0.1:5005" |              quark-auto-save 的地址              |
|   qas_token   |  是   |           无            | 从 quark-auto-save webui 系统配置下拉 API 处获取 |
| qas_path_base |  否   |     "夸克自动转存"      |               自动转存文件夹的名称               |

## 🎉 使用
### 指令表
|   指令   | 权限  | 需要@ | 范围  |                     说明                     |
| :------: | :---: | :---: | :---: | :------------------------------------------: |
|   qas    | 主人  |  否   | 私聊  |               添加自动转存任务               |
| qas.run  | 主人  |  否   | 私聊  |               运行自动转存任务               |
| qas.list | 主人  |  否   | 私聊  |             查看自动转存任务列表             |
| qas.del  | 主人  |  否   | 私聊  | 指定索引(从 qas.list 中获取)删除自动转存任务 |

### 🎨 效果图
如果有效果图的话
