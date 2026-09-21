# skin_management_panel.py
import os
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox

class SkinManagementPanel(QFrame):
    """Отдельный блок в правом углу для управления скинами и кнопками загрузки медиафайлов"""
    
    def __init__(self, main_window, timeline_panel):
        super().__init__()
        self.window = main_window
        self.timeline_panel = timeline_panel
        
        self.setStyleSheet("background-color: #1e1e1e; padding: 6px; border-radius: 4px;")
        self.init_ui()

    def init_ui(self):
        control_layout = QHBoxLayout(self) 
        control_layout.setSpacing(12)
        control_layout.setContentsMargins(4, 4, 4, 4)
        
        # --- БЛОК А: УПРАВЛЕНИЕ СКИНАМИ ---
        skin_mgmt_layout = QVBoxLayout()
        skin_mgmt_layout.setSpacing(4)
        
        lbl_skin_title = QLabel("<span style='color: #7c7c8a; font-size: 9px; font-weight: bold;'>АКТИВНЫЙ СКИН:</span>")
        skin_mgmt_layout.addWidget(lbl_skin_title)
        
        self.window.box_reward_profiles = QComboBox()
        self.window.box_reward_profiles.currentIndexChanged.connect(self.window.on_skin_dropdown_changed)
        skin_mgmt_layout.addWidget(self.window.box_reward_profiles)
        
        row_create = QHBoxLayout()
        self.window.btn_create_skin = QPushButton("➕ НОВЫЙ СКИН")
        self.window.btn_create_skin.setStyleSheet("background-color: #1e3c20; border: 1px solid #2d5a30; font-size: 10px; font-weight: bold;")
        self.window.btn_create_skin.clicked.connect(self.window.create_new_skin_action)
        row_create.addWidget(self.window.btn_create_skin)
        
        self.window.btn_create_effect = QPushButton("✨ НОВЫЙ ЭФФЕКТ")
        self.window.btn_create_effect.setStyleSheet("background-color: #3c1e3b; border: 1px solid #5a2d59; font-size: 10px; font-weight: bold;")
        self.window.btn_create_effect.clicked.connect(self.window.create_new_effect_action)
        row_create.addWidget(self.window.btn_create_effect)
        skin_mgmt_layout.addLayout(row_create)
        
        self.window.btn_delete_skin = QPushButton("🗑 УДАЛИТЬ ТЕКУЩИЙ СКИН")
        self.window.btn_delete_skin.setStyleSheet("background-color: #2d1616; border: 1px solid #5a2525; color: #ff5555; font-size: 10px; font-weight: bold; padding: 4px;")
        self.window.btn_delete_skin.clicked.connect(self.window.delete_current_skin_action)
        skin_mgmt_layout.addWidget(self.window.btn_delete_skin)
        
        control_layout.addLayout(skin_mgmt_layout)
        
        # --- БЛОК Б: ЗАГРУЗКА ФАЙЛОВ В ЯЧЕЙКУ ---
        file_io_layout = QVBoxLayout()
        file_io_layout.setSpacing(4)
        
        self.timeline_panel.lbl_title = QLabel("<b>ЯЧЕЙКА КАДРА</b>")
        self.timeline_panel.lbl_title.setStyleSheet("color: #569cd6; font-size: 9px;")
        file_io_layout.addWidget(self.timeline_panel.lbl_title)
        
        self.btn_upload = QPushButton("UPLOAD FILE")
        self.btn_upload.setStyleSheet("""
            QPushButton {
                background-color: #6324c4; border: none; border-radius: 4px;
                color: #ffffff; font-size: 9px; padding: 5px 10px; font-weight: bold;
            }
            QPushButton:hover { background-color: #7c3aed; }
        """)
        self.btn_upload.clicked.connect(self.timeline_panel.upload_file)
        file_io_layout.addWidget(self.btn_upload)
        
        self.btn_batch = QPushButton("UPLOAD FOLDER")
        self.btn_batch.setStyleSheet("""
            QPushButton {
                background-color: #6324c4; border: none; border-radius: 4px;
                color: #ffffff; font-size: 9px; padding: 5px 10px; font-weight: bold;
            }
            QPushButton:hover { background-color: #7c3aed; }
        """)
        self.btn_batch.clicked.connect(self.timeline_panel.open_batch_loader)
        file_io_layout.addWidget(self.btn_batch)
        
        control_layout.addLayout(file_io_layout)
# skin_management_panel.py
import os
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox

class SkinManagementPanel(QFrame):
    """Отдельный блок в правом углу для управления скинами и кнопками загрузки медиафайлов"""
    
    def __init__(self, main_window, timeline_panel):
        super().__init__()
        self.window = main_window
        self.timeline_panel = timeline_panel
        
        self.setStyleSheet("background-color: #1e1e1e; padding: 6px; border-radius: 4px;")
        self.init_ui()

    def init_ui(self):
        control_layout = QHBoxLayout(self) 
        control_layout.setSpacing(12)
        control_layout.setContentsMargins(4, 4, 4, 4)
        
        # --- БЛОК А: УПРАВЛЕНИЕ СКИНАМИ ---
        skin_mgmt_layout = QVBoxLayout()
        skin_mgmt_layout.setSpacing(4)
        
        lbl_skin_title = QLabel("<span style='color: #7c7c8a; font-size: 9px; font-weight: bold;'>АКТИВНЫЙ СКИН:</span>")
        skin_mgmt_layout.addWidget(lbl_skin_title)
        
        self.window.box_reward_profiles = QComboBox()
        self.window.box_reward_profiles.currentIndexChanged.connect(self.window.on_skin_dropdown_changed)
        skin_mgmt_layout.addWidget(self.window.box_reward_profiles)
        
        row_create = QHBoxLayout()
        self.window.btn_create_skin = QPushButton("➕ НОВЫЙ СКИН")
        self.window.btn_create_skin.setStyleSheet("background-color: #1e3c20; border: 1px solid #2d5a30; font-size: 10px; font-weight: bold;")
        self.window.btn_create_skin.clicked.connect(self.window.create_new_skin_action)
        row_create.addWidget(self.window.btn_create_skin)
        
        self.window.btn_create_effect = QPushButton("✨ НОВЫЙ ЭФФЕКТ")
        self.window.btn_create_effect.setStyleSheet("background-color: #3c1e3b; border: 1px solid #5a2d59; font-size: 10px; font-weight: bold;")
        self.window.btn_create_effect.clicked.connect(self.window.create_new_effect_action)
        row_create.addWidget(self.window.btn_create_effect)
        skin_mgmt_layout.addLayout(row_create)
        
        self.window.btn_delete_skin = QPushButton("🗑 УДАЛИТЬ ТЕКУЩИЙ СКИН")
        self.window.btn_delete_skin.setStyleSheet("background-color: #2d1616; border: 1px solid #5a2525; color: #ff5555; font-size: 10px; font-weight: bold; padding: 4px;")
        self.window.btn_delete_skin.clicked.connect(self.window.delete_current_skin_action)
        skin_mgmt_layout.addWidget(self.window.btn_delete_skin)
        
        control_layout.addLayout(skin_mgmt_layout)
        
        # --- БЛОК Б: ЗАГРУЗКА ФАЙЛОВ В ЯЧЕЙКУ ---
        file_io_layout = QVBoxLayout()
        file_io_layout.setSpacing(4)
        
        self.timeline_panel.lbl_title = QLabel("<b>ЯЧЕЙКА КАДРА</b>")
        self.timeline_panel.lbl_title.setStyleSheet("color: #569cd6; font-size: 9px;")
        file_io_layout.addWidget(self.timeline_panel.lbl_title)
        
        self.btn_upload = QPushButton("UPLOAD FILE")
        self.btn_upload.setStyleSheet("""
            QPushButton {
                background-color: #6324c4; border: none; border-radius: 4px;
                color: #ffffff; font-size: 9px; padding: 5px 10px; font-weight: bold;
            }
            QPushButton:hover { background-color: #7c3aed; }
        """)
        self.btn_upload.clicked.connect(self.timeline_panel.upload_file)
        file_io_layout.addWidget(self.btn_upload)
        
        self.btn_batch = QPushButton("UPLOAD FOLDER")
        self.btn_batch.setStyleSheet("""
            QPushButton {
                background-color: #6324c4; border: none; border-radius: 4px;
                color: #ffffff; font-size: 9px; padding: 5px 10px; font-weight: bold;
            }
            QPushButton:hover { background-color: #7c3aed; }
        """)
        self.btn_batch.clicked.connect(self.timeline_panel.open_batch_loader)
        file_io_layout.addWidget(self.btn_batch)
        
        control_layout.addLayout(file_io_layout)
