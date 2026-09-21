import os
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QFrame
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor

class StreamWindow(QMainWindow):
    def __init__(self, avatar_render, parent_main_window):
        super().__init__()
        self.main_win = parent_main_window
        self.avatar_render = avatar_render
        self._is_closing = False  # Флаг-защита от бесконечной рекурсии при закрытии окна
        
        self.setWindowTitle("Покадровая Студия — OBS Окно")
        
        # БАГ ИСПРАВЛЕН: Включаем честную прозрачность окна вместо ядовито-зеленого хромакея.
        # В OBS теперь можно использовать "Захват игры" или "Захват окна" с включенной прозрачностью.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowMinimizeButtonHint)
        
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        self.init_ui()
        self.resize_to_avatar_bounds()

    def init_ui(self):
        central_widget = QWidget()
        # Задаем центральному виджету прозрачный фон
        central_widget.setStyleSheet("background: transparent;")
        self.setCentralWidget(central_widget)
        
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.main_layout.addWidget(self.avatar_render, stretch=1)
        
        # Нижняя плашка управления
        self.control_panel = QFrame()
        self.control_panel.setStyleSheet("""
            QFrame { 
                background-color: #16161a; 
                border-top: 2px solid #4a285a; /* Верхний фиолетовый контур панели */
            }
            QLabel { 
                color: #ff7700; 
                font-size: 11px; 
                font-family: 'Segoe UI', sans-serif; 
                font-weight: bold; 
                background: transparent; 
            }
            QComboBox { 
                background-color: #111114; 
                border: 1px solid #4a285a; 
                border-radius: 3px; 
                color: #ffffff; 
                padding: 3px 8px; 
                min-width: 160px; 
                font-weight: bold; 
            }
            QPushButton { 
                background-color: #1f1f24; 
                border: 2px solid #4a285a; 
                border-radius: 3px; 
                color: #ffffff; 
                font-size: 11px; 
                padding: 4px 12px; 
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #ff7700; 
                color: #111114; 
                border-color: #ffffff; 
            }
            QPushButton#btn_close_stream { 
                background-color: #2d1616; 
                border-color: #5a2525; 
                color: #ff5555; 
                font-weight: bold; 
            }
            QPushButton#btn_close_stream:hover { 
                background-color: #ef4444; 
                color: #ffffff; 
                border-color: #ffffff; 
            }
        """)


        
        panel_layout = QHBoxLayout(self.control_panel)
        panel_layout.setContentsMargins(10, 6, 10, 6)
        panel_layout.setSpacing(10)
        
        panel_layout.addWidget(QLabel("ВЫБОР СКИНА:"))
        self.combo_live_profiles = QComboBox()
        self.combo_live_profiles.currentIndexChanged.connect(self.on_profile_switched)
        panel_layout.addWidget(self.combo_live_profiles)
        
        panel_layout.addStretch(1)
        
        btn_minimize = QPushButton("🟡 Свернуть")
        btn_minimize.clicked.connect(self.showMinimized)
        panel_layout.addWidget(btn_minimize)
        
        btn_back_to_menu = QPushButton("🔴 В МЕНЮ")
        btn_back_to_menu.setObjectName("btn_close_stream")
        btn_back_to_menu.clicked.connect(self.close)
        panel_layout.addWidget(btn_back_to_menu)
        
        self.main_layout.addWidget(self.control_panel)
        self.refresh_skins_list()

    def resize_to_avatar_bounds(self):
        if hasattr(self.avatar_render, 'current_frame_size') and self.avatar_render.current_frame_size:
            w = self.avatar_render.current_frame_size.width()
            h = self.avatar_render.current_frame_size.height()
        else:
            w, h = 500, 500 
        self.setFixedSize(max(500, w), h + 45)

    def refresh_skins_list(self):
        self.combo_live_profiles.blockSignals(True)
        self.combo_live_profiles.clear()
        if hasattr(self.main_win, 'box_reward_profiles') and self.main_win.box_reward_profiles:
            main_combo = self.main_win.box_reward_profiles
            for i in range(main_combo.count()):
                self.combo_live_profiles.addItem(main_combo.itemText(i))
            self.combo_live_profiles.setCurrentIndex(main_combo.currentIndex())
        self.combo_live_profiles.blockSignals(False)

    def on_profile_switched(self, index):
        if index >= 0 and hasattr(self.main_win, 'box_reward_profiles'):
            self.main_win.box_reward_profiles.setCurrentIndex(index)

    def keyPressEvent(self, event):
        """Отслеживание нажатий для активации эффектов поверх скина"""
        if hasattr(self, 'main_win') and self.main_win:
            self.main_win.keyPressEvent(event)
        elif hasattr(self, 'parent') and self.parent():
            self.parent().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        # БАГ ИСПРАВЛЕН: Добавлена проверка флага self._is_closing. 
        # Она предотвращает бесконечную рекурсию взаимовызовов close() между MainWindow и StreamWindow
        if self._is_closing:
            event.accept()
            return
            
        self._is_closing = True
        if hasattr(self.main_win, 'toggle_stream_mode'):
            if self.main_win.is_stream_mode:
                self.main_win.toggle_stream_mode()
        event.accept()
