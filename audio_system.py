# audio_system.py
import numpy as np
import sounddevice as sd
from PyQt6.QtCore import QObject, pyqtSignal

class AudioSystem(QObject):
    volume_changed = pyqtSignal(float)  # Сигнал для передачи громкости в GUI
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
            # Получаем устройства именно через WASAPI — это самый стабильный API в Windows
            devices = sd.query_devices()
            default_input = sd.query_hostapis()[0].get('default_input_device', -1)
            
            for i, dev in enumerate(devices):
                # Проверяем, что это устройство ввода
                if dev['max_input_channels'] > 0:
                    name = dev['name']
                    
                    # Расширенный фильтр мусорных системных названий Windows
                    stop_words = [
                        "output", "mix", "mapper", "primary", "cable", "virtual", 
                        "переназначение", "первичный", "драйвер"
                    ]
                    if any(word in name.lower() for word in stop_words):
                        continue
                        
                    # Очищаем имя от лишних системных суффиксов для красивого отображения
                    clean_name = name.split(' (')[0]
                    
                    if clean_name not in seen_names:
                        seen_names.add(clean_name)
                        display_name = f"🎤 {clean_name} (По умолчанию)" if i == default_input else f"🎤 {clean_name}"
                        
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
            if status:
                print(status)
            # Рассчитываем RMS громкость по всем доступным каналам устройства
            raw_vol = np.sqrt(np.mean(indata**2))
            amplified_vol = raw_vol * self.gain
            self.current_volume = (self.smooth_factor * amplified_vol) + ((1.0 - self.smooth_factor) * self.current_volume)
            
            # Отправляем текущую громкость в интерфейс
            self.volume_changed.emit(self.current_volume)
            
        try:
            # ИСПРАВЛЕНО: Запрашиваем количество каналов, которое устройство поддерживает физически
            device_info = sd.query_devices(device_id, 'input')
            channels = min(2, device_info['max_input_channels']) # Предпочитаем стерео/моно, избегаем многоканальных сбоев
            samplerate = int(device_info['default_samplerate'])
            
            self.audio_stream = sd.InputStream(
                device=device_id, 
                channels=channels,
                samplerate=samplerate,
                blocksize=1024, # Увеличили буфер для стабильности потока
                callback=audio_callback
            )
            self.audio_stream.start()
            self.status_message.emit(f"Подключен микрофон: {device_name}")
        except Exception as e:
            self.status_message.emit(f"Ошибка инициализации микрофона: {e}")

    def set_threshold(self, slider_value):
        """Превращаем значение слайдера в нормализованный шаг аудио-порога"""
        self.volume_threshold = slider_value / 500.0

    def set_shout_threshold(self, slider_value):
        """Превращаем значение слайдера в шаг для порога крика"""
        self.shout_threshold = slider_value / 500.0
