import os
from PyQt6.QtWidgets import QWidget, QFrame, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QComboBox, QInputDialog
from PyQt6.QtCore import Qt, QSize, QTimer

class SkinGridWidget(QWidget):
    def __init__(self, parent_panel):
        super().__init__()
        self.panel = parent_panel
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        self.matrix_structure = [
            ["idle_close_1", "idle_close_2", "idle_close_3"],
            ["talk_close",   "talk_open",    "talk_blink"],
            ["shout_close",  "shout_open",   "shout_blink"],
            ["sleep_close_1", "sleep_close_2", "sleep_close_3"]
        ]
        
        layout.addWidget(QLabel("<span style='color: #a370f7; font-size: 9px; font-weight: bold;'>IDLE</span>"), 0, 0)
        layout.addWidget(QLabel("<span style='color: #e1e1e6; font-size: 9px; font-weight: bold;'>TALK</span>"), 1, 0)
        layout.addWidget(QLabel("<span style='color: #e1e1e6; font-size: 9px; font-weight: bold;'>SHOUT</span>"), 2, 0)
        layout.addWidget(QLabel("<span style='color: #7c7c8a; font-size: 9px; font-weight: bold;'>SLEEP</span>"), 3, 0)
        
        for col_idx, text in enumerate(["Кадр 1", "Кадр 2", "Кадр 3"]):
            layout.addWidget(QLabel(f"<center><span style='color: #888; font-size: 8px;'>{text}</span></center>"), 4, col_idx + 1)
        
        for row_idx in range(4):
            for col_idx in range(3):
                key = self.matrix_structure[row_idx][col_idx]
                btn = QPushButton("[ ]") 
                btn.setFixedSize(QSize(54, 38))
                btn.setIconSize(QSize(46, 30))
                btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                btn.clicked.connect(lambda checked, k=key: self.panel.select_key(k))
                btn.customContextMenuRequested.connect(lambda pos, k=key: self.show_cell_context_menu(pos, k))
                layout.addWidget(btn, row_idx, col_idx + 1)
                self.panel.buttons[key] = btn

    def show_cell_context_menu(self, pos, key):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #202024; border: 1px solid #323238; color: #e1e1e6; font-size: 11px; } QMenu::item:selected { background-color: #4d1c9c; color: white; }")
        action_clear = menu.addAction("🗑 Очистить эту ячейку")
        sender_btn = self.sender()
        action = menu.exec(sender_btn.mapToGlobal(pos))
        if action == action_clear:
            self.panel.set_button_icon_externally(key, "")
            main_win = self.panel.window()
            if hasattr(main_win, 'avatar_render') and key in main_win.avatar_render.layers:
                main_win.avatar_render.layers[key] = ""
                main_win.avatar_render.update()
            if hasattr(main_win, 'db'):
                current_skin = main_win.box_reward_profiles.currentText()
                if current_skin in main_win.db.database["skins"]:
                    main_win.db.database["skins"][current_skin][key] = ""
                    main_win.db.save_database()

class EffectGridWidget(QWidget):
    def __init__(self, parent_panel):
        super().__init__()
        self.panel = parent_panel
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        layout.addWidget(QLabel("<span style='color: #bc94ff; font-size: 9px; font-weight: bold;'>FX LAYERS</span>"), 0, 0)
        
        effect_keys = ["fx_1", "fx_2", "fx_3"]
        for idx, key in enumerate(effect_keys):
            layout.addWidget(QLabel(f"<center><span style='color: #7c7c8a; font-size: 8px;'>Слой {idx+1}</span></center>"), 1, idx + 1)
            btn = QPushButton("[ ]")
            btn.setFixedSize(QSize(64, 46))
            btn.setIconSize(QSize(54, 36))
            btn.setProperty("is_cell", True) 
            btn.clicked.connect(lambda checked, k=key: self.panel.select_key(k))
            layout.addWidget(btn, 0, idx + 1)
            self.panel.buttons[key] = btn
class SkinSettingsWidget(QFrame):
    def __init__(self, parent_panel):
        super().__init__()
        self.panel = parent_panel
        self.setObjectName("skin_settings_panel")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        layout.addWidget(QLabel("<b>⚙️ ПАРАМЕТРЫ АВАТАРА</b>"))

        layout.addWidget(QLabel("<span style='color: #7c7c8a; font-size: 9px;'>Скорость анимации (FPS):</span>"))
        fps_layout = QHBoxLayout()
        self.slide_speed = QSlider(Qt.Orientation.Horizontal)
        self.slide_speed.setRange(2, 6) 
        self.slide_speed.setValue(4)     
        self.lbl_fps_val = QLabel("<span style='color: #a370f7; font-weight: bold;'>4</span> <span style='color: #7c7c8a;'>кадр/с</span>")
        self.lbl_fps_val.setFixedWidth(60)
        fps_layout.addWidget(self.slide_speed)
        fps_layout.addWidget(self.lbl_fps_val)
        layout.addLayout(fps_layout)

        # ПОЛЗУНОК: ЧАСТОТА МОРГАНИЯ
        layout.addWidget(QLabel("<span style='color: #7c7c8a; font-size: 9px;'>Частота моргания (интервал):</span>"))
        blink_freq_layout = QHBoxLayout()
        self.slide_blink_freq = QSlider(Qt.Orientation.Horizontal)
        self.slide_blink_freq.setRange(1000, 7000)  # от 1 до 7 секунд
        self.slide_blink_freq.setValue(3500)
        self.lbl_blink_freq_val = QLabel("<span style='color: #a370f7; font-weight: bold;'>3.5</span> <span style='color: #7c7c8a;'>сек</span>")
        self.lbl_blink_freq_val.setFixedWidth(60)
        blink_freq_layout.addWidget(self.slide_blink_freq)
        blink_freq_layout.addWidget(self.lbl_blink_freq_val)
        layout.addLayout(blink_freq_layout)

        # ПОЛЗУНОК: ДЛИТЕЛЬНОСТЬ МОРГАНИЯ
        layout.addWidget(QLabel("<span style='color: #7c7c8a; font-size: 9px;'>Длительность моргания (закрытые глаза):</span>"))
        blink_dur_layout = QHBoxLayout()
        self.slide_blink_dur = QSlider(Qt.Orientation.Horizontal)
        self.slide_blink_dur.setRange(100, 600)  # от 100 до 600 миллисекунд
        self.slide_blink_dur.setValue(200)
        self.lbl_blink_dur_val = QLabel("<span style='color: #a370f7; font-weight: bold;'>200</span> <span style='color: #7c7c8a;'>мс</span>")
        self.lbl_blink_dur_val.setFixedWidth(60)
        blink_dur_layout.addWidget(self.slide_blink_dur)
        blink_dur_layout.addWidget(self.lbl_blink_dur_val)
        layout.addLayout(blink_dur_layout)

        layout.addWidget(QLabel("<span style='color: #7c7c8a; font-size: 9px;'>Удержание Речи (инерция):</span>"))
        talk_layout = QHBoxLayout()
        self.slide_talk_inertia = QSlider(Qt.Orientation.Horizontal)
        self.slide_talk_inertia.setRange(5, 150)
        self.slide_talk_inertia.setValue(20)
        self.lbl_talk_val = QLabel("<span style='color: #a370f7; font-weight: bold;'>0.20</span> <span style='color: #7c7c8a;'>сек</span>")
        self.lbl_talk_val.setFixedWidth(60)
        talk_layout.addWidget(self.slide_talk_inertia)
        talk_layout.addWidget(self.lbl_talk_val)
        layout.addLayout(talk_layout)

        layout.addWidget(QLabel("<span style='color: #7c7c8a; font-size: 9px;'>Удержание Крика (инерция):</span>"))
        shout_layout = QHBoxLayout()
        self.slide_shout_inertia = QSlider(Qt.Orientation.Horizontal)
        self.slide_shout_inertia.setRange(2, 40)
        self.slide_shout_inertia.setValue(10)
        self.lbl_shout_val = QLabel("<span style='color: #a370f7; font-weight: bold;'>1.0</span> <span style='color: #7c7c8a;'>сек</span>")
        self.lbl_shout_val.setFixedWidth(60)
        shout_layout.addWidget(self.slide_shout_inertia)
        shout_layout.addWidget(self.lbl_shout_val)
        layout.addLayout(shout_layout)

        layout.addWidget(QLabel("<span style='color: #7c7c8a; font-size: 9px;'>Время до сна (AFK):</span>"))
        sleep_layout = QHBoxLayout()
        self.slide_afk = QSlider(Qt.Orientation.Horizontal)
        self.slide_afk.setRange(5, 300)
        self.slide_afk.setValue(60)
        self.lbl_sleep_val = QLabel("<span style='color: #a370f7; font-weight: bold;'>1:00</span> <span style='color: #7c7c8a;'>мин</span>")
        self.lbl_sleep_val.setFixedWidth(60)
        sleep_layout.addWidget(self.slide_afk)
        sleep_layout.addWidget(self.lbl_sleep_val)
        layout.addLayout(sleep_layout)

        # Коннекты для всех слайдеров
        self.slide_speed.valueChanged.connect(self._on_local_changed)
        self.slide_blink_freq.valueChanged.connect(self._on_local_changed)
        self.slide_blink_dur.valueChanged.connect(self._on_local_changed)
        self.slide_talk_inertia.valueChanged.connect(self._on_local_changed)
        self.slide_shout_inertia.valueChanged.connect(self._on_local_changed)
        self.slide_afk.valueChanged.connect(self._on_local_changed)

    def _on_local_changed(self):
        # 1. Скорость анимации FPS
        self.lbl_fps_val.setText(f"<span style='color: #a370f7; font-weight: bold;'>{self.slide_speed.value()}</span> <span style='color: #7c7c8a;'>кадр/с</span>")
        
        # 2. Частота моргания (интервал в секундах)
        freq_sec = self.slide_blink_freq.value() / 1000.0
        self.lbl_blink_freq_val.setText(f"<span style='color: #a370f7; font-weight: bold;'>{freq_sec:.1f}</span> <span style='color: #7c7c8a;'>сек</span>")
        
        # 3. Длительность закрытых глаз (в миллисекундах)
        self.lbl_blink_dur_val.setText(f"<span style='color: #a370f7; font-weight: bold;'>{self.slide_blink_dur.value()}</span> <span style='color: #7c7c8a;'>мс</span>")
        
        # 4. Удержания и AFK
        t_sec = self.slide_talk_inertia.value() / 100.0
        self.lbl_talk_val.setText(f"<span style='color: #a370f7; font-weight: bold;'>{t_sec:.2f}</span> <span style='color: #7c7c8a;'>сек</span>")
        s_sec = self.slide_shout_inertia.value() / 10.0
        self.lbl_shout_val.setText(f"<span style='color: #a370f7; font-weight: bold;'>{s_sec:.1f}</span> <span style='color: #7c7c8a;'>сек</span>")
        total_sec = self.slide_afk.value()
        m, s = total_sec // 60, total_sec % 60
        self.lbl_sleep_val.setText(f"<span style='color: #a370f7; font-weight: bold;'>{m}:{s:02d}</span> <span style='color: #7c7c8a;'>мин</span>")
        
        # Передаем обновленные данные дальше в конфиг и логику панели
        self.panel.on_config_slider_changed()


class EffectSettingsWidget(QFrame):
    def __init__(self, parent_panel):
        super().__init__()
        self.panel = parent_panel
        self.setObjectName("effect_settings_panel")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        layout.addWidget(QLabel("<b>✨ НАСТРОЙКА ЭФФЕКТА</b>"))
        
        layout.addWidget(QLabel("<span style='color: #7c7c8a; font-size: 9px;'>Редактируемый Эффект:</span>"))
        self.box_active_effects = QComboBox()
        layout.addWidget(self.box_active_effects)
        
        layout.addWidget(QLabel("<span style='color: #aaa; font-size: 8px;'>Скорость эффекта (FPS):</span>"))
        eff_layout = QHBoxLayout()
        self.slide_fx_speed = QSlider(Qt.Orientation.Horizontal)
        self.slide_fx_speed.setRange(2, 6)
        self.slide_fx_speed.setValue(4)
        self.lbl_fx_fps = QLabel("<span style='color: #a370f7; font-weight: bold;'>4</span> <span style='color: #7c7c8a;'>кадр/с</span>")
        self.lbl_fx_fps.setFixedWidth(60)
        eff_layout.addWidget(self.slide_fx_speed)
        eff_layout.addWidget(self.lbl_fx_fps)
        layout.addLayout(eff_layout)
        
        layout.addWidget(QLabel("<span style='color: #aaa; font-size: 8px;'>Время работы эффекта (сек):</span>"))
        duration_layout = QHBoxLayout()
        self.slide_fx_duration = QSlider(Qt.Orientation.Horizontal)
        self.slide_fx_duration.setRange(1, 30)  
        self.slide_fx_duration.setValue(5)
        self.lbl_fx_duration = QLabel("<span style='color: #a370f7; font-weight: bold;'>5</span> <span style='color: #7c7c8a;'>сек</span>")
        self.lbl_fx_duration.setFixedWidth(60)
        duration_layout.addWidget(self.slide_fx_duration)
        duration_layout.addWidget(self.lbl_fx_duration)
        layout.addLayout(duration_layout)
        
        layout.addWidget(QLabel("<span style='color: #aaa; font-size: 8px;'>Горячая клавиша активации:</span>"))
        self.btn_bind_key = QPushButton("Клавиша: [нет]")
        self.btn_bind_key.clicked.connect(self.change_hotkey_prompt)
        layout.addWidget(self.btn_bind_key)
        
        self.slide_fx_speed.valueChanged.connect(self._auto_save_runtime_data)
        self.slide_fx_duration.valueChanged.connect(self._auto_save_runtime_data)
        
        layout.addStretch()
        QTimer.singleShot(100, self.refresh_effects_list_source)

    def get_current_active_effect_name(self):
        return self.box_active_effects.currentText()

    def refresh_effects_list_source(self):
        main_win = self.panel.window()
        if not hasattr(main_win, 'db') or "effects" not in main_win.db.database: return
        self.box_active_effects.blockSignals(True)
        current_selection = self.box_active_effects.currentText()
        self.box_active_effects.clear()
        for eff_name in main_win.db.database["effects"].keys():
            self.box_active_effects.addItem(eff_name)
        idx = self.box_active_effects.findText(current_selection)
        if idx >= 0: self.box_active_effects.setCurrentIndex(idx)
        elif self.box_active_effects.count() > 0: self.box_active_effects.setCurrentIndex(0)
        self.box_active_effects.blockSignals(False)
        self.load_selected_effect_data_into_ui()

    def load_selected_effect_data_into_ui(self):
        eff_name = self.get_current_active_effect_name()
        main_win = self.panel.window()
        if not eff_name or not hasattr(main_win, 'db'): return
        
        eff_data = main_win.db.database["effects"].get(eff_name, {})
        
        self.slide_fx_speed.blockSignals(True)
        self.slide_fx_duration.blockSignals(True)
        
        current_fps = eff_data.get("fps", 4)
        self.btn_bind_key.setText(f"Клавиша: [{eff_data.get('hotkey', 'E')}]")
        self.slide_fx_speed.setValue(current_fps)
        self.slide_fx_duration.setValue(eff_data.get("duration_sec", 5))
        
        self.slide_fx_speed.blockSignals(False)
        self.slide_fx_duration.blockSignals(False)
        
        self.lbl_fx_fps.setText(f"<span style='color: #a370f7; font-weight: bold;'>{current_fps}</span> <span style='color: #7c7c8a;'>кадр/с</span>")
        self.lbl_fx_duration.setText(f"<span style='color: #a370f7; font-weight: bold;'>{self.slide_fx_duration.value()}</span> <span style='color: #7c7c8a;'>сек</span>")

        if hasattr(main_win, 'avatar_render'):
            main_win.avatar_render.set_effect_fps(current_fps)
            if self.panel.current_mode == "effect":
                self.panel.clear_all_buttons_visuals()
                for i in range(1, 4):
                    key = f"fx_{i}"
                    self.panel.set_button_icon_externally(key, eff_data.get(key, ""))

    def _auto_save_runtime_data(self):
        eff_name = self.get_current_active_effect_name()
        main_win = self.panel.window()
        if eff_name and hasattr(main_win, 'db') and eff_name in main_win.db.database.get("effects", {}):
            fps_val = self.slide_fx_speed.value()
            main_win.db.database["effects"][eff_name]["fps"] = fps_val
            main_win.db.database["effects"][eff_name]["duration_sec"] = self.slide_fx_duration.value()
            main_win.db.save_database()
            
            self.lbl_fx_fps.setText(f"<span style='color: #a370f7; font-weight: bold;'>{fps_val}</span> <span style='color: #7c7c8a;'>кадр/с</span>")
            self.lbl_fx_duration.setText(f"<span style='color: #a370f7; font-weight: bold;'>{self.slide_fx_duration.value()}</span> <span style='color: #7c7c8a;'>сек</span>")
            if hasattr(main_win, 'avatar_render'):
                main_win.avatar_render.set_effect_fps(fps_val)

    def change_hotkey_prompt(self):
        eff_name = self.get_current_active_effect_name()
        if not eff_name: 
            return
            
        text, ok = QInputDialog.getText(self, "Привязка клавиши", f"Введите одну английскую букву для эффекта '{eff_name}':")
        if ok and text.strip():
            key = text.strip().upper()[:1] 
            main_win = self.panel.window()
            if hasattr(main_win, 'db') and "effects" in main_win.db.database:
                main_win.db.database["effects"][eff_name]["hotkey"] = key
                main_win.db.save_database()
                self.btn_bind_key.setText(f"Клавиша: [{key}]")
