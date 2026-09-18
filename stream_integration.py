import os
import re
import json
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, Qt
from PyQt6.QtWidgets import QInputDialog, QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QLabel, QMessageBox
from twitch_manager import TwitchManager
from save_system import SaveSystem

CONFIG_REWARDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_rewards_config.json")

class RewardManager(QObject):
    reward_activated = pyqtSignal(str, str, int)  # тип (skin/effect), название, секунды
    reward_ended = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.active_timers = {}

    def activate_reward(self, r_type, name, duration_sec):
        timer_key = f"{r_type}_{name}"
        if timer_key in self.active_timers:
            self.active_timers[timer_key].stop()
        
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._on_timeout(r_type, name))
        timer.start(duration_sec * 1000)
        
        self.active_timers[timer_key] = timer
        self.reward_activated.emit(r_type, name, duration_sec)

    def _on_timeout(self, r_type, name):
        timer_key = f"{r_type}_{name}"
        if timer_key in self.active_timers:
            del self.active_timers[timer_key]
        self.reward_ended.emit(r_type, name)


class TwitchRewardsDialog(QDialog):
    def __init__(self, rewards_list, integration_controller, parent=None):
        super().__init__(parent)
        self.integration = integration_controller
        self.setWindowTitle("📦 Награды Twitch (Двойной клик для настройки)")
        self.resize(450, 400)
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        
        layout = QVBoxLayout(self)
        lbl = QLabel("<b>Активные награды канала:</b><br><span style='color: #aaa; font-size: 9px;'>Кликните дважды, чтобы превратить награду в Скин или Эффект</span>")
        lbl.setStyleSheet("font-size: 11px; color: #a970ff;")
        layout.addWidget(lbl)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            "QListWidget { background-color: #2d2d30; border: 1px solid #444; border-radius: 4px; padding: 4px; } "
            "QListWidget::item { padding: 8px; border-bottom: 1px solid #3e3e42; } "
            "QListWidget::item:hover { background-color: #444; }"
        )
        
        for r in rewards_list:
            item = QListWidgetItem(f"🎁 {r['title']} — 💎 {r['cost']} баллов")
            clean_name = re.sub(r'[^a-zA-Z0-9а-яА-Я_ ]', '', r['title']).strip().replace(' ', '_').lower()
            item.setData(Qt.ItemDataRole.UserRole, (r['title'], clean_name))
            self.list_widget.addItem(item)
            
        self.list_widget.itemDoubleClicked.connect(self.configure_reward)
        layout.addWidget(self.list_widget)
        
        btn_close = QPushButton("Закрыть")
        btn_close.setStyleSheet("background-color: #6441a5; color: white; font-weight: bold; padding: 6px; border-radius: 4px;")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def configure_reward(self, item):
        title, folder_name = item.data(Qt.ItemDataRole.UserRole)
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Выбор типа интеграции")
        msg.setText(f"Чем должна стать награда '{title}'?")
        msg.setStyleSheet("background-color: #1e1e1e; color: white;")
        
        btn_skin = msg.addButton("🎨 Скин (12 кадров)", QMessageBox.ButtonRole.ActionRole)
        btn_effect = msg.addButton("✨ Эффект (3 кадра)", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        r_type = ""
        if msg.clickedButton() == btn_skin:
            r_type = "skin"
        elif msg.clickedButton() == btn_effect:
            r_type = "effect"
        else:
            return
            
        self.integration.register_new_reward(title, folder_name, r_type)
        QMessageBox.information(self, "Успех!", f"Награда добавлена как {r_type.upper()}.\nПапка '{folder_name}' создана!\nОна появилась в меню выбора.")


class StreamIntegration(QObject):
    reward_registered_signal = pyqtSignal()

    def __init__(self, main_window):
        super().__init__()
        self.window = main_window
        self.reward_duration_sec = 30
        self.rewards_database = self.load_rewards_database()

        self.reward_manager = RewardManager()
        self.twitch = TwitchManager()

        self.reward_manager.reward_activated.connect(self.on_reward_triggered)
        self.reward_manager.reward_ended.connect(self.on_reward_expired)
        self.twitch.reward_redeemed.connect(self.process_twitch_reward)
        self.twitch.error.connect(self.window.log_message)
        self.twitch.rewards_loaded.connect(self.display_rewards_window)

    def load_rewards_database(self):
        if os.path.exists(CONFIG_REWARDS_FILE):
            try:
                with open(CONFIG_REWARDS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {}

    def save_rewards_database(self):
        try:
            with open(CONFIG_REWARDS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.rewards_database, f, ensure_ascii=False, indent=4)
        except Exception as e: print(e)

    def register_new_reward(self, title, folder_name, r_type):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        sub_folder = "skins" if r_type == "skin" else "effects"
        
        os.makedirs(os.path.join(base_dir, sub_folder, folder_name), exist_ok=True)
        
        self.rewards_database[title] = {
            "folder": folder_name,
            "type": r_type,
            "layers": {} # Пустые слои под эту конкретную папку
        }
        self.save_rewards_database()
        self.reward_registered_signal.emit()

    def connect_twitch(self):
        saved = SaveSystem.load_twitch_credentials()
        default_id = saved["client_id"] if saved else ""
        default_token = saved["token"] if saved else ""
        default_channel = saved["channel"] if saved else ""

        client_id, ok1 = QInputDialog.getText(self.window, "Twitch Client ID", "Введи Client ID:", text=default_id)
        if not ok1 or not client_id: return
        token, ok2 = QInputDialog.getText(self.window, "Twitch Token", "Введи OAuth токен:", text=default_token)
        if not ok2 or not token: return
        channel, ok3 = QInputDialog.getText(self.window, "Twitch Channel", "Имя канала (без @):", text=default_channel)
        if not ok3 or not channel: return

        SaveSystem.save_twitch_credentials(client_id, token, channel)
        self.window.log_message(f"🔴 Подключение к Twitch: {channel}...")
        self.twitch.connect(token, client_id, channel)

    def display_rewards_window(self, rewards):
        dialog = TwitchRewardsDialog(rewards, self, self.window)
        dialog.exec()

    def process_twitch_reward(self, username, reward_title):
        if reward_title in self.rewards_database:
            cfg = self.rewards_database[reward_title]
            self.window.log_message(f"🎉 Стрим-триггер! {username} активировал {cfg['type']}: {reward_title}")
            self.reward_manager.activate_reward(cfg['type'], reward_title, self.reward_duration_sec)
        else:
            # Поиск по ключевым словам по умолчанию
            reward_lower = reward_title.lower()
            for title, cfg in self.rewards_database.items():
                if cfg['folder'].lower() in reward_lower:
                    self.reward_manager.activate_reward(cfg['type'], title, self.reward_duration_sec)
                    return

    def on_reward_triggered(self, r_type, name, duration):
        cfg = self.rewards_database.get(name)
        if not cfg: return
        
        if r_type == "skin":
            self.window.log_message(f"🎨 Временный скин '{cfg['folder']}' включен на {duration} сек.")
            # Подменяем слои во время стрима на сохраненные слои этой награды
            self.window.avatar_render.layers = cfg.get("layers", {}).copy()
        elif r_type == "effect":
            self.window.log_message(f"✨ Временный эффект '{cfg['folder']}' запущен на {duration} sec.")
            self.window.avatar_render.active_effect_layers = cfg.get("layers", {}).copy()
            self.window.avatar_render.effect_timer.start()
        self.window.avatar_render.update()

    def on_reward_expired(self, r_type, name):
        self.window.log_message(f"⏰ Время действия награды '{name}' истекло. Возврат к дефолту.")
        if r_type == "skin":
            self.window.restore_saved_data() # возвращает базовый аватар из json
        elif r_type == "effect":
            self.window.avatar_render.active_effect_layers.clear()
            self.window.avatar_render.effect_timer.stop()
        self.window.avatar_render.update()
    def change_skin_manual(self):
        skins = self.get_available_skins_list()
        skin, ok = QInputDialog.getItem(self.window, "Выбор скина", "Выберите скин:", skins, 0, False)
        if ok and skin:
            self.window.log_message(f"🎨 Вручную выбран скин: {skin}")
            # Вручную подменяем слои на выбранную папку
            # Для этого считываем сохраненные настройки, если они есть, или просто пишем лог
            self.activate_temporary_skin(skin)
