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
        self._anim_frame = 0
        
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
        self.effect_play_type = "loop"  # loop или once
        self.effect_timer = QTimer()
        self.effect_timer.timeout.connect(self._on_effect_tick)
        self.effect_timer.setInterval(200)  # скорость по умолчанию
        
        self.sync_timer_speeds()

    def sync_timer_speeds(self):
        blink_ms = config.blink_frequency
        anim_ms = config.idle_speed
        self._blink_timer.setInterval(blink_ms)
        self._anim_timer.setInterval(anim_ms)
        if not self._blink_timer.isActive():
            self._blink_timer.start()
        if not self._anim_timer.isActive():
            self._anim_timer.start()

    def set_effect_speed(self, ms):
        """Меняет скорость анимации эффекта (вызывается из ползунка)"""
        self.effect_timer.setInterval(ms)

    def _on_blink(self):
        self._blink_frame = 1
        self.update()
        duration = config.blink_duration
        QTimer.singleShot(duration, self._end_blink)

    def _end_blink(self):
        self._blink_frame = 0
        self.update()

    def _on_anim_tick(self):
        self._anim_frame = (self._anim_frame + 1) % 2
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
        
    def _on_effect_tick(self):
        """Проигрывание эффекта по кругу: 1 -> 2 -> 3 -> 1..."""
        if not self.active_effect_layers:
            self.effect_timer.stop()
            return
        
        self.effect_frame = (self.effect_frame + 1) % 3
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        is_stream = hasattr(self.window(), 'is_stream_mode') and self.window().is_stream_mode
        if not is_stream:
            painter.fillRect(self.rect(), QColor(30, 30, 30))

        # Включаем стандартный режим наложения слоёв с прозрачностью
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        # 1. Рисуем БАЗОВЫЙ АВАТАР персонажа
        pixmap = self._get_current_pixmap()
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            
        # 2. Поверх рисуем КАДР ЭФФЕКТА (если мы в режиме настройки или триггер сработал)
        effect_pixmap = self._get_current_effect_pixmap()
        if effect_pixmap and not effect_pixmap.isNull():
            scaled_eff = effect_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            ex = (self.width() - scaled_eff.width()) // 2
            ey = (self.height() - scaled_eff.height()) // 2
            painter.drawPixmap(ex, ey, scaled_eff)
            
        painter.end()

    def _get_current_effect_pixmap(self):
        # Если мы редактируем эффект в приложении, принудительно крутим таймер для превью
        if self.active_effect_layers and not self.effect_timer.isActive():
            self.effect_timer.start()

        key = f"fx_{self.effect_frame + 1}"
        path = self.active_effect_layers.get(key)
        if path and os.path.exists(path):
            return QPixmap(path)
        return None

    def _get_current_pixmap(self):
        state = self.audio_state
        frame = self._anim_frame
        blink = self._blink_frame

        # РЕЖИМ РЕДАКТОРА
        if state == "editor":
            if hasattr(self.window(), 'timeline_panel'):
                key = self.window().timeline_panel.selected_key
                # Если выбран ключ эффекта fx_, аватар должен показывать базовый кадр покоя, чтобы мы видели наложение!
                if key.startswith("fx_"):
                    key = "idle_close_1"
                path = self.layers.get(key)
                if path:
                    pix = QPixmap(path)
                    if not pix.isNull():
                        return pix
            return None

        if blink:
            if state == "shout": key = "shout_blink"; fallback = "talk_blink"
            elif state == "talk": key = "talk_blink"; fallback = "idle_close_3"
            elif state == "sleep": key = "sleep_close_3"; fallback = "idle_close_3"
            else: key = "idle_close_3"; fallback = "idle_close_1"
            path = self.layers.get(key) or self.layers.get(fallback)
            if path:
                pix = QPixmap(path)
                if not pix.isNull(): return pix

        if state == "sleep":
            sleep_keys = ["sleep_close_1", "sleep_close_2"]
            key = sleep_keys[frame]
            path = self.layers.get(key)
            if path:
                pix = QPixmap(path)
                if not pix.isNull(): return pix
            return None

        if state == "shout":
            key = "shout_open" if frame == 0 else "shout_close"
            fallback = "talk_open" if frame == 0 else "talk_close"
        elif state == "talk":
            key = "talk_open" if frame == 0 else "talk_close"
            fallback = "idle_close_1"
        else:
            idle_keys = ["idle_close_1", "idle_close_2"]
            key = idle_keys[frame]
            fallback = "idle_close_1"

        path = self.layers.get(key) or self.layers.get(fallback)
        if path:
            pix = QPixmap(path)
            if not pix.isNull(): return pix
        return None
