from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QSlider, QLabel, QProgressBar
from PyQt6.QtCore import Qt


class MixerPanel(QFrame):
    def __init__(self, audio_system):
        super().__init__()
        self.audio = audio_system
        self.init_ui()

    def init_ui(self):
        mixer_layout = QHBoxLayout(self)
        mixer_layout.setContentsMargins(0, 0, 4, 0)
        mixer_layout.setSpacing(4)

        # 1. Ползунок Речи (зеленый)
        slider_talk_layout = QVBoxLayout()
        slider_talk_layout.addWidget(QLabel("<center><span style='color: #4caf50; font-size: 8px;'>Речь</span></center>"))
        self.slider_talk = QSlider(Qt.Orientation.Vertical)
        self.slider_talk.setRange(1, 150)
        self.slider_talk.setValue(25)
        self.slider_talk.setStyleSheet("QSlider::handle:vertical { background: #4caf50; height: 10px; border-radius: 5px; }")
        slider_talk_layout.addWidget(self.slider_talk)
        mixer_layout.addLayout(slider_talk_layout)

        # 2. Ползунок Крика (красный)
        slider_shout_layout = QVBoxLayout()
        slider_shout_layout.addWidget(QLabel("<center><span style='color: #f44336; font-size: 8px;'>Крик</span></center>"))
        self.slider_shout = QSlider(Qt.Orientation.Vertical)
        self.slider_shout.setRange(1, 150)
        self.slider_shout.setValue(80)
        self.slider_shout.setStyleSheet("QSlider::handle:vertical { background: #f44336; height: 10px; border-radius: 5px; }")
        slider_shout_layout.addWidget(self.slider_shout)
        mixer_layout.addLayout(slider_shout_layout)

        # 3. Вертикальная шкала громкости
        vol_bar_layout = QVBoxLayout()
        vol_bar_layout.addWidget(QLabel("<center><span style='color: #aaa; font-size: 8px;'>Звук</span></center>"))
        self.vol_bar = QProgressBar()
        self.vol_bar.setOrientation(Qt.Orientation.Vertical)
        self.vol_bar.setRange(0, 100)
        self.vol_bar.setValue(0)
        self.vol_bar.setTextVisible(False)
        self.vol_bar.setFixedWidth(12)
        self.vol_bar.setStyleSheet(
            "QProgressBar { background-color: #2d2d30; border: 1px solid #444; border-radius: 2px; } "
            "QProgressBar::chunk { background-color: #4caf50; }"
        )
        vol_bar_layout.addWidget(self.vol_bar)
        mixer_layout.addLayout(vol_bar_layout)

    def update_volume_display(self, vol, thresh_talk, thresh_shout):
        """Обновление прыгающего столбика громкости и его цвета"""
        bar_value = int(vol * 500)
        self.vol_bar.setValue(min(100, bar_value))
        if vol > thresh_shout:
            self.vol_bar.setStyleSheet(
                "QProgressBar { background-color: #2d2d30; border: 1px solid #444; } "
                "QProgressBar::chunk { background-color: #f44336; }"
            )
        elif vol > thresh_talk:
            self.vol_bar.setStyleSheet(
                "QProgressBar { background-color: #2d2d30; border: 1px solid #444; } "
                "QProgressBar::chunk { background-color: #ffaa00; }"
            )
        else:
            self.vol_bar.setStyleSheet(
                "QProgressBar { background-color: #2d2d30; border: 1px solid #444; } "
                "QProgressBar::chunk { background-color: #4caf50; }"
            )