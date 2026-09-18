import os
from PyQt6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QComboBox
from PyQt6.QtCore import Qt, QSize
from config_manager import config

class SkinGridWidget(QWidget):
    """Сетка из 12 кнопок для настройки аватара"""
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
        
        # Вместо старых QLabel с эмодзи ставим аккуратный текст:
        layout.addWidget(QLabel("<span style='color: #a370f7; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;'>IDLE</span>"), 0, 0)
        layout.addWidget(QLabel("<span style='color: #e1e1e6; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;'>TALK</span>"), 1, 0)
        layout.addWidget(QLabel("<span style='color: #e1e1e6; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;'>SHOUT</span>"), 2, 0)
        layout.addWidget(QLabel("<span style='color: #7c7c8a; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;'>SLEEP</span>"), 3, 0)

       
        labels = ["Кадр 1", "Кадр 2", "Кадр 3"]
        for col_idx, text in enumerate(labels):
            layout.addWidget(QLabel(f"<center><span style='color: #888; font-size: 8px;'>{text}</span></center>"), 4, col_idx + 1)

        for row_idx in range(4):
            for col_idx in range(3):
                key = self.matrix_structure[row_idx][col_idx]
                # Меняем дефолтный красный круг на пустой квадрат
                btn = QPushButton("[ ]") 
                btn.setFixedSize(QSize(54, 38))
                btn.setIconSize(QSize(46, 30))
                # Красивый темный стиль с фиолетовым фокусом при выделении
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #18181c; 
                        border: 1px solid #282830; 
                        border-radius: 4px;
                        color: #4d4d57;
                        font-size: 10px;
                    }
                    QPushButton:hover {
                        border-color: #4d1c9c;
                        background-color: #1c1c22;
                    }
                """)
                btn.clicked.connect(lambda checked, k=key: self.panel.select_key(k))
                layout.addWidget(btn, row_idx, col_idx + 1)
                self.panel.buttons[key] = btn


class EffectGridWidget(QWidget):
    """Сетка из 3 кнопок для настройки эффектов"""
    def __init__(self, parent_panel):
        super().__init__()
        self.panel = parent_panel
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        layout.addWidget(QLabel("<span style='color: #a370f7; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;'>FX LAYERS</span>"), 0, 0)

        
        effect_keys = ["fx_1", "fx_2", "fx_3"]
        for idx, key in enumerate(effect_keys):
            layout.addWidget(QLabel(f"<center><span style='color: #7c7c8a; font-size: 8px;'>Слой {idx+1}</span></center>"), 1, idx + 1)
            btn = QPushButton("[ ]")
            btn.setFixedSize(QSize(64, 46))
            btn.setIconSize(QSize(54, 36))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #18181c; 
                    border: 1px solid #282830; 
                    border-radius: 4px;
                    color: #4d4d57;
                    font-size: 10px;
                }
                QPushButton:hover {
                    border-color: #4d1c9c;
                    background-color: #1c1c22;
                }
            """)
            btn.clicked.connect(lambda checked, k=key: self.panel.select_key(k))
            layout.addWidget(btn, 0, idx + 1)
            self.panel.buttons[key] = btn


class SkinSettingsWidget(QWidget):
    """Красивые и просторные ползунки для настройки скина аватара"""
    def __init__(self, parent_panel):
        super().__init__()
        self.panel = parent_panel
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4) # Вернули нормальный отступ

        layout.addWidget(QLabel("<span style='color: #aaa; font-size: 8px;'> Скорость циклов:</span>"))
        self.slide_speed = QSlider(Qt.Orientation.Horizontal)
        self.slide_speed.setRange(80, 450)
        self.slide_speed.valueChanged.connect(self.panel.on_config_slider_changed)
        layout.addWidget(self.slide_speed)

        layout.addWidget(QLabel("<span style='color: #aaa; font-size: 8px;'> Удержание Речи:</span>"))
        self.slide_talk_inertia = QSlider(Qt.Orientation.Horizontal)
        self.slide_talk_inertia.setRange(1, 20)
        self.slide_talk_inertia.valueChanged.connect(self.panel.on_config_slider_changed)
        layout.addWidget(self.slide_talk_inertia)

        layout.addWidget(QLabel("<span style='color: #aaa; font-size: 8px;'> Удержание Крика:</span>"))
        self.slide_shout_inertia = QSlider(Qt.Orientation.Horizontal)
        self.slide_shout_inertia.setRange(2, 40)
        self.slide_shout_inertia.valueChanged.connect(self.panel.on_config_slider_changed)
        layout.addWidget(self.slide_shout_inertia)

        layout.addWidget(QLabel("<span style='color: #aaa; font-size: 8px;'> Время до Сна (сек):</span>"))
        self.slide_afk = QSlider(Qt.Orientation.Horizontal)
        self.slide_afk.setRange(2, 25)
        self.slide_afk.valueChanged.connect(self.panel.on_config_slider_changed)
        layout.addWidget(self.slide_afk)

        layout.addWidget(QLabel("<span style='color: #aaa; font-size: 8px;'> Частота моргания (сек):</span>"))
        self.slide_blink_freq = QSlider(Qt.Orientation.Horizontal)
        self.slide_blink_freq.setRange(1000, 10000)
        self.slide_blink_freq.valueChanged.connect(self.panel.on_config_slider_changed)
        layout.addWidget(self.slide_blink_freq)

        layout.addWidget(QLabel("<span style='color: #aaa; font-size: 8px;'> Длительность (мс):</span>"))
        self.slide_blink_dur = QSlider(Qt.Orientation.Horizontal)
        self.slide_blink_dur.setRange(50, 400)
        self.slide_blink_dur.valueChanged.connect(self.panel.on_config_slider_changed)
        layout.addWidget(self.slide_blink_dur)


class EffectSettingsWidget(QWidget):
    """Комфортный интерфейс настроек для эффектов"""
    def __init__(self, parent_panel):
        super().__init__()
        self.panel = parent_panel
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        layout.addWidget(QLabel("<span style='color: #aaa; font-size: 8px;'> Скорость эффекта:</span>"))
        self.slide_fx_speed = QSlider(Qt.Orientation.Horizontal)
        self.slide_fx_speed.setRange(50, 600)
        self.slide_fx_speed.setValue(200)
        layout.addWidget(self.slide_fx_speed)
        
        layout.addWidget(QLabel("<span style='color: #aaa; font-size: 8px;'> Воспроизведение:</span>"))
        self.box_fx_type = QComboBox()
        self.box_fx_type.addItems(["Циклично (Loop)", "Один раз (Once)"])
        self.box_fx_type.setStyleSheet("font-size: 10px; background: #2d2d30; color: white;")
        layout.addWidget(self.box_fx_type)
        layout.addStretch()
