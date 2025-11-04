from nonebug import App


def test_load(app: App):
    from nonebot import require

    require("nonebot_plugin_quark_autosave")


def test_share_url_regex():
    import re

    from nonebot_plugin_quark_autosave import SHARE_URL_REGEX

    url_list = [
        "https://pan.quark.cn/s/e06704643151",
        "https://pan.quark.cn/s/e06704643151#/list/share/4afa4cd5bf0e4e7bb1a2ccef8f094d74",
        "https://pan.quark.cn/s/e06704643151?pwd=12e4L6",
        "https://pan.quark.cn/s/203e7e764160?pwd=FLtm#/list/share/aabc9f149afc425bb8a81a51402bb5a1",
    ]

    for url in url_list:
        matched = re.match(SHARE_URL_REGEX, url)
        assert matched
        assert matched.group(0) == url
