# mixer_panel.py
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QSlider, QLabel, QProgressBar
from PyQt6.QtCore import Qt

class MixerPanel(QFrame):
    def __init__(self, audio_system):
        super().__init__()
        self.audio = audio_system
        self.init_ui()

    def init_ui(self):
        mixer_layout = QHBoxLayout(self)
        mixer_layout.setContentsMargins(4, 4, 4, 4)
        mixer_layout.setSpacing(6)
        
        # 1. Ползунок Усиления (Усилитель / Gain)
        gain_layout = QVBoxLayout()
        self.lbl_gain_val = QLabel("<center><span style='color: #b88eff; font-size: 8px;'>х1.0</span></center>")
        gain_layout.addWidget(QLabel("<center><span style='color: #a370f7; font-size: 8px;'>Усиление</span></center>"))
        gain_layout.addWidget(self.lbl_gain_val)
        
        self.slider_gain = QSlider(Qt.Orientation.Vertical)
        self.slider_gain.setRange(10, 50)  # Множитель от 1.0 до 5.0
        self.slider_gain.setValue(10)
        self.slider_gain.setStyleSheet("QSlider::handle:vertical { background: #a370f7; height: 10px; border-radius: 5px; }")
        self.slider_gain.valueChanged.connect(self.on_gain_changed)
        gain_layout.addWidget(self.slider_gain)
        mixer_layout.addLayout(gain_layout)

        # 2. Ползунок Речи (зеленый)
        slider_talk_layout = QVBoxLayout()
        self.lbl_talk_val = QLabel("<center><span style='color: #4caf50; font-size: 8px;'>12</span></center>")
        slider_talk_layout.addWidget(QLabel("<center><span style='color: #4caf50; font-size: 8px;'>Речь</span></center>"))
        slider_talk_layout.addWidget(self.lbl_talk_val)
        
        self.slider_talk = QSlider(Qt.Orientation.Vertical)
        self.slider_talk.setRange(1, 100)
        self.slider_talk.setValue(12)
        self.slider_talk.setObjectName("talk")
        self.slider_talk.valueChanged.connect(lambda val: self.lbl_talk_val.setText(f"<center><span style='color: #4caf50; font-size: 8px;'>{val}</span></center>"))
        slider_talk_layout.addWidget(self.slider_talk)
        mixer_layout.addLayout(slider_talk_layout)

        # 3. Ползунок Крика (красный)
        slider_shout_layout = QVBoxLayout()
        self.lbl_shout_val = QLabel("<center><span style='color: #f44336; font-size: 8px;'>40</span></center>")
        slider_shout_layout.addWidget(QLabel("<center><span style='color: #f44336; font-size: 8px;'>Крик</span></center>"))
        slider_shout_layout.addWidget(self.lbl_shout_val)
        
        self.slider_shout = QSlider(Qt.Orientation.Vertical)
        self.slider_shout.setRange(1, 100)
        self.slider_shout.setValue(40)
        self.slider_shout.setObjectName("shout")
        self.slider_shout.valueChanged.connect(lambda val: self.lbl_shout_val.setText(f"<center><span style='color: #f44336; font-size: 8px;'>{val}</span></center>"))
        slider_shout_layout.addWidget(self.slider_shout)
        mixer_layout.addLayout(slider_shout_layout)

        # 4. Вертикальная шкала громкости
        vol_bar_layout = QVBoxLayout()
        vol_bar_layout.addWidget(QLabel("<center><span style='color: #aaa; font-size: 8px;'>Звук</span></center>"))
        vol_bar_layout.addWidget(QLabel("")) # Заглушка подравнивания высоты
        
        self.vol_bar = QProgressBar()
        self.vol_bar.setOrientation(Qt.Orientation.Vertical)
        self.vol_bar.setRange(0, 100)
        self.vol_bar.setValue(0)
        self.vol_bar.setTextVisible(False)
        self.vol_bar.setFixedWidth(14)
        self.vol_bar.setStyleSheet(
            "QProgressBar { background-color: #2d2d30; border: 1px solid #444; border-radius: 2px; } "
            "QProgressBar::chunk { background-color: #4caf50; }"
        )
        vol_bar_layout.addWidget(self.vol_bar)
        mixer_layout.addLayout(vol_bar_layout)

    def on_gain_changed(self, val):
        gain_factor = val / 10.0
        if hasattr(self, 'audio') and self.audio:
            self.audio.gain = gain_factor
        self.lbl_gain_val.setText(f"<center><span style='color: #b88eff; font-size: 8px;'>х{gain_factor:.1f}</span></center>")

    def update_volume_display(self, vol, thresh_talk, thresh_shout):
        """Обновление прыгающего столбика звука в виде оранжевых пиксельных кубиков"""
        bar_value = int(vol * 250)
        self.vol_bar.setValue(min(100, bar_value))
        
        # Ползунок звука теперь всегда заполняется пиксельными кубиками с оранжевым свечением
        self.vol_bar.setStyleSheet("""
            QProgressBar { 
                background-color: #111114; 
                border: 2px solid #ff7700; 
                border-radius: 2px; 
            } 
            QProgressBar::chunk { 
                background-image: repeating-linear-gradient(0deg, #ff5500, #ff5500 8px, #111114 8px, #111114 11px);
                border-radius: 1px;
            }
        """)
