# timeline.py
import os
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFileDialog
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon

from config_manager import config
from timeline_widgets import SkinGridWidget, EffectGridWidget

class TimelinePanel(QFrame):
    frame_loaded = pyqtSignal(str, str)
    batch_loaded_signal = pyqtSignal(dict)
    config_changed = pyqtSignal()
    cell_selected = pyqtSignal(str)
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #252526; border-radius: 5px; padding: 4px;")
        self.selected_key = "idle_close_1"
        self.current_mode = "skin"
        self.buttons = {}
        
        # Ссылки на внешние виджеты настроек параметров
        self.skin_settings = None
        self.effect_settings = None
        
        self.init_ui()

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(15, 6, 15, 6)
        self.main_layout.setSpacing(12)
        
        # Информационный индикатор выбранной ячейки
        self.info_block = QFrame()
        self.info_block.setStyleSheet("background-color: #0b070e; padding: 6px; border: 1px solid #4a285a; border-radius: 4px;")
        info_layout = QVBoxLayout(self.info_block)
        info_layout.setContentsMargins(6, 6, 6, 6)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_title = QLabel("<b>ЯЧЕЙКА КАДРА</b>")
        self.lbl_title.setStyleSheet("color: #bc94ff; font-size: 9px;")
        info_layout.addWidget(self.lbl_title)
        
        self.main_layout.addWidget(self.info_block, stretch=0)
        
        # Добавляем сетки кадров
        self.avatar_grid = SkinGridWidget(self)
        self.effect_grid = EffectGridWidget(self)
        
        self.main_layout.addWidget(self.avatar_grid, stretch=1, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.effect_grid, stretch=1, alignment=Qt.AlignmentFlag.AlignCenter)
        self.effect_grid.hide()
        
        self.select_key("idle_close_1")

    def set_mode(self, mode):
        self.current_mode = mode
        if mode == "skin":
            self.effect_grid.hide()
            self.avatar_grid.show()
            if self.skin_settings: self.skin_settings.show()
            if self.effect_settings: self.effect_settings.hide()
            main_win = self.window()
            if hasattr(main_win, 'box_reward_profiles') and main_win.box_reward_profiles:
                main_win.on_skin_dropdown_changed(main_win.box_reward_profiles.currentIndex())
        else:
            self.avatar_grid.hide()
            self.effect_grid.show()
            if self.skin_settings: self.skin_settings.hide()
            if self.effect_settings: 
                self.effect_settings.show()
                # БАГ ИСПРАВЛЕН: Вызываем обновление источника списка эффектов в безопасном контексте
                self.effect_settings.refresh_effects_list_source()

    def update_sliders_from_config(self):
        if not self.skin_settings: return
        s = self.skin_settings
        s.slide_speed.blockSignals(True)
        s.slide_talk_inertia.blockSignals(True)
        s.slide_shout_inertia.blockSignals(True)
        s.slide_afk.blockSignals(True)
        
        saved_ms = getattr(config, 'idle_speed', 250)
        calculated_fps = int(1000 / saved_ms) if saved_ms > 0 else 4
        s.slide_speed.setValue(max(2, min(6, calculated_fps)))
        
        s.slide_talk_inertia.setValue(getattr(config, 'talk_inertia', 20))
        s.slide_shout_inertia.setValue(getattr(config, 'shout_inertia', 10))
        s.slide_afk.setValue(getattr(config, 'afk_time_to_sleep', 60))
        
        s.slide_speed.blockSignals(False)
        s.slide_talk_inertia.blockSignals(False)
        s.slide_shout_inertia.blockSignals(False)
        s.slide_afk.blockSignals(False)
        s._on_local_changed()

    def on_config_slider_changed(self):
        if not self.skin_settings: 
            return
        s = self.skin_settings
        fps = s.slide_speed.value()
        
        # Записываем значения в общий конфиг
        config.idle_speed = int(1000 / fps) if fps > 0 else 250
        config.blink_frequency = s.slide_blink_freq.value()  
        config.blink_duration = s.slide_blink_dur.value()    
        config.talk_inertia = s.slide_talk_inertia.value()
        config.shout_inertia = s.slide_shout_inertia.value()
        config.afk_time_to_sleep = s.slide_afk.value()
        
        main_win = self.window()
        if hasattr(main_win, 'avatar_render') and main_win.avatar_render:
            main_win.avatar_render.update_avatar_idle_speed(config.idle_speed)
            if hasattr(main_win.avatar_render, '_blink_timer'):
                main_win.avatar_render._blink_timer.setInterval(config.blink_frequency)
            
        self.config_changed.emit()
    def select_key(self, key):
        if self.selected_key in self.buttons:
            old_btn = self.buttons[self.selected_key]
            # Ячейки без фокуса: графитовые с тонкой фиолетовой обводкой
            bg = "#1f1f24" if old_btn.property("has_file") or not old_btn.icon().isNull() else "#111114"
            border = "#4a285a" # Тонкий тёмно-фиолетовый контур
            old_btn.setStyleSheet(f"background-color: {bg}; border: 1px solid {border}; border-radius: 3px; color: #7c7c8a;")
        
        self.selected_key = key
        if key in self.buttons:
            # БЕЗ БЕЛОГО: Выделенная активная ячейка загорается сочным оранжевым цветом
            self.buttons[key].setStyleSheet("border: 2px solid #ff7700; background-color: #2a1a0c; color: #ff7700; font-weight: bold;")
        
        if hasattr(self, 'lbl_title') and self.lbl_title:
            self.lbl_title.setText(f"<b>ЯЧЕЙКА:<br><span style='color:#ff7700;'>{key.upper()}</span></b>")
        self.cell_selected.emit(key)

    def set_button_icon_externally(self, key, file_path):
        if key in self.buttons:
            if file_path and os.path.exists(file_path):
                self.buttons[key].setIcon(QIcon(file_path))
                self.buttons[key].setText("")
                self.buttons[key].setProperty("has_file", True)
                self.buttons[key].setStyleSheet("background-color: #1f1f24; border: 1px solid #4a285a; border-radius: 3px;")
            else:
                self.buttons[key].setIcon(QIcon())
                self.buttons[key].setText("[ ]") 
                self.buttons[key].setProperty("has_file", False)
                self.buttons[key].setStyleSheet("background-color: #111114; border: 1px solid #4a285a; border-radius: 3px; color: #4a285a;")
            
            # Если ячейка удерживает фокус прямо сейчас
            if key == self.selected_key:
                self.buttons[key].setStyleSheet("border: 2px solid #ff7700; background-color: #2a1a0c;")

    def clear_all_buttons_visuals(self):
        for key in self.buttons.keys():
            self.set_button_icon_externally(key, "")

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать PNG", "", "Изображения (*.png)")
        if file_path:
            self.set_button_icon_externally(self.selected_key, file_path)
            self.frame_loaded.emit(self.selected_key, file_path)

    def open_batch_loader(self):
        if self.current_mode != "skin": 
            return
        from batch_loader import BatchLoaderDialog
        dialog = BatchLoaderDialog(self)
        dialog.files_loaded.connect(self.batch_loaded_signal.emit)
        dialog.exec()
