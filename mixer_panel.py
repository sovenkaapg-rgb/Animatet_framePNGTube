# mixer_panel.py
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QSlider, QLabel, QProgressBar
from PyQt6.QtCore import Qt

class MixerPanel(QFrame):
    def __init__(self, audio_system):
        super().__init__()
        self.audio = audio_system
        self.init_ui()
        
        # ИСПРАВЛЕНО: Связываем ползунки с аудиосистемой для управления порогами речи/крика
        self.slider_talk.valueChanged.connect(self.audio.set_threshold)
        self.slider_shout.valueChanged.connect(self.audio.set_shout_threshold)
        
        # ИСПРАВЛЕНО: Подписываем визуализатор на события изменения громкости
        self.audio.volume_changed.connect(self.on_volume_received)

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

    def on_volume_received(self, vol):
        """Промежуточный слот для сбора актуальных порогов и вызова отрисовки"""
        self.update_volume_display(vol, self.audio.volume_threshold, self.audio.shout_threshold)

    def update_volume_display(self, vol, thresh_talk, thresh_shout):
        """Обновление прыгающего столбика звука в виде оранжевых пиксельных кубиков"""
        bar_value = int(vol * 250)
        self.vol_bar.setValue(min(100, bar_value))
        
        # ИСПРАВЛЕНО: Корректный вертикальный градиент (from bottom to top) 
        # с четкими границами для эффекта пиксельных кубиков
        self.vol_bar.setStyleSheet("""
            QProgressBar { 
                background-color: #111114; 
                border: 2px solid #ff7700; 
                border-radius: 2px; 
            } 
            QProgressBar::chunk { 
                background-color: #ff5500;
                background-image: repeating-linear-gradient(to top, #ff5500, #ff5500 6px, #111114 6px, #111114 9px);
            }
        """)
