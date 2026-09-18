import os
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon
from config_manager import config

# Импортируем наши разделенные компоненты
from timeline_widgets import SkinGridWidget, EffectGridWidget, SkinSettingsWidget, EffectSettingsWidget


class TimelinePanel(QFrame):
    frame_loaded = pyqtSignal(str, str)
    batch_loaded_signal = pyqtSignal(dict)
    config_changed = pyqtSignal()
    cell_selected = pyqtSignal(str)
    status_message = pyqtSignal(str)
    
    

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #252526; border-radius: 5px; padding: 4px;")
        self.selected_key = "idle_close_1"
        self.current_mode = "skin"
        self.buttons = {}
        self.init_ui()



    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(4, 4, 4, 4)

        # 1. Готовим сетки кадров
        self.avatar_grid = SkinGridWidget(self)
        self.effect_grid = EffectGridWidget(self)
        self.effect_grid.hide()
        
        # 2. Создаем боковую панель и её ИЗОЛИРОВАННЫЙ слой компоновки
        self.side_panel = QFrame()
        self.side_panel.setStyleSheet("background-color: #1e1e1e; padding: 4px; border-radius: 4px;")
        
        # Создаем слой БЕЗ передачи родителя в скобки, чтобы Qt не сжимал элементы
        control_layout = QVBoxLayout() 
        control_layout.setSpacing(4)
        control_layout.setContentsMargins(4, 4, 4, 4)

        # Текст выбранной ячейки
        self.lbl_title = QLabel("<b>Ячейка</b>")
        self.lbl_title.setStyleSheet("color: #569cd6; font-size: 9px;")
        control_layout.addWidget(self.lbl_title)
        
        
        # Кнопки загрузки файлов в стиле минимализма
                # Кнопки загрузки файлов (UPLOAD) — Стилизованы под общую фиолетовую тему
        load_btn_layout = QHBoxLayout()
        
        self.btn_upload = QPushButton("UPLOAD FILE")
        self.btn_upload.setStyleSheet("""
            QPushButton {
                background-color: #6324c4; 
                border: none;
                border-radius: 4px;
                color: #ffffff; 
                font-size: 9px; 
                padding: 6px 10px; 
                font-weight: bold;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #7c3aed;
            }
            QPushButton:pressed {
                background-color: #5b21b6;
            }
        """)
        self.btn_upload.clicked.connect(self.upload_file)
        load_btn_layout.addWidget(self.btn_upload)

        self.btn_batch = QPushButton("UPLOAD FOLDER")
        self.btn_batch.setStyleSheet("""
            QPushButton {
                background-color: #6324c4; 
                border: none;
                border-radius: 4px;
                color: #ffffff; 
                font-size: 9px; 
                padding: 6px 10px; 
                font-weight: bold;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #7c3aed;
            }
            QPushButton:pressed {
                background-color: #5b21b6;
            }
        """)
        self.btn_batch.clicked.connect(self.open_batch_loader)
        load_btn_layout.addWidget(self.btn_batch)
        
        control_layout.addLayout(load_btn_layout)
        # Разделитель
        control_layout.addWidget(QLabel("<span style='color: #555;'>———————</span>"))

        # 3. Создаем блоки ползунков настроек
        self.skin_settings = SkinSettingsWidget(self)
        self.effect_settings = EffectSettingsWidget(self)


        control_layout.addStretch() # Выталкивает ползунки вверх, не давая им сплющиваться!

        # ПРИВЯЗЫВАЕМ НАПОЛНЕННЫЙ СЛОЙ К БОКОВОЙ ПАНЕЛИ
        self.side_panel.setLayout(control_layout)

        # 4. Размещаем панели на экране таймлайна
        self.main_layout.addWidget(self.avatar_grid, stretch=3)
        self.main_layout.addWidget(self.effect_grid, stretch=3)
        self.main_layout.addWidget(self.side_panel, stretch=2) 
        
        self.select_key("idle_close_1")

    def set_mode(self, mode):
        """Переключение между интерфейсом Скина и Эффекта"""
        self.current_mode = mode
        if mode == "skin":
            self.effect_grid.hide()
            self.avatar_grid.show()
            self.btn_batch.show()
            self.select_key("idle_close_1")
            # Показываем/скрываем ползунки в главном окне
            self.skin_settings.show()
            self.effect_settings.hide()
                        # Если мы НЕ в режиме стрима — переключаем видимость ползунков
            if hasattr(self, 'skin_settings') and hasattr(self, 'effect_settings'):
                self.skin_settings.show()
                self.effect_settings.hide()
            
        else:
            self.avatar_grid.hide()
            self.btn_batch.hide()
            self.effect_grid.show()
            self.select_key("fx_1")
            
                        # Если мы НЕ в режиме стрима — переключаем видимость ползунков
            if hasattr(self, 'skin_settings') and hasattr(self, 'effect_settings'):
                self.skin_settings.hide()
                self.effect_settings.show()
            
            # Показываем/скрываем ползунки в главном окне
            self.skin_settings.hide()
            self.effect_settings.show()


    def update_sliders_from_config(self):
        s = self.skin_settings
        s.slide_speed.blockSignals(True)
        s.slide_talk_inertia.blockSignals(True)
        s.slide_shout_inertia.blockSignals(True)
        s.slide_afk.blockSignals(True)
        s.slide_blink_freq.blockSignals(True)
        s.slide_blink_dur.blockSignals(True)

        s.slide_speed.setValue(config.idle_speed)
        s.slide_talk_inertia.setValue(config.talk_inertia)
        s.slide_shout_inertia.setValue(config.shout_inertia)
        s.slide_afk.setValue(config.afk_time_to_sleep)
        s.slide_blink_freq.setValue(config.blink_frequency)
        s.slide_blink_dur.setValue(config.blink_duration)

        s.slide_speed.blockSignals(False)
        s.slide_talk_inertia.blockSignals(False)
        s.slide_shout_inertia.blockSignals(False)
        s.slide_afk.blockSignals(False)
        s.slide_blink_freq.blockSignals(False)
        s.slide_blink_dur.blockSignals(False)

    def on_config_slider_changed(self):
        s = self.skin_settings
        config.idle_speed = s.slide_speed.value()
        config.talk_inertia = s.slide_talk_inertia.value()
        config.shout_inertia = s.slide_shout_inertia.value()
        config.afk_time_to_sleep = s.slide_afk.value()
        config.blink_frequency = s.slide_blink_freq.value()
        config.blink_duration = s.slide_blink_dur.value()
        self.config_changed.emit()

    def select_key(self, key):
        if self.selected_key in self.buttons:
            old_btn = self.buttons[self.selected_key]
            # Рассчитываем правильный темный или зеленый фон для старой кнопки
            bg = "#1d3821" if old_btn.property("has_file") or not old_btn.icon().isNull() else "#18181c"
            border = "#3b1578" if old_btn.property("has_file") else "#282830"
            old_btn.setStyleSheet(f"background-color: {bg}; border: 1px solid {border}; border-radius: 4px; color: #4d4d57;")

        self.selected_key = key
        if key in self.buttons:
            # Назначаем неоново-фиолетовый фокус для выбранной ячейки
            self.buttons[key].setStyleSheet("border: 2px solid #a370f7; background-color: #202024; color: #e1e1e6;")

        self.lbl_title.setText(f"<b>Выбрано:<br><span style='color:#a370f7;'>{key.upper()}</span></b>")
        self.cell_selected.emit(key)

    def set_button_icon_externally(self, key, file_path):
        if key in self.buttons:
            if file_path and os.path.exists(file_path):
                
                self.buttons[key].setIcon(QIcon(file_path))
                self.buttons[key].setText("")
                self.buttons[key].setProperty("has_file", True)
                self.buttons[key].setStyleSheet("background-color: #1e4620; border: 1px solid #555; border-radius: 4px;")
            else:
                self.buttons[key].setIcon(QIcon())
                # Вместо красного шара ставим аккуратный текстовый маркер пустоты
                self.buttons[key].setText("[ ]") 
                self.buttons[key].setProperty("has_file", False)
                self.buttons[key].setStyleSheet("""
                    background-color: #18181c; 
                    border: 1px solid #282830; 
                    border-radius: 4px;
                    color: #4d4d57;
                    font-size: 10px;
                """)

            if key == self.selected_key:
                # Меняем цвет фокуса на фиолетовый
                self.buttons[key].setStyleSheet("border: 2px solid #a370f7; background-color: #202024; color: #e1e1e6;")

    def clear_all_buttons_visuals(self):
        for key in self.buttons.keys():
            self.set_button_icon_externally(key, "")

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать PNG", "", "Изображения (*.png)")
        if file_path:
            self.set_button_icon_externally(self.selected_key, file_path)
            self.frame_loaded.emit(self.selected_key, file_path)

    def open_batch_loader(self):
        if self.current_mode != "skin": return
        from batch_loader import BatchLoaderDialog
        dialog = BatchLoaderDialog(self)
        dialog.files_loaded.connect(self.batch_loaded_signal.emit)
        dialog.exec()
