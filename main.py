import sys
from PyQt6.QtWidgets import QMainWindow, QApplication, QInputDialog, QMessageBox
from PyQt6.QtCore import QTimer

from avatar_preview import AvatarRenderer     
from timeline import TimelinePanel            
from mixer_panel import MixerPanel            
from audio_system import AudioSystem           
from avatar_controller import AvatarController 
from main_ui import MainWindowUI  

from db_manager import DatabaseManager
from fx_controller import FXController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ПНГ-А")
        self.setMinimumSize(1024, 700)
        self.is_stream_mode = False

        # Инициализация менеджеров данных
        self.db = DatabaseManager()
        self.fx = FXController(self)

        # Компоненты приложения
        self.audio_system = AudioSystem()
        self.avatar_render = AvatarRenderer(self)
        self.timeline_panel = TimelinePanel(self)
        self.mixer_panel = MixerPanel(self.audio_system)
        self.avatar_controller = AvatarController(self.avatar_render, self.timeline_panel, self.mixer_panel)
        
        # Сборка UI
        self.ui_manager = MainWindowUI()
        self.ui_manager.setup_ui(self)
        self.ui_manager.apply_theme(self)
        
        # Первичная синхронизация данных
        self.refresh_skins_ui_dropdown()
        self.on_skin_dropdown_changed(self.box_reward_profiles.currentIndex())
        self.setup_audio_processing()
        
        self.timeline_panel.frame_loaded.connect(self.on_frame_assigned_manually)
        self.timeline_panel.batch_loaded_signal.connect(self.on_batch_frames_received)

    def setup_audio_processing(self):
        mics = self.audio_system.get_microphone_list()
        self.box_microphones.blockSignals(True)
        self.box_microphones.clear()
        for name, idx in mics:
            self.box_microphones.addItem(name, idx)
        self.box_microphones.blockSignals(False)
        
        if mics:
            self.audio_system.change_microphone(mics[0][1], mics[0][0])
        
        self.audio_timer = QTimer(self)
        self.audio_timer.timeout.connect(self.process_audio_tick)
        self.audio_timer.start(30)

    def on_microphone_changed(self, index):
        if index >= 0:
            mic_name = self.box_microphones.itemText(index)
            mic_id = self.box_microphones.itemData(index)
            self.audio_system.change_microphone(mic_id, mic_name)

    def process_audio_tick(self):
        current_vol = self.audio_system.current_volume
        talk_slider = self.mixer_panel.slider_talk.value()
        shout_slider = self.mixer_panel.slider_shout.value()
        self.audio_system.set_threshold(talk_slider)
        self.audio_system.set_shout_threshold(shout_slider)
        
        thresh_talk = self.audio_system.volume_threshold
        thresh_shout = self.audio_system.shout_threshold
        
        self.mixer_panel.update_volume_display(current_vol, thresh_talk, thresh_shout)
        
        if not self.is_stream_mode:
            self.avatar_render.audio_state = "editor"
        else:
            self.avatar_controller.update_frame_logic(current_vol, thresh_talk, thresh_shout, self.is_stream_mode)

    def reset_all_database_prompt(self):
        if QMessageBox.question(self, "Сброс", "Стереть все кастомные скины и эффекты?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.db.reset_database()
            self.refresh_skins_ui_dropdown()
            self.on_skin_dropdown_changed(0)

    def refresh_skins_ui_dropdown(self):
        self.box_reward_profiles.blockSignals(True)
        self.box_reward_profiles.clear()
        for skin_name in self.db.database["skins"].keys():
            self.box_reward_profiles.addItem(skin_name)
        active = self.db.database.get("active_skin", "По умолчанию")
        idx = self.box_reward_profiles.findText(active)
        self.box_reward_profiles.setCurrentIndex(idx if idx >= 0 else 0)
        self.box_reward_profiles.blockSignals(False)

    def on_skin_dropdown_changed(self, index):
        if index < 0: return
        skin_name = self.box_reward_profiles.itemText(index)
        self.db.database["active_skin"] = skin_name
        skin_layers = self.db.database["skins"].get(skin_name, {})
        self.avatar_render.layers = skin_layers
        
        if hasattr(self.timeline_panel, 'clear_all_buttons_visuals'):
            self.timeline_panel.clear_all_buttons_visuals()
            for key, path in skin_layers.items():
                self.timeline_panel.set_button_icon_externally(key, path)
        self.avatar_render.update()
    def create_new_skin_action(self):
        name, ok = QInputDialog.getText(self, "Новый Скин", "Введите название для нового скина:")
        if ok and name.strip():
            skin_name = name.strip()
            if skin_name in self.db.database["skins"]:
                QMessageBox.warning(self, "Внимание", "Скин с таким именем уже существует!")
                return
            
            self.db.database["skins"][skin_name] = {}
            self.db.database["active_skin"] = skin_name
            
            self.refresh_skins_ui_dropdown()
            idx = self.box_reward_profiles.findText(skin_name)
            if idx >= 0: 
                self.box_reward_profiles.setCurrentIndex(idx)
            
            self.db.save_database()
            self.timeline_panel.set_mode("skin")
            
            from batch_loader import BatchLoaderDialog
            if hasattr(BatchLoaderDialog, '_global_asset_library'):
                BatchLoaderDialog._global_asset_library.clear() 
            
            dialog = BatchLoaderDialog(self.timeline_panel)
            dialog.files_loaded.connect(self.timeline_panel.batch_loaded_signal.emit)
            dialog.exec()

    def delete_current_skin_action(self):
        current_skin = self.box_reward_profiles.currentText()
        if current_skin == "По умолчанию":
            QMessageBox.warning(self, "Ошибка", "Нельзя удалить скин 'По умолчанию'!")
            return
            
        confirm = QMessageBox.question(
            self, "Удаление", f"Вы уверены, что хотите полностью удалить скин '{current_skin}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            if current_skin in self.db.database["skins"]:
                del self.db.database["skins"][current_skin]
            
            self.db.database["active_skin"] = "По умолчанию"
            self.refresh_skins_ui_dropdown()
            
            self.on_skin_dropdown_changed(0)
            self.db.save_database()
            QMessageBox.information(self, "Успех", f"Скин '{current_skin}' успешно удален.")

    def create_new_effect_action(self):
        name, ok = QInputDialog.getText(self, "Новый Эффект", "Введите название для нового эффекта:")
        if not ok or not name.strip():
            return
            
        eff_name = name.strip()
        if eff_name in self.db.database["effects"]:
            QMessageBox.warning(self, "Внимание", "Эффект с таким именем уже существует!")
            return
            
        self.db.database["effects"][eff_name] = {
            "fx_1": "", 
            "fx_2": "", 
            "fx_3": "", 
            "hotkey": "E", 
            "fps": 4, 
            "duration_sec": 5
        }
        self.db.save_database()
        
        self.timeline_panel.set_mode("effect")
        if hasattr(self, 'btn_switch_mode'):
            self.btn_switch_mode.setText("🔄 РЕЖИМ: НАСТРОЙКА ЭФФЕКТОВ")
        
        if hasattr(self.timeline_panel, 'effect_settings'):
            fx_widget = self.timeline_panel.effect_settings
            fx_widget.refresh_effects_list_source()
            idx = fx_widget.box_active_effects.findText(eff_name)
            if idx >= 0:
                fx_widget.box_active_effects.setCurrentIndex(idx)
                    
        QMessageBox.information(self, "Успех", f"Эффект '{eff_name}' успешно создан! \nЗаполните ячейки кадров справа.")

    def on_batch_frames_received(self, assigned_map):
        current_skin = self.box_reward_profiles.currentText()
        if not current_skin or current_skin not in self.db.database["skins"]:
            return
            
        self.db.database["skins"][current_skin] = assigned_map
        self.avatar_render.layers = self.db.database["skins"][current_skin]
        
        if hasattr(self.timeline_panel, 'clear_all_buttons_visuals'):
            self.timeline_panel.clear_all_buttons_visuals()
            for key, path in assigned_map.items():
                self.timeline_panel.set_button_icon_externally(key, path)
                
        self.db.save_database()
        self.avatar_render.update()
        QMessageBox.information(self, "Успешно", f"Все кадры успешно импортированы в скин '{current_skin}'!")

    def on_frame_assigned_manually(self, key, file_path):
        current_skin = self.box_reward_profiles.currentText()
        if key.startswith("fx_"):
            if hasattr(self.timeline_panel, 'effect_settings'):
                current_fx = self.timeline_panel.effect_settings.get_current_active_effect_name()
                if current_fx and current_fx in self.db.database["effects"]:
                    self.db.database["effects"][current_fx][key] = file_path
                    self.avatar_render.active_effect_layers = self.db.database["effects"][current_fx]
        else:
            if current_skin in self.db.database["skins"]:
                self.db.database["skins"][current_skin][key] = file_path
                self.avatar_render.layers = self.db.database["skins"][current_skin]
        self.db.save_database()

    def toggle_stream_mode(self):
        from stream_window import StreamWindow
        if not self.is_stream_mode:
            self.is_stream_mode = True
            if hasattr(self, 'avatar_controller'): self.avatar_controller.reset_timers()
            self.fx.is_fx_active_in_stream = False 
            self.avatar_render.update() 
            self.hide()
            self.stream_window = StreamWindow(self.avatar_render, self)
            self.stream_window.show()
        else:
            self.is_stream_mode = False
            if hasattr(self, 'stream_window') and self.stream_window:
                if self.stream_window.main_layout:
                    self.stream_window.main_layout.removeWidget(self.avatar_render)
                self.stream_window.close()
                self.stream_window = None
            if hasattr(self, 'left_side_layout') and self.left_side_layout:
                self.left_side_layout.addWidget(self.avatar_render, stretch=1)
            self.show()
            self.avatar_render.update()

    def keyPressEvent(self, event):
        key_text = event.text().upper()
        if "effects" in self.db.database:
            for eff_name, eff_data in self.db.database["effects"].items():
                hotkey = eff_data.get("hotkey", "").upper()
                if hotkey and key_text == hotkey:
                    if hasattr(self.timeline_panel, 'effect_settings') and self.timeline_panel.effect_settings:
                        e_box = self.timeline_panel.effect_settings.box_active_effects
                        idx = e_box.findText(eff_name)
                        if idx >= 0 and e_box.currentIndex() != idx:
                            e_box.setCurrentIndex(idx)
                            
                    self.fx.start_effect_playback()
                    event.accept()
                    return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        if hasattr(self, 'audio_system') and self.audio_system.audio_stream:
            try:
                self.audio_system.audio_stream.stop()
                self.audio_system.audio_stream.close()
            except:
                pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion') 
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
