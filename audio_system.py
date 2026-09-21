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
        
        # Параметры калибровки
        self.gain = 1.0               
        self.smooth_factor = 0.35      

    def get_microphone_list(self):
        """Возвращает очищенный от дубликатов список физических микрофонов"""
        mic_list = []
        seen_names = set()
        try:
            devices = sd.query_devices()
            default_input = sd.query_hostapis()[0].get('default_input_device', -1)
            
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0 and dev['max_output_channels'] == 0:
                    name = dev['name']
                    stop_words = ["mme", "output", "mix", "mapper", "primary", "cable", "virtual", "wasapi"]
                    if any(word in name.lower() for word in stop_words):
                        continue
                        
                    if name not in seen_names:
                        seen_names.add(name)
                        display_name = f"🎤 {name} (По умолчанию)" if i == default_input else f"🎤 {name}"
                        
                        if i == default_input:
                            mic_list.insert(0, (display_name, i))
                        else:
                            mic_list.append((display_name, i))
        except Exception as e:
            self.status_message.emit(f"Ошибка поиска аудиоустройств: {e}")
        return mic_list

    def change_microphone(self, device_id, device_name):
        if self.audio_stream:
            try:
                self.audio_stream.stop()
                self.audio_stream.close()
            except:
                pass
            
        def audio_callback(indata, frames, time, status):
            # БАГ ИСПРАВЛЕН: Используем non-local/explicit ссылку для корректной записи громкости в класс
            raw_vol = np.sqrt(np.mean(indata**2))
            amplified_vol = raw_vol * self.gain
            self.current_volume = (self.smooth_factor * amplified_vol) + ((1.0 - self.smooth_factor) * self.current_volume)
            
        try:
            self.audio_stream = sd.InputStream(device=device_id, blocksize=512, callback=audio_callback)
            self.audio_stream.start()
            self.status_message.emit(f"Подключен микрофон: {device_name}")
        except Exception as e:
            self.status_message.emit(f"Ошибка микрофона: {e}")

    def set_threshold(self, slider_value):
        """Превращаем значение слайдера в нормализованный шаг аудио-порога"""
        self.volume_threshold = slider_value / 500.0

    def set_shout_threshold(self, slider_value):
        """Превращаем значение слайдера в шаг для порога крика"""
        self.shout_threshold = slider_value / 500.0
