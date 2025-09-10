import nonebot

# Import Adapters
from nonebot.adapters.telegram import Adapter as TelegramAdapter

nonebot.init()
driver = nonebot.get_driver()

# Register Adapters
driver.register_adapter(TelegramAdapter)

nonebot.load_plugins("src/nonebot_plugin_quark_autosave")

if __name__ == "__main__":
    nonebot.run()
