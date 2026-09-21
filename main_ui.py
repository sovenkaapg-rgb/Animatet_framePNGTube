from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QFrame
from timeline_widgets import SkinSettingsWidget, EffectSettingsWidget

class MainWindowUI:
    def setup_ui(self, window):
        """Настройка всего внешнего вида главного окна"""
        central_widget = QWidget()
        window.setCentralWidget(central_widget)
        
        window.main_layout = QVBoxLayout(central_widget)
        window.main_layout.setContentsMargins(10, 10, 10, 10)
        window.main_layout.setSpacing(8)
        
        # 1. ВЕРХНЯЯ ПАНЕЛЬ КОНТРОЛЛЕРОВ
        window.top_bar_widget = QWidget()
        top_bar = QHBoxLayout(window.top_bar_widget)
        top_bar.setContentsMargins(0, 0, 0, 0)
        
        left_audio_layout = QVBoxLayout()
        window.lbl_audio_input_title = QLabel("<b>AUDIO INPUT</b> | Переназначение звуковых устр. - Input")
        left_audio_layout.addWidget(window.lbl_audio_input_title)
        
        window.box_microphones = QComboBox()
        window.box_microphones.setMinimumWidth(250)
        window.box_microphones.currentIndexChanged.connect(window.on_microphone_changed)
        left_audio_layout.addWidget(window.box_microphones)
        top_bar.addLayout(left_audio_layout)
        
        top_bar.addStretch()
        
        window.btn_reset_ui = QPushButton("🗑 СБРОС НАСТРОЕК")
        window.btn_reset_ui.clicked.connect(window.reset_all_database_prompt)
        top_bar.addWidget(window.btn_reset_ui)
        
        window.btn_toggle_stream = QPushButton("LAUNCH STREAM")
        window.btn_toggle_stream.setObjectName("btn_stream_trigger")
        window.btn_toggle_stream.clicked.connect(window.toggle_stream_mode)
        top_bar.addWidget(window.btn_toggle_stream)
        
        window.main_layout.addWidget(window.top_bar_widget)
        
        # Инициализация боковых панелей параметров
        window.timeline_panel.skin_settings = SkinSettingsWidget(window.timeline_panel)
        window.timeline_panel.effect_settings = EffectSettingsWidget(window.timeline_panel)

        # Синхронизация переключения эффектов в выпадающем списке
        window.timeline_panel.effect_settings.box_active_effects.currentIndexChanged.connect(
            window.timeline_panel.effect_settings.load_selected_effect_data_into_ui
        )

        # 2. СРЕДНЯЯ ЧАСТЬ (Микшер + Аватар + Панели справа)
        window.middle_container = QWidget()
        middle_layout = QHBoxLayout(window.middle_container)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(15)
        
        window.left_side_layout = QHBoxLayout()
        window.left_side_layout.addWidget(window.mixer_panel)
        window.left_side_layout.addWidget(window.avatar_render, stretch=1)
        middle_layout.addLayout(window.left_side_layout, stretch=2) 
        
        window.right_side_widget = QFrame()
        right_side_layout = QVBoxLayout(window.right_side_widget)
        right_side_layout.setContentsMargins(4, 4, 4, 4)
        right_side_layout.setSpacing(10)
        
        right_side_layout.addWidget(window.timeline_panel.skin_settings)
        right_side_layout.addWidget(window.timeline_panel.effect_settings)
        
        right_side_layout.addStretch()
        middle_layout.addWidget(window.right_side_widget, stretch=1)
        window.main_layout.addWidget(window.middle_container, stretch=2)
        
        # 3. НИЖНЯЯ ЧАСТЬ (Управление режимами и кнопками)
        window.bottom_container = QWidget()
        bottom_layout = QHBoxLayout(window.bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)
        
        bottom_layout.addWidget(window.timeline_panel, stretch=1)
        
        window.skin_control_widget = QFrame()
        window.skin_control_widget.setFixedWidth(260)  
        skin_control_layout = QVBoxLayout(window.skin_control_widget)
        skin_control_layout.setContentsMargins(6, 6, 6, 6)
        skin_control_layout.setSpacing(6)
        
        window.btn_switch_mode = QPushButton("РЕЖИМ: НАСТРОЙКА СКИНА")
        
        def toggle_studio_mode():
            if window.timeline_panel.current_mode == "skin":
                window.timeline_panel.set_mode("effect")
                window.btn_switch_mode.setText("РЕЖИМ: НАСТРОЙКА ЭФФЕКТОВ")
                window.btn_switch_mode.setProperty("mode", "effect")
                window.timeline_panel.effect_settings.refresh_effects_list_source()
            else:
                window.timeline_panel.set_mode("skin")
                window.btn_switch_mode.setText("РЕЖИМ: НАСТРОЙКА СКИНА")
                window.btn_switch_mode.setProperty("mode", "skin")
                
            window.btn_switch_mode.style().unpolish(window.btn_switch_mode)
            window.btn_switch_mode.style().polish(window.btn_switch_mode)

        window.btn_switch_mode.clicked.connect(toggle_studio_mode)
        skin_control_layout.addWidget(window.btn_switch_mode)
        
        window.lbl_reward_profile_title = QLabel("<span style='color: #7c7c8a; font-size: 10px; font-weight: bold;'>ТЕКУЩИЙ АКТИВНЫЙ СКИН:</span>")
        skin_control_layout.addWidget(window.lbl_reward_profile_title)
        
        window.box_reward_profiles = QComboBox()
        window.box_reward_profiles.currentIndexChanged.connect(window.on_skin_dropdown_changed)
        skin_control_layout.addWidget(window.box_reward_profiles)
        
        row_create = QHBoxLayout()
        window.btn_create_skin = QPushButton("НОВЫЙ СКИН")
        window.btn_create_skin.clicked.connect(window.create_new_skin_action)
        row_create.addWidget(window.btn_create_skin)
        
        window.btn_create_effect = QPushButton("НОВЫЙ ЭФФЕКТ")
        window.btn_create_effect.clicked.connect(window.create_new_effect_action)
        row_create.addWidget(window.btn_create_effect)
        skin_control_layout.addLayout(row_create)
        
        window.btn_delete_skin = QPushButton("🗑 УДАЛИТЬ ТЕКУЩИЙ СКИН")
        window.btn_delete_skin.clicked.connect(window.delete_current_skin_action)
        skin_control_layout.addWidget(window.btn_delete_skin)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #2d2d30; margin-top: 4px; margin-bottom: 4px;")
        skin_control_layout.addWidget(line)
        
        window.btn_upload = QPushButton("UPLOAD FILE")
        window.btn_upload.clicked.connect(window.timeline_panel.upload_file)
        skin_control_layout.addWidget(window.btn_upload)
        
        window.btn_batch = QPushButton("UPLOAD FOLDER")
        window.btn_batch.clicked.connect(window.timeline_panel.open_batch_loader)
        skin_control_layout.addWidget(window.btn_batch)
        
        bottom_layout.addWidget(window.skin_control_widget, stretch=0)
        window.main_layout.addWidget(window.bottom_container, stretch=1)
        
        window.timeline_panel.set_mode("skin")

    def apply_theme(self, window):
        """Финальный стиль: Тёмно-графитовая база, фиолетовые контуры и оранжевые пиксельные кубики"""
        window.setStyleSheet("""
            QMainWindow, QWidget { 
                background-color: #16161a; /* Глубокий тёмно-графитовый */
                color: #e1e1e6; 
                font-family: 'Segoe UI', Tahoma, sans-serif; 
                font-size: 11px;
            }
            
            /* Главные панели: тонкая тёмно-фиолетовая ретро-обводка */
            QFrame#skin_settings_panel, 
            QFrame#effect_settings_panel {
                background-color: #1f1f24;
                border: 2px solid #4a285a; /* Тонкий тёмно-фиолетовый контур */
                border-radius: 3px; /* Микро-скругление */
            }
            
            #skin_settings_panel QWidget, 
            #effect_settings_panel QWidget {
                background-color: transparent;
            }
            
            QLabel { 
                color: #e1e1e6; 
                padding: 2px 0px; 
                background: transparent; 
                font-weight: bold;
                letter-spacing: 0.5px;
            }
            
            /* Списки и поля ввода */
            QLineEdit, QComboBox {
                background-color: #111114;
                border: 1px solid #4a285a;
                border-radius: 3px;
                color: #ffffff;
                padding: 5px;
                font-weight: bold;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 18px;
                border-left: 1px solid #4a285a;
            }
            
            /* Кнопки управления */
            QPushButton { 
                background-color: #1f1f24; 
                border: 2px solid #4a285a;
                border-radius: 3px; 
                color: #ffffff; 
                font-weight: bold;
                padding: 5px 12px; 
            }
            QPushButton:hover { 
                background-color: #ff7700; /* Выделение оранжевым при наведении */
                border-color: #ffffff;
                color: #111114;
            }
            QPushButton:pressed {
                background-color: #ffaa66;
                color: #111114;
            }
            
            /* Кнопка запуска стрима */
            QPushButton#btn_stream_trigger {
                background-color: #ff5500;
                border: 2px solid #ffffff;
                color: #ffffff;
            }
            QPushButton#btn_stream_trigger:hover {
                background-color: #ff7700;
                color: #111114;
            }
            
            /* ================================================================= */
            /* ПОЛЗУНКИ С КУБИКАМИ (КАК НА СКРИНШОТЕ)                             */
            /* ================================================================= */
            
            /* ГОРИЗОНТАЛЬНЫЕ ПОЛЗУНКИ (Параметры аватара) */
            QSlider::groove:horizontal {
                border: 2px solid #ff7700; /* Оранжевая рамка шкалы */
                height: 12px; 
                background-color: #111114; 
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                /* Рисуем оранжевые пиксельные кубики с черными разделителями в 3px */
                background-image: repeating-linear-gradient(90deg, #ff7700, #ff7700 8px, #111114 8px, #111114 11px);
                border-radius: 1px;
            }
            QSlider::handle:horizontal {
                background-color: #ffffff; 
                border: 1px solid #ff7700;
                width: 8px; 
                height: 20px; 
                margin-top: -5px; 
                border-radius: 1px;
            }
            
            /* ВЕРТИКАЛЬНЫЕ ПОЛЗУНКИ (Микшер звука) */
            QSlider::groove:vertical {
                border: 2px solid #ff7700; /* Оранжевая рамка шкалы */
                width: 12px; 
                background-color: #111114; 
                border-radius: 2px;
            }
            QSlider::add-page:vertical {
                /* Рисуем вертикальные оранжевые кубики, идущие снизу вверх */
                background-image: repeating-linear-gradient(0deg, #ff7700, #ff7700 8px, #111114 8px, #111114 11px);
                border-radius: 1px;
            }
            QSlider::handle:vertical {
                background-color: #ffffff; 
                border: 1px solid #ff7700;
                width: 20px; 
                height: 8px; 
                margin-left: -5px; 
                border-radius: 1px;
            }
        """)



