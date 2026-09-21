# fx_controller.py
from PyQt6.QtCore import QObject, QTimer

class FXController(QObject):
    def __init__(self, window):
        super().__init__()
        self.win = window
        self.fx_frame_index = 1
        self.is_fx_playing = False          
        self.is_fx_active_in_stream = False  
        self.fx_stream_time_left_ms = 0
        
        self.fx_timer = QTimer(self)
        self.fx_timer.timeout.connect(self.advance_fx_animation_frame)
        self.fx_timer.start(250)

    def start_effect_playback(self):
        if not hasattr(self.win.timeline_panel, 'effect_settings') or not self.win.timeline_panel.effect_settings:
            return
            
        current_fx = self.win.timeline_panel.effect_settings.get_current_active_effect_name()
        if not current_fx or current_fx not in self.win.db.database["effects"]:
            return
            
        eff_data = self.win.db.database["effects"][current_fx]
        
        # Если эффект уже запущен — повторное нажатие горячей клавиши выключает его
        if (not self.win.is_stream_mode and self.is_fx_playing) or (self.win.is_stream_mode and self.is_fx_active_in_stream):
            self.stop_effect_playback()
            return

        fps = eff_data.get("fps", 4)
        interval = int(1000 / fps) if fps > 0 else 250
        duration_sec = eff_data.get("duration_sec", 5) # Исправлено: берем реальную длительность, по умолчанию 5с
        
        self.fx_frame_index = 1
        self.fx_timer.setInterval(interval)

        # Синхронизируем состояние анимации внутри движка рендеринга
        if hasattr(self.win, 'avatar_render') and self.win.avatar_render:
            self.win.avatar_render.effect_frame = 0

        if not self.win.is_stream_mode:
            self.is_fx_playing = True
            self.win.avatar_render.active_effect_layers = eff_data
            QTimer.singleShot(duration_sec * 1000, lambda: self.stop_effect_playback() if self.is_fx_playing else None)
        else:
            self.fx_stream_time_left_ms = duration_sec * 1000
            self.is_fx_active_in_stream = True
            self.win.avatar_render.active_effect_layers = eff_data
            
        if hasattr(self.win, 'avatar_render') and self.win.avatar_render:
            self.win.avatar_render.update()

    def stop_effect_playback(self):
        self.is_fx_playing = False
        self.is_fx_active_in_stream = False
        self.fx_stream_time_left_ms = 0
        
        if hasattr(self.win, 'avatar_render') and self.win.avatar_render:
            self.win.avatar_render.current_live_fx_path = ""
            self.win.avatar_render.active_effect_layers = {}
            if hasattr(self.win.avatar_render, 'effect_timer') and self.win.avatar_render.effect_timer.isActive():
                self.win.avatar_render.effect_timer.stop()
            self.win.avatar_render.update()

    def advance_fx_animation_frame(self):
        if not self.is_fx_playing and not self.is_fx_active_in_stream:
            return

        if not hasattr(self.win.timeline_panel, 'effect_settings') or not self.win.timeline_panel.effect_settings:
            return
            
        current_fx = self.win.timeline_panel.effect_settings.get_current_active_effect_name()
        if not current_fx or current_fx not in self.win.db.database["effects"]:
            return
            
        eff_data = self.win.db.database["effects"][current_fx]
        interval = self.fx_timer.interval()
        
        if self.win.is_stream_mode and self.is_fx_active_in_stream:
            self.fx_stream_time_left_ms -= interval
            if self.fx_stream_time_left_ms <= 0:
                self.stop_effect_playback()
                return
                
            self.fx_frame_index = (self.fx_frame_index % 3) + 1
            current_key = f"fx_{self.fx_frame_index}"
            
            # БАГ ИСПРАВЛЕН: Принудительно дублируем шаг кадра в render, чтобы таймеры шли синхронно
            if hasattr(self.win, 'avatar_render'):
                self.win.avatar_render.effect_frame = self.fx_frame_index - 1
            
            if eff_data.get(current_key):
                self.win.avatar_render.current_live_fx_path = eff_data[current_key]
            else:
                self.win.avatar_render.current_live_fx_path = ""
            self.win.avatar_render.update()
            
        elif not self.win.is_stream_mode and self.is_fx_playing:
            self.fx_frame_index = (self.fx_frame_index % 3) + 1
            current_key = f"fx_{self.fx_frame_index}"
            
            if hasattr(self.win, 'avatar_render'):
                self.win.avatar_render.effect_frame = self.fx_frame_index - 1
                
            if eff_data.get(current_key):
                self.win.avatar_render.current_live_fx_path = eff_data[current_key]
            self.win.avatar_render.update()
