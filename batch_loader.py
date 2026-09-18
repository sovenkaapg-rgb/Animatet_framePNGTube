import os
import re
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QListWidgetItem, QPushButton, QLabel, QFileDialog,
                             QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize


class BatchLoaderDialog(QDialog):
    files_loaded = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📦 Массовая загрузка кадров")
        self.resize(700, 500)
        self.setModal(True)
        
        self.available_files = {}
        self.assigned_files = {}
        
        self.init_ui()
        
        # Глобальная тема для окна массовой загрузки
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #121214;
                color: #e1e1e6;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                border: 1px solid #282830;
                border-radius: 6px;
                margin-top: 12px;
                font-size: 10px;
                font-weight: bold;
                color: #a370f7;
                letter-spacing: 0.5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
            }
            QLabel {
                color: #7c7c8a;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }
            /* Главные фиолетовые кнопки */
            QPushButton#btn_select_folder, QPushButton#btn_confirm {
                background-color: #6324c4;
                border: none;
                border-radius: 4px;
                color: #ffffff;
                font-size: 10px;
                font-weight: bold;
                padding: 6px;
                letter-spacing: 0.5px;
            }
            QPushButton#btn_select_folder:hover, QPushButton#btn_confirm:hover {
                background-color: #7c3aed;
            }
            /* Второстепенные темные кнопки */
            QPushButton#btn_auto, QPushButton#btn_clear, QPushButton#btn_cancel {
                background-color: #202024;
                border: 1px solid #323238;
                border-radius: 4px;
                color: #e1e1e6;
                font-size: 10px;
                padding: 6px;
            }
            QPushButton#btn_auto:hover, QPushButton#btn_clear:hover {
                border-color: #4d1c9c;
                background-color: #1c1c22;
            }
            QPushButton#btn_cancel:hover {
                background-color: #d32f2f;
                border-color: #ef4444;
                color: white;
            }
            /* Списки файлов */
            QListWidget {
                background-color: #18181c;
                border: 1px solid #282830;
                border-radius: 4px;
                color: #e1e1e6;
                font-size: 10px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 4px;
            }
            QListWidget::item:hover {
                background-color: #202024;
                border-radius: 2px;
            }
            QListWidget::item:selected {
                background-color: #4d1c9c;
                color: white;
                border-radius: 2px;
            }
        """)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Кнопка выбора папки (Стиль привязан по ID)
        self.btn_select_folder = QPushButton("SELECT FOLDER WITH FRAMES")
        self.btn_select_folder.setObjectName("btn_select_folder")
        self.btn_select_folder.clicked.connect(self.select_folder)
        layout.addWidget(self.btn_select_folder)
        
        self.lbl_status = QLabel("Выберите папку с PNG файлами")
        self.lbl_status.setStyleSheet("padding: 2px;")
        layout.addWidget(self.lbl_status)
        
        columns_layout = QHBoxLayout()
        
        # Левая колонка
        left_group = QGroupBox("AVAILABLE FILES")
        left_layout = QVBoxLayout(left_group)
        left_layout.setContentsMargins(6, 12, 6, 6)
        self.list_available = QListWidget()
        self.list_available.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.list_available.itemDoubleClicked.connect(self.assign_selected_to_next_key)
        left_layout.addWidget(self.list_available)
        columns_layout.addWidget(left_group, stretch=1)
        
        # Правая колонка
        right_group = QGroupBox("CELL DISTRIBUTION")
        right_layout = QVBoxLayout(right_group)
        right_layout.setContentsMargins(6, 12, 6, 6)
        self.list_assigned = QListWidget()
        right_layout.addWidget(self.list_assigned)
        columns_layout.addWidget(right_group, stretch=1)
        
        layout.addLayout(columns_layout)
        
        # Средний блок функциональных кнопок
        btn_layout = QHBoxLayout()
        self.btn_auto_assign = QPushButton("AUTO ASSIGN")
        self.btn_auto_assign.setObjectName("btn_auto")
        self.btn_auto_assign.clicked.connect(self.auto_assign_by_order)
        self.btn_auto_assign.setEnabled(False)
        btn_layout.addWidget(self.btn_auto_assign)
        
        self.btn_clear = QPushButton("CLEAR")
        self.btn_clear.setObjectName("btn_clear")
        self.btn_clear.clicked.connect(self.clear_assignment)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)
        
        # Нижний финальный блок кнопок
        final_layout = QHBoxLayout()
        self.btn_load = QPushButton("LOAD FRAMES")
        self.btn_load.setObjectName("btn_confirm")
        self.btn_load.setEnabled(False)
        self.btn_load.clicked.connect(self.load_files)
        final_layout.addWidget(self.btn_load)
        
        self.btn_cancel = QPushButton("CANCEL")
        self.btn_cancel.setObjectName("btn_cancel")
        self.btn_cancel.clicked.connect(self.reject)
        final_layout.addWidget(self.btn_cancel)
        layout.addLayout(final_layout)
    
    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку с кадрами", "")
        if folder_path:
            self.load_files_from_folder(folder_path)
    
    def load_files_from_folder(self, folder_path):
        self.available_files.clear()
        self.list_available.clear()
        
        files = []
        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.png'):
                full_path = os.path.join(folder_path, filename)
                files.append((filename, full_path))
        
        files.sort(key=lambda x: natural_sort_key(x[0]))
        
        for filename, full_path in files:
            self.available_files[filename] = full_path
            item = QListWidgetItem(f"📄 {filename}")
            item.setData(Qt.ItemDataRole.UserRole, filename)
            self.list_available.addItem(item)
        
        self.lbl_status.setText(f"Найдено файлов: {len(files)}")
        
        if files:
            self.btn_auto_assign.setEnabled(True)
            self.btn_load.setEnabled(True)
    
    def auto_assign_by_order(self):
        self.assigned_files.clear()
        self.list_assigned.clear()
        
        available = list(self.available_files.keys())
        all_keys = [
            "idle_close_1", "idle_close_2", "idle_close_3",
            "talk_close", "talk_open", "talk_blink",
            "shout_close", "shout_open", "shout_blink",
            "sleep_close_1", "sleep_close_2", "sleep_close_3"
        ]
        
        for i, key in enumerate(all_keys):
            if i < len(available):
                filename = available[i]
                self.assigned_files[key] = filename
                item = QListWidgetItem(f"{key} → {filename}")
                item.setData(Qt.ItemDataRole.UserRole, (key, filename))
                self.list_assigned.addItem(item)
        
        self.lbl_status.setText(f"Авто-распределено: {len(self.assigned_files)} кадров")
    
    def assign_selected_to_next_key(self, item):
        filename = item.data(Qt.ItemDataRole.UserRole)
        if not filename:
            return
        
        all_keys = [
            "idle_close_1", "idle_close_2", "idle_close_3",
            "talk_close", "talk_open", "talk_blink",
            "shout_close", "shout_open", "shout_blink",
            "sleep_close_1", "sleep_close_2", "sleep_close_3"
        ]
        
        for key in all_keys:
            if key not in self.assigned_files:
                self.assigned_files[key] = filename
                list_item = QListWidgetItem(f"{key} → {filename}")
                list_item.setData(Qt.ItemDataRole.UserRole, (key, filename))
                self.list_assigned.addItem(list_item)
                self.lbl_status.setText(f"Назначено: {key}")
                break
        else:
            QMessageBox.warning(self, "Внимание", "Все ячейки уже заполнены!")
    
    def clear_assignment(self):
        self.assigned_files.clear()
        self.list_assigned.clear()
        self.lbl_status.setText("Распределение очищено")
    
    def load_files(self):
        if not self.assigned_files:
            QMessageBox.warning(self, "Внимание", "Нет назначенных файлов!")
            return
        
        result = {}
        for key, filename in self.assigned_files.items():
            if filename in self.available_files:
                result[key] = self.available_files[filename]
        
        self.files_loaded.emit(result)
        self.accept()


def natural_sort_key(filename):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', filename)]
