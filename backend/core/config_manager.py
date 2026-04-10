import json
import os

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"api_key": "", "preferred_provider": "SiliconFlow (云端)"}

def save_config(api_key, provider):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"api_key": api_key, "preferred_provider": provider}, f)
    return "✅ 配置已永久保存"
