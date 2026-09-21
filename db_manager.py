import os
import json

CONFIG_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "avatar_studio_database.json")

class DatabaseManager:
    def __init__(self):
        self.database = {
            "skins": {"По умолчанию": {}},
            "effects": {},
            "active_skin": "По умолчанию"
        }
        self.load_database()

    def save_database(self):
        try:
            with open(CONFIG_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.database, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def load_database(self):
        if os.path.exists(CONFIG_DATA_FILE):
            try:
                with open(CONFIG_DATA_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    for key in ["skins", "effects", "active_skin"]:
                        if key in loaded:
                            self.database[key] = loaded[key]
            except Exception as e:
                print(f"Ошибка загрузки: {e}")

    def reset_database(self):
        if os.path.exists(CONFIG_DATA_FILE):
            os.remove(CONFIG_DATA_FILE)
        self.database = {"skins": {"По умолчанию": {}}, "effects": {}, "active_skin": "По умолчанию"}
