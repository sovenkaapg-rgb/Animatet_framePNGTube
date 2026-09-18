class ConfigManager:
    def __init__(self):
        # Дефолтные настройки анимации
        self.idle_speed = 175           # мс между кадрами
        self.talk_inertia = 4           # тиков удержания речи
        self.shout_inertia = 25         # тиков удержания крика
        self.afk_time_to_sleep = 7      # секунд до сна
        self.blink_frequency = 4000     # мс между морганиями
        self.blink_duration = 150       # мс длительность моргания

    def update_from_dict(self, data):
        """Загрузка настроек из общего JSON сейва"""
        if not data:
            return
        self.idle_speed = data.get("idle_speed", 175)
        self.talk_inertia = data.get("talk_inertia", 4)
        self.shout_inertia = data.get("shout_inertia", 25)
        self.afk_time_to_sleep = data.get("afk_time_to_sleep", 7)
        self.blink_frequency = data.get("blink_frequency", 4000)
        self.blink_duration = data.get("blink_duration", 150)

    def to_dict(self):
        """Подготовка данных для сохранения в JSON"""
        return {
            "idle_speed": self.idle_speed,
            "talk_inertia": self.talk_inertia,
            "shout_inertia": self.shout_inertia,
            "afk_time_to_sleep": self.afk_time_to_sleep,
            "blink_frequency": self.blink_frequency,
            "blink_duration": self.blink_duration
        }

config = ConfigManager()