from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, QTimer
from config_manager import config
import os
import math

class AvatarRenderer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layers = {}
        self.audio_state = "idle"
        self._current_pixmap = None
        
        # Таймеры аватара
        self._blink_timer = QTimer()
        self._blink_timer.timeout.connect(self._on_blink)
        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._on_anim_tick)
        
        # Счётчики кадров
        self._blink_frame = 0
        self._anim_frame = 0  # Теперь крутится по кругу: 0 -> 1 -> 2 -> 0
        
        # Парение (отключено)
        self.hover_enabled = False
        self.hover_amplitude = 10
        self.hover_speed = 2000
        self._hover_timer = QTimer()
        self._hover_timer.timeout.connect(self._on_hover_tick)
        self._hover_phase = 0
        self._hover_offset = 0
        
        # Настройки анимации эффектов (3 кадра)
        self.active_effect_layers = {}
        self.effect_frame = 0
        self.effect_play_type = "loop"  
        self.effect_timer = QTimer()
        self.effect_timer.timeout.connect(self._on_effect_tick)
        self.effect_timer.setInterval(200)  
        self.sync_timer_speeds()

    def update_avatar_idle_speed(self, ms):
        """Мгновенно обновляет скорость анимации покоя (Idle) аватара и перезапускает таймер"""
        if ms <= 0: 
            return
        self._anim_timer.setInterval(ms)
        if self._anim_timer.isActive():
            self._anim_timer.stop()
        self._anim_timer.start()

    def sync_timer_speeds(self):
        blink_ms = config.blink_frequency
        anim_ms = config.idle_speed 
        self._blink_timer.setInterval(blink_ms)
        self._anim_timer.setInterval(anim_ms)
        if not self._blink_timer.isActive():
            self._blink_timer.start()
        if not self._anim_timer.isActive():
            self._anim_timer.start()

    def set_effect_fps(self, fps):
        """Переводит FPS в миллисекунды и обновляет интервал таймера"""
        if fps <= 0: return
        ms = int(1000 / fps)  
        self.effect_timer.setInterval(ms)
        if self.active_effect_layers and not self.effect_timer.isActive():
            self.effect_timer.start()

    def _on_effect_tick(self):
        """Проигрывание эффекта по кругу: 1 -> 2 -> 3 -> 1..."""
        if not self.active_effect_layers:
            self.effect_timer.stop()
            self.current_live_fx_path = None 
            return
        self.effect_frame = (self.effect_frame + 1) % 3
        key = f"fx_{self.effect_frame + 1}"
        self.current_live_fx_path = self.active_effect_layers.get(key)
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QPixmap
        from PyQt6.QtCore import Qt, QRect
        painter = QPainter(self)
        
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        render_rect = self.rect()
        
        # 1. Отрисовка аватара
        avatar_pixmap = self._get_current_pixmap()
        if avatar_pixmap and not avatar_pixmap.isNull():
            scaled_avatar = avatar_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (self.width() - scaled_avatar.width()) // 2
            y = (self.height() - scaled_avatar.height()) // 2
            render_rect = QRect(x, y, scaled_avatar.width(), scaled_avatar.height())
            painter.drawPixmap(render_rect, scaled_avatar)
                    
        # 2. Отрисовка цикличного эффекта поверх аватара
        fx_pixmap = self._get_current_effect_pixmap()
        if (not fx_pixmap or fx_pixmap.isNull()) and hasattr(self, 'current_live_fx_path') and self.current_live_fx_path:
            if os.path.exists(self.current_live_fx_path):
                fx_pixmap = QPixmap(self.current_live_fx_path)

        if fx_pixmap and not fx_pixmap.isNull():
            scaled_fx = fx_pixmap.scaled(
                render_rect.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(render_rect, scaled_fx)
                        
        painter.end()

    def _on_blink(self):
        self._blink_frame = 1
        self.update()
        duration = config.blink_duration
        QTimer.singleShot(duration, self._end_blink)

    def _end_blink(self):
        self._blink_frame = 0
        self.update()

    def _on_anim_tick(self):
        # БАГ ИСПРАВЛЕН: Теперь счетчик корректно идет по кругу: 0 -> 1 -> 2 -> 0
        # Это позволяет отображать все 3 кадра анимации покоя (Idle)
        self._anim_frame = (self._anim_frame + 1) % 3
        self.update()

    def _on_hover_tick(self):
        if not self.hover_enabled:
            self._hover_offset = 0
            return
        self._hover_phase += 50
        if self._hover_phase >= 360:
            self._hover_phase = 0
        self._hover_offset = math.sin(math.radians(self._hover_phase)) * self.hover_amplitude
        self.update()

    def _get_current_effect_pixmap(self):
        if self.active_effect_layers and not self.effect_timer.isActive():
            self.effect_timer.start()
        key = f"fx_{self.effect_frame + 1}"
        path = self.active_effect_layers.get(key)
        if path and os.path.exists(path):
            return QPixmap(path)
        return None

    def _get_current_pixmap(self):
        state = self.audio_state
        frame = self._anim_frame  # Принимает значения 0, 1 или 2
        blink = self._blink_frame
        
        # РЕЖИМ РЕДАКТОРА
        if state == "editor":
            if hasattr(self.window(), 'timeline_panel'):
                key = self.window().timeline_panel.selected_key
                if key.startswith("fx_"):
                    key = "idle_close_1"
                path = self.layers.get(key)
                if path:
                    pix = QPixmap(path)
                    if not pix.isNull():
                        return pix
            return None
        
        # СОСТОЯНИЕ: МОРГАНИЕ
        if blink:
            if state == "shout": 
                key = "shout_blink"
                fallback = "talk_blink"
            elif state == "talk": 
                key = "talk_blink"
                fallback = "idle_close_3"
            elif state == "sleep": 
                key = "sleep_close_3"
                fallback = "idle_close_3"
            else: 
                key = "idle_close_3"
                fallback = "idle_close_1"
            path = self.layers.get(key) or self.layers.get(fallback)
            if path:
                pix = QPixmap(path)
                if not pix.isNull(): 
                    return pix
        
        # СОСТОЯНИЕ: СОН (AFK)
        if state == "sleep":
            # Циклически перебираем 3 кадра сна: 1, 2, 3
            sleep_keys = ["sleep_close_1", "sleep_close_2", "sleep_close_3"]
            key = sleep_keys[frame]
            path = self.layers.get(key) or self.layers.get("sleep_close_1")
            if path:
                pix = QPixmap(path)
                if not pix.isNull(): 
                    return pix
            return None
        
        # БАГ ИСПРАВЛЕН: Логика выбора кадров переписана под 3-кадровую анимацию
        if state == "shout":
            shout_keys = ["shout_open", "shout_close", "shout_open"]
            key = shout_keys[frame]
            fallback = "talk_open"
        elif state == "talk":
            talk_keys = ["talk_open", "talk_close", "talk_open"]
            key = talk_keys[frame]
            fallback = "idle_close_1"
        else:
            # Обычный покой (Idle): честно перебираем idle_close_1, idle_close_2, idle_close_3
            idle_keys = ["idle_close_1", "idle_close_2", "idle_close_3"]
            key = idle_keys[frame]
            fallback = "idle_close_1"
        
        path = self.layers.get(key) or self.layers.get(fallback)
        if path:
            pix = QPixmap(path)
            if not pix.isNull(): 
                return pix
        return None
