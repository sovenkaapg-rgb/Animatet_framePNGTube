import os
import json
from config_manager import config

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save_slots.json")
TWITCH_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "twitch_settings.json")


class SaveSystem:
    @staticmethod
    def save(talk_val, shout_val, layers_dict):
        save_data = {
            "slider_talk": talk_val,
            "slider_shout": shout_val,
            "layers": layers_dict,
            "config": config.to_dict()
        }
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False

    @staticmethod
    def load():
        if not os.path.exists(SAVE_FILE):
            return None
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data and "config" in data:
                config.update_from_dict(data["config"])
            return data
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return None

    @staticmethod
    def save_twitch_credentials(client_id, token, channel):
        """Сохраняет данные Twitch, чтобы не вводить их заново"""
        try:
            with open(TWITCH_FILE, "w", encoding="utf-8") as f:
                json.dump({"client_id": client_id, "token": token, "channel": channel}, f, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения ключей Twitch: {e}")

    @staticmethod
    def load_twitch_credentials():
        """Загружает сохраненные данные Twitch"""
        if not os.path.exists(TWITCH_FILE):
            return None
        try:
            with open(TWITCH_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки ключей Twitch: {e}")
            return None
