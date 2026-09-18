# audio_system.py
import numpy as np
import sounddevice as sd
from PyQt6.QtCore import QObject, pyqtSignal

class AudioSystem(QObject):
    volume_changed = pyqtSignal(float)
    status_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.audio_stream = None
        self.volume_threshold = 0.025  # Порог обычной речи
        self.shout_threshold = 0.080   # Порог крика
        self.current_volume = 0.0

    def get_microphone_list(self):
        mic_list = []
        try:
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    mic_list.append((dev['name'], i))
        except Exception as e:
            self.status_message.emit(f"Ошибка поиска аудиоустройств: {e}")
        return mic_list

    def change_microphone(self, device_id, device_name):
        if self.audio_stream:
            self.audio_stream.stop()
            self.audio_stream.close()
            
        def audio_callback(indata, frames, time, status):
            self.current_volume = np.sqrt(np.mean(indata**2))
            
        try:
            self.audio_stream = sd.InputStream(device=device_id, callback=audio_callback)
            self.audio_stream.start()
            self.status_message.emit(f"Подключен микрофон: {device_name}")
        except Exception as e:
            self.status_message.emit(f"Ошибка микрофона: {e}")

    def set_threshold(self, slider_value):
        """Изменение порога речи (значение от 1 до 100 переводим в 0.001 - 0.1)"""
        self.volume_threshold = slider_value / 1000.0

    def set_shout_threshold(self, slider_value):
        """Изменение порога крика"""
        self.shout_threshold = slider_value / 1000.0
