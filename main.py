import sys
import os
from PyQt6.QtCore import QTimer, Qt, QSize
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QComboBox, QPushButton, QLabel, QFrame, QTextEdit, QSlider)
from PyQt6.QtGui import QPixmap

from audio_system import AudioSystem
from avatar_preview import AvatarRenderer
from timeline import TimelinePanel
from save_system import SaveSystem
from mixer_panel import MixerPanel
from config_manager import config
from avatar_controller import AvatarController
from stream_integration import StreamIntegration


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.is_stream_mode = False
        self.audio = AudioSystem()
        self.original_png_size = QSize(350, 350)
        
        self.setWindowTitle("Покадровая Студия")
        
        # ИСПРАВЛЕНО: Жёстко задаем компактный размер окна, 
        # чтобы снизу не появлялась чёрная пустота!
        self.setMinimumSize(780, 560)
        self.setMaximumSize(1200, 900)
        self.resize(800, 600)
        
        self.init_ui()

        
        self.stream_integration = StreamIntegration(self)
        self.stream_integration.reward_registered_signal.connect(self.update_rewards_dropdown_menu)
        
        self.controller = AvatarController(self.avatar_render, self.timeline_panel, self.mixer_panel)
        
        self.update_rewards_dropdown_menu()
        self.restore_saved_data()

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.main_layout.setSpacing(6)

        # Глобальный стиль для кнопок, выпадающих списков и ползунков
        self.setStyleSheet("""
            QWidget {
                background-color: #121214;
                color: #e1e1e6;
                font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
            }
            QFrame {
                border: none;
            }
            QPushButton {
                background-color: #202024;
                border: 1px solid #323238;
                border-radius: 4px;
                color: #e1e1e6;
                font-size: 11px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #4d1c9c;
                border-color: #6324c4;
            }
            QPushButton:pressed {
                background-color: #3b1578;
            }
            QComboBox {
                background-color: #202024;
                border: 1px solid #323238;
                border-radius: 4px;
                padding: 4px;
                font-size: 11px;
                color: #e1e1e6;
            }
            QComboBox::drop-down {
                border: none;
            }
            QSlider::groove:horizontal {
                border: 1px solid #323238;
                height: 4px;
                background: #202024;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #6324c4;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #a370f7;
                border: 1px solid #6324c4;
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: #b88eff;
            }
        """)

        # 1. ТАЙМЛАЙН
        self.timeline_panel = TimelinePanel()
        self.timeline_panel.cell_selected.connect(lambda: self.avatar_render.update() if not self.is_stream_mode else None)
        self.timeline_panel.frame_loaded.connect(self.on_frame_received)
        self.timeline_panel.batch_loaded_signal.connect(self.on_batch_frames_received)
        self.timeline_panel.config_changed.connect(self.on_config_sliders_adjusted)

        # 2. ВЕРХ: МИКРОФОН И TWITCH
        self.audio_panel = QFrame()
        audio_layout = QHBoxLayout(self.audio_panel)
        audio_layout.setContentsMargins(2, 2, 2, 2)
        
        lbl_mic = QLabel("AUDIO INPUT")
        lbl_mic.setStyleSheet("color: #a370f7; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        audio_layout.addWidget(lbl_mic)

        self.mic_box = QComboBox()
        for name, idx in self.audio.get_microphone_list():
            self.mic_box.addItem(name, idx)
        self.mic_box.currentIndexChanged.connect(self.on_mic_changed)
        audio_layout.addWidget(self.mic_box, stretch=3)
        
        self.btn_twitch = QPushButton("CONNECT TWITCH")
        self.btn_twitch.setStyleSheet("background-color: #6324c4; color: white; font-weight: bold; font-size: 10px; border: none;")
        self.btn_twitch.clicked.connect(lambda: self.stream_integration.connect_twitch())
        audio_layout.addWidget(self.btn_twitch)
        self.main_layout.addWidget(self.audio_panel)

        # 3. ЦЕНТР: МИКШЕР + АВАТАР + НАСТРОЙКИ НАГРАД
        self.center_panel = QFrame()
        center_layout = QHBoxLayout(self.center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)

        # Центр - 1. Микшер
        self.mixer_panel = MixerPanel(self.audio)
        self.mixer_panel.slider_talk.valueChanged.connect(self.on_talk_slider_moved)
        self.mixer_panel.slider_shout.valueChanged.connect(self.on_shout_slider_moved)
        center_layout.addWidget(self.mixer_panel)

        # Центр - 2. Аватар
        self.avatar_render = AvatarRenderer()
        self.avatar_render.setMinimumSize(250, 250)
        center_layout.addWidget(self.avatar_render, stretch=3, alignment=Qt.AlignmentFlag.AlignCenter)

        # Центр - 3. Панель настроек (Награды Twitch)
        self.settings_panel = QFrame()
        self.settings_panel.setStyleSheet("background-color: #18181c; border: 1px solid #222226; border-radius: 6px; padding: 6px;")
        set_layout = QVBoxLayout(self.settings_panel)
        set_layout.setSpacing(4)
        
        lbl_set_title = QLabel("REWARDS CONFIG")
        lbl_set_title.setStyleSheet("color: #a370f7; font-weight: bold; font-size: 10px; letter-spacing: 1px;")
        set_layout.addWidget(lbl_set_title)
        
        set_layout.addWidget(QLabel("<span style='color: #7c7c8a; font-size: 9px;'>Длительность эффекта:</span>"))
        rew_layout = QHBoxLayout()
        self.slide_reward = QSlider(Qt.Orientation.Horizontal)
        self.slide_reward.setRange(5, 120)
        self.slide_reward.setValue(30)
        self.slide_reward.valueChanged.connect(self.on_reward_duration_changed)
        rew_layout.addWidget(self.slide_reward)
        self.lbl_reward = QLabel("<span style='color: #a370f7; font-weight: bold;'>30</span> <span style='color: #7c7c8a;'>сек</span>")
        rew_layout.addWidget(self.lbl_reward)
        set_layout.addLayout(rew_layout)
        set_layout.addStretch()
        center_layout.addWidget(self.settings_panel, stretch=2)

        # Центр - 4. Новая правая панель
        right_layout = QVBoxLayout()
        self.btn_toggle_ui = QPushButton("LAUNCH STREAM")
        self.btn_toggle_ui.setStyleSheet("background-color: #6324c4; color: white; font-weight: bold; font-size: 10px; border: none; padding: 8px;")
        self.btn_toggle_ui.clicked.connect(self.toggle_stream_mode)
        right_layout.addWidget(self.btn_toggle_ui)
        
        self.lbl_reward_profile_title = QLabel("<center><span style='color:#7c7c8a; font-size:8px; letter-spacing: 0.5px;'>АКТИВНЫЙ ПРОФИЛЬ:</span></center>")
        right_layout.addWidget(self.lbl_reward_profile_title)
        
        self.box_reward_profiles = QComboBox()
        self.box_reward_profiles.currentIndexChanged.connect(self.on_reward_profile_changed)
        right_layout.addWidget(self.box_reward_profiles)
        
        self.lbl_avatar_params_title = QLabel("<br><span style='color: #a370f7; font-weight: bold; font-size: 10px; letter-spacing: 1px;'>AVATAR PARAMS</span>")
        right_layout.addWidget(self.lbl_avatar_params_title)
        
        right_layout.addWidget(self.timeline_panel.skin_settings)
        right_layout.addWidget(self.timeline_panel.effect_settings)
        
        right_layout.addStretch()
        center_layout.addLayout(right_layout, stretch=2)

        self.main_layout.addWidget(self.center_panel)

        # 4. НИЗ: ТАЙМЛАЙН
        self.main_layout.addWidget(self.timeline_panel)
        
        self.timeline_panel.effect_settings.slide_fx_speed.valueChanged.connect(
            lambda val: self.avatar_render.set_effect_speed(val)
        )
        self.timeline_panel.effect_settings.box_fx_type.currentTextChanged.connect(
            lambda text: setattr(self.avatar_render, 'effect_play_type', 'once' if 'Once' in text else 'loop')
        )
        
        # 5. НИЖНИЙ БЛОК: ЖУРНАЛ + АВТОРСКИЙ НИКНЕЙМ
        self.log_panel = QFrame()
        log_layout = QHBoxLayout(self.log_panel) # Меняем на горизонтальный слой, чтобы уместить никнейм сбоку
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(10)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFixedHeight(32)
        self.log_area.setStyleSheet("""
            background-color: #18181c; 
            border: 1px solid #222226; 
            border-radius: 4px; 
            color: #7c7c8a; 
            font-family: Consolas, monospace; 
            font-size: 10px;
        """)
        log_layout.addWidget(self.log_area, stretch=4)
        
        # ── ВАШ АВТОРСКИЙ НИКНЕЙМ ──
        # Замените 'ВАШ_НИКНЕЙМ' на ваше реальное имя/ник
        self.lbl_credits = QLabel("by SovenkaART") 
        self.lbl_credits.setStyleSheet("""
            color: #4d4d57; 
            font-size: 10px; 
            font-weight: bold; 
            letter-spacing: 1px;
            alignment: bottom;
        """)
        self.lbl_credits.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        log_layout.addWidget(self.lbl_credits, stretch=1)
        
        self.main_layout.addWidget(self.log_panel)

        self.setLayout(self.main_layout)

        # Центрирование окна при старте
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

        if self.mic_box.count() > 0:
            self.on_mic_changed(self.mic_box.currentIndex())

        self.timer = QTimer()
        self.timer.timeout.connect(self.process_audio_frame)
        self.timer.start(30)

    def update_rewards_dropdown_menu(self):
        """Заполняет выпадающий список созданными наградами"""
        self.box_reward_profiles.blockSignals(True)
        self.box_reward_profiles.clear()
        self.box_reward_profiles.addItem("По умолчанию", "default")
        
        if hasattr(self, 'stream_integration'):
            for title, cfg in self.stream_integration.rewards_database.items():
                self.box_reward_profiles.addItem(f" {title} ({cfg['type']})", title)
                
        self.box_reward_profiles.blockSignals(False)

    def on_reward_profile_changed(self, index):
        """Срабатывает при выборе награды из выпадающего меню"""
        reward_key = self.box_reward_profiles.itemData(index)
        self.timeline_panel.clear_all_buttons_visuals()
        
        if reward_key == "default":
            self.timeline_panel.set_mode("skin")
            
            # 1. Полностью очищаем временные эффекты
            self.avatar_render.active_effect_layers.clear() 
            if hasattr(self.avatar_render, 'stop_effect'):
                self.avatar_render.stop_effect()
                
            # 2. Восстанавливаем данные базового скина из сохранения
            self.restore_saved_data()
            
            # 3. ИСПРАВЛЕНО: Принудительно заталкиваем восстановленные кадры базового скина обратно на кнопки!
            for key, path in self.avatar_render.layers.items():
                if path and os.path.exists(path):
                    self.timeline_panel.set_button_icon_externally(key, path)
            
            self.avatar_render.update()
            self.log_message("🔄 Переключено на базовый аватар по умолчанию.")
        else:
            cfg = self.stream_integration.rewards_database.get(reward_key)
            if cfg:
                self.timeline_panel.set_mode(cfg["type"])
                saved_layers = cfg.get("layers", {})
                
                if cfg["type"] == "skin":
                    self.avatar_render.active_effect_layers.clear()
                    self.avatar_render.layers = saved_layers.copy()
                    for k, p in saved_layers.items():
                        self.timeline_panel.set_button_icon_externally(k, p)
                else:
                    # Если переключились на эффект, базовый скин НЕ трогаем в памяти,
                    # а просто поверх включаем слои эффекта
                    self.avatar_render.active_effect_layers = saved_layers.copy()
                    for k, p in saved_layers.items():
                        self.timeline_panel.set_button_icon_externally(k, p)
                        
                self.avatar_render.update()
                self.log_message(f"📂 Редактирование контента под награду: {reward_key}")

    def log_message(self, text):
        self.log_area.append(text)

    def on_mic_changed(self, index):
        self.audio.change_microphone(self.mic_box.itemData(index), "Микрофон")

    def on_frame_received(self, key, path):
        current_profile = self.box_reward_profiles.itemData(self.box_reward_profiles.currentIndex())
        
        if current_profile == "default":
            self.avatar_render.layers[key] = path
            self._save_current_state() # сохраняем только дефолт
        else:
            cfg = self.stream_integration.rewards_database.get(current_profile)
            if cfg:
                cfg["layers"][key] = path
                self.stream_integration.save_rewards_database()
                if cfg["type"] == "skin":
                    self.avatar_render.layers[key] = path
                else:
                    self.avatar_render.active_effect_layers[key] = path

        if key == "idle_close_1" and os.path.exists(path):
            pix = QPixmap(path)
            if not pix.isNull(): self.original_png_size = pix.size()
            
        self.avatar_render.update()
       
        
    def on_batch_frames_received(self, result_dict):
        if not result_dict: return
        current_profile = self.box_reward_profiles.itemData(self.box_reward_profiles.currentIndex())
        
        for key, path in result_dict.items():
            if path and os.path.exists(path):
                if current_profile == "default":
                    self.avatar_render.layers[key] = path
                else:
                    cfg = self.stream_integration.rewards_database.get(current_profile)
                    if cfg: cfg["layers"][key] = path
                
                self.timeline_panel.set_button_icon_externally(key, path)
        
        if current_profile != "default":
            self.stream_integration.save_rewards_database()
        else:
            self._save_current_state()
            
        self.avatar_render.update()

    def on_talk_slider_moved(self, val):
        self.audio.set_threshold(val)
        self._save_current_state()

    def on_shout_slider_moved(self, val):
        self.audio.set_shout_threshold(val)
        self._save_current_state()
        
    def on_config_sliders_adjusted(self):
        self.avatar_render.sync_timer_speeds()
        self._save_current_state()

    def on_reward_duration_changed(self):
        if hasattr(self, 'stream_integration'):
            self.stream_integration.reward_duration_sec = self.slide_reward.value()
            self.lbl_reward.setText(f"<span style='color: #4caf50; font-weight: bold;'>{self.stream_integration.reward_duration_sec}</span> <span style='color: #888;'>сек</span>")

    def _save_current_state(self):
        # Сохраняем файл настроек ТОЛЬКО если активен профиль по умолчанию
        current_profile = self.box_reward_profiles.itemData(self.box_reward_profiles.currentIndex())
        if current_profile == "default":
            SaveSystem.save(
                self.mixer_panel.slider_talk.value(),
                self.mixer_panel.slider_shout.value(),
                self.avatar_render.layers, # Сохраняем именно слои базового скина
            )


    def restore_saved_data(self):
        data = SaveSystem.load()
        if not data: 
            self.timeline_panel.update_sliders_from_config()
            return
        if "slider_talk" in data: self.mixer_panel.slider_talk.setValue(data["slider_talk"])
        if "slider_shout" in data: self.mixer_panel.slider_shout.setValue(data["slider_shout"])
        self.timeline_panel.update_sliders_from_config()
        self.avatar_render.sync_timer_speeds()
        if "layers" in data:
            for key, path in data["layers"].items():
                if path and os.path.exists(path):
                    self.avatar_render.layers[key] = path
                    self.timeline_panel.set_button_icon_externally(key, path)
                    if key == "idle_close_1":
                        pix = QPixmap(path)
                        if not pix.isNull(): self.original_png_size = pix.size()
        self.log_message("💾 Настройки по умолчанию восстановлены!")

    def process_audio_frame(self):
        vol = self.audio.current_volume
        thresh_talk = self.audio.volume_threshold
        thresh_shout = self.audio.shout_threshold
        self.mixer_panel.update_volume_display(vol, thresh_talk, thresh_shout)
        self.controller.update_frame_logic(vol, thresh_talk, thresh_shout, self.is_stream_mode)

    def toggle_stream_mode(self):
        self.is_stream_mode = not self.is_stream_mode
        self.hide() 
        
        if self.is_stream_mode:
            # Скрываем стандартные панели управления редактора
            self.audio_panel.hide()
            self.timeline_panel.hide()
            self.log_panel.hide()
            self.mixer_panel.hide()
            self.settings_panel.hide()
            self.btn_toggle_ui.hide()
            if hasattr(self, 'box_reward_profiles'): self.box_reward_profiles.hide()
            self.timeline_panel.skin_settings.hide()
            self.timeline_panel.effect_settings.hide()
            if hasattr(self, 'lbl_reward_profile_title'): self.lbl_reward_profile_title.hide()
            if hasattr(self, 'lbl_avatar_params_title'): self.lbl_avatar_params_title.hide()
            
            # Создаем или обновляем нижнюю панель управления для стрима
            if not hasattr(self, 'stream_control_panel'):
                self.stream_control_panel = QFrame()
                self.stream_control_panel.setStyleSheet("background-color: #1e1e1e; border-top: 1px solid #333;")
                panel_layout = QHBoxLayout(self.stream_control_panel)
                panel_layout.setContentsMargins(10, 4, 10, 4)
                
                self.lbl_active_skin_status = QLabel()
                self.lbl_active_skin_status.setStyleSheet("color: #4caf50; font-weight: bold; font-size: 11px;")
                panel_layout.addWidget(self.lbl_active_skin_status, stretch=1)
                
                btn_minimize = QPushButton("🟡 Свернуть")
                btn_minimize.setStyleSheet("background-color: #3a3a3a; color: #fff; font-size: 10px; padding: 4px 8px;")
                btn_minimize.clicked.connect(self.showMinimized)
                panel_layout.addWidget(btn_minimize)
                
                btn_close_stream = QPushButton("🔴 Меню")
                btn_close_stream.setStyleSheet("background-color: #d32f2f; color: #fff; font-weight: bold; font-size: 10px; padding: 4px 8px;")
                btn_close_stream.clicked.connect(self.toggle_stream_mode)
                panel_layout.addWidget(btn_close_stream)
                self.main_layout.addWidget(self.stream_control_panel)
            
            self.lbl_active_skin_status.setText(f"👗 Скин: {self.box_reward_profiles.currentText()}")
            self.stream_control_panel.show()
            
            self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinimizeButtonHint)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setStyleSheet("background-color: #00ff00;") 
            
            self.setMinimumSize(400, 400)
            self.setMaximumSize(800, 800)
            self.resize(450, 450)
            self.avatar_render.update()
            self.show()
        else:
            # ВОЗВРАТ В РЕЖИМ РЕДАКТОРА
            self.controller.reset_timers()
            self.avatar_render.audio_state = "idle"
            if hasattr(self, 'stream_control_panel'): self.stream_control_panel.hide()
            
            self.setWindowFlags(Qt.WindowType.Window)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            
            # ── ВОТ ТУТ МЫ ПОВТОРНО НАКАТЫВАЕМ ФИОЛЕТОВУЮ ТЕМУ ──
            self.setStyleSheet("""
                QWidget {
                    background-color: #121214;
                    color: #e1e1e6;
                    font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
                }
                QFrame { border: none; }
                QPushButton {
                    background-color: #202024;
                    border: 1px solid #323238;
                    border-radius: 4px;
                    color: #e1e1e6;
                    font-size: 11px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #4d1c9c;
                    border-color: #6324c4;
                }
                QPushButton:pressed { background-color: #3b1578; }
                QComboBox {
                    background-color: #202024;
                    border: 1px solid #323238;
                    border-radius: 4px;
                    padding: 4px;
                    font-size: 11px;
                    color: #e1e1e6;
                }
                QComboBox::drop-down { border: none; }
                QSlider::groove:horizontal {
                    border: 1px solid #323238;
                    height: 4px;
                    background: #202024;
                    border-radius: 2px;
                }
                QSlider::sub-page:horizontal {
                    background: #6324c4;
                    border-radius: 2px;
                }
                QSlider::handle:horizontal {
                    background: #a370f7;
                    border: 1px solid #6324c4;
                    width: 12px;
                    margin: -4px 0;
                    border-radius: 6px;
                }
                QSlider::handle:horizontal:hover { background: #b88eff; }
            """)
            
            self.setMaximumSize(16777215, 16777215)
            self.setMinimumSize(780, 560)
            
            self.audio_panel.show()
            self.timeline_panel.show()
            self.log_panel.show()
            self.mixer_panel.show()
            self.settings_panel.show()
            self.btn_toggle_ui.show()
            if hasattr(self, 'box_reward_profiles'): self.box_reward_profiles.show()
            if hasattr(self, 'lbl_reward_profile_title'): self.lbl_reward_profile_title.show()
            if hasattr(self, 'lbl_avatar_params_title'): self.lbl_avatar_params_title.show()
            
            if self.timeline_panel.current_mode == "skin":
                self.timeline_panel.skin_settings.show()
                self.timeline_panel.effect_settings.hide()
            else:
                self.timeline_panel.skin_settings.hide()
                self.timeline_panel.effect_settings.show()
                
            self.resize(800, 600)
            self.show()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.is_stream_mode: self.toggle_stream_mode()
            else: self.close()

    def mousePressEvent(self, event):
        if not self.is_stream_mode or event.button() != Qt.MouseButton.LeftButton: return
        pos = event.position().toPoint()
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        if x > w - 15 and y > h - 15:
            self.windowHandle().startSystemResize(Qt.Edge.RightEdge | Qt.Edge.BottomEdge)
        else:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        event.accept()

    def mouseMoveEvent(self, event):
        if self.is_stream_mode and event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
