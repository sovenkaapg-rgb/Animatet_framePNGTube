# batch_loader.py
import os
import re
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QListWidget, QListWidgetItem, QPushButton, QLabel, 
                             QFileDialog, QMessageBox, QGroupBox, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon

# БАГ ИСПРАВЛЕН: Функция перенесена на самый верх файла, чтобы избежать ошибок NameError при вызове в __init__
def natural_sort_key(filename):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', filename)]

class BatchLoaderDialog(QDialog):
    # Сигнал для передачи готового словаря расстановки в главное окно
    files_loaded = pyqtSignal(dict)
    
    # Статическое (классовое) хранилище, чтобы загруженные файлы не стирались при закрытии окна
    _global_asset_library = {} 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Библиотека ассетов и Менеджер кадров")
        self.resize(850, 550)
        self.setModal(True)
        
        # Текущая расстановка для таймлайна (Ячейка -> Полный путь к файлу)
        self.assigned_map = {}
        
        # Безопасно считываем текущие кадры из главного окна аватара
        if parent:
            main_win = parent.window()
            if hasattr(main_win, 'avatar_render') and hasattr(main_win.avatar_render, 'layers'):
                if isinstance(main_win.avatar_render.layers, dict):
                    for k, v in main_win.avatar_render.layers.items():
                        if v and os.path.exists(str(v)):
                            self.assigned_map[k] = v

        self.init_ui()
        self.apply_styles()
        self.refresh_library_list()
        self.refresh_assigned_list()

    def apply_styles(self):
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #16161a; /* Глубокий тёмно-графитовый фон */
                color: #e1e1e6;
                font-family: 'Segoe UI', Tahoma, sans-serif;
            }
            QGroupBox {
                border: 2px solid #4a285a; /* Тонкий тёмно-фиолетовый контур */
                border-radius: 3px;
                margin-top: 12px;
                font-size: 11px;
                font-weight: bold;
                color: #ff7700; /* Оранжевый заголовок группы */
                letter-spacing: 0.5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 5px;
            }
            QLabel {
                color: #ffaa66;
                font-size: 11px;
                font-weight: bold;
            }
            QListWidget {
                background-color: #111114; /* Вдавленный тёмный список ассетов */
                border: 1px solid #4a285a;
                border-radius: 3px;
                color: #ffffff;
                font-size: 11px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #1f1f24;
            }
            QListWidget::item:hover {
                background-color: #1f1f24;
                border-radius: 2px;
            }
            QListWidget::item:selected {
                background-color: #ff7700; /* Оранжевое выделение активного ассета */
                color: #111114;
                font-weight: bold;
                border-radius: 2px;
            }
            QPushButton {
                background-color: #1f1f24;
                border: 2px solid #4a285a;
                border-radius: 3px;
                color: #ffffff;
                font-size: 11px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff7700;
                border-color: #ffffff;
                color: #111114;
            }
            QPushButton#btn_add_files, QPushButton#btn_add_folder, QPushButton#btn_confirm {
                background-color: #2a1a0c;
                border: 2px solid #ff7700;
                color: #ff7700;
            }
            QPushButton#btn_add_files:hover, QPushButton#btn_add_folder:hover, QPushButton#btn_confirm:hover {
                background-color: #ff7700;
                color: #111114;
                border-color: #ffffff;
            }
            QPushButton#btn_delete_asset {
                background-color: #2d1616;
                border: 1px solid #5a2525;
                color: #ff5555;
            }
            QPushButton#btn_delete_asset:hover {
                background-color: #ef4444;
                color: #ffffff;
            }
        """)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        top_btn_layout = QHBoxLayout()
        self.btn_add_files = QPushButton("ДОБАВИТЬ PNG ФАЙЛЫ")
        self.btn_add_files.setObjectName("btn_add_files")
        self.btn_add_files.clicked.connect(self.import_individual_files)
        top_btn_layout.addWidget(self.btn_add_files)
        
        self.btn_add_folder = QPushButton("ИМПОРТИРОВАТЬ ПАПКУ")
        self.btn_add_folder.setObjectName("btn_add_folder")
        self.btn_add_folder.clicked.connect(self.import_entire_folder)
        top_btn_layout.addWidget(self.btn_add_folder)
        main_layout.addLayout(top_btn_layout)
        
        columns_layout = QHBoxLayout()
        
        left_group = QGroupBox("БИБЛИОТЕКА ЗАГРУЖЕННЫХ АССЕТОВ")
        left_layout = QVBoxLayout(left_group)
        left_layout.setContentsMargins(8, 14, 8, 8)
        
        self.list_library = QListWidget()
        self.list_library.itemDoubleClicked.connect(self.shortcut_assign_to_next)
        left_layout.addWidget(self.list_library)
        
        self.btn_delete_asset = QPushButton("🗑 Удалить выделенные из базы")
        self.btn_delete_asset.setObjectName("btn_delete_asset")
        self.btn_delete_asset.clicked.connect(self.delete_selected_assets)
        left_layout.addWidget(self.btn_delete_asset)
        
        columns_layout.addWidget(left_group, stretch=4)
        
        mid_control_layout = QVBoxLayout()
        mid_control_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_move_to = QPushButton("➡")
        self.btn_move_to.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px 5px;")
        self.btn_move_to.clicked.connect(self.assign_current_selection)
        mid_control_layout.addWidget(self.btn_move_to)
        columns_layout.addLayout(mid_control_layout, stretch=0)
        
        right_group = QGroupBox("ТЕКУЩАЯ КАРТА ТАЙМЛАЙНА (12 ЯЧЕЕК)")
        right_layout = QVBoxLayout(right_group)
        right_layout.setContentsMargins(10, 16, 10, 10)
        
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(6)
        
        self.matrix_structure = [
            ["idle_close_1", "idle_close_2", "idle_close_3"],
            ["talk_close",   "talk_open",    "talk_blink"],
            ["shout_close",  "shout_open",   "shout_blink"],
            ["sleep_close_1", "sleep_close_2", "sleep_close_3"]
        ]
        
        self.cell_buttons = {}
        
        self.grid_layout.addWidget(QLabel("<span style='color: #a370f7; font-weight:bold; font-size:10px;'>IDLE</span>"), 0, 0)
        self.grid_layout.addWidget(QLabel("<span style='color: #e1e1e6; font-weight:bold; font-size:10px;'>TALK</span>"), 1, 0)
        self.grid_layout.addWidget(QLabel("<span style='color: #e1e1e6; font-weight:bold; font-size:10px;'>SHOUT</span>"), 2, 0)
        self.grid_layout.addWidget(QLabel("<span style='color: #7c7c8a; font-weight:bold; font-size:10px;'>SLEEP</span>"), 3, 0)
        
        for row_idx in range(4):
            for col_idx in range(3):
                key = self.matrix_structure[row_idx][col_idx]
                btn = QPushButton("[ ]")
                btn.setCheckable(True)
                btn.setFixedSize(65, 48)
                btn.setIconSize(QSize(55, 38))
                btn.setToolTip(f"Ячейка: {key.upper()}")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #18181c; border: 1px solid #282830;
                        border-radius: 4px; color: #4d4d57; font-size: 10px;
                    }
                    QPushButton:hover { border-color: #4d1c9c; background-color: #1c1c22; }
                    QPushButton:checked { border: 2px solid #a370f7; background-color: #202024; color: #e1e1e6; }
                """)
                btn.clicked.connect(lambda checked, k=key: self.on_cell_clicked(k))
                
                self.grid_layout.addWidget(btn, row_idx, col_idx + 1)
                self.cell_buttons[key] = btn
                
        right_layout.addLayout(self.grid_layout)
        
        right_utils = QHBoxLayout()
        self.btn_auto = QPushButton("Авто по порядку")
        self.btn_auto.clicked.connect(self.auto_assign_all_library)
        right_utils.addWidget(self.btn_auto)
        
        self.btn_clear_map = QPushButton("Сбросить ячейки")
        self.btn_clear_map.clicked.connect(self.clear_current_map)
        right_utils.addWidget(self.btn_clear_map)
        right_layout.addLayout(right_utils)
        
        columns_layout.addWidget(right_group, stretch=5)
        main_layout.addLayout(columns_layout)
        
        self.lbl_status = QLabel("Менеджер готов. Кликните по ячейке справа, затем по файлу слева и нажмите ➡.")
        main_layout.addWidget(self.lbl_status)
        
        final_layout = QHBoxLayout()
        self.btn_confirm = QPushButton("ПРИМЕНИТЬ ИЗМЕНЕНИЯ В ТАЙМЛАЙН")
        self.btn_confirm.setObjectName("btn_confirm")
        self.btn_confirm.clicked.connect(self.commit_to_timeline)
        final_layout.addWidget(self.btn_confirm, stretch=2)
        
        self.btn_cancel = QPushButton("ОТМЕНА")
        self.btn_cancel.setObjectName("btn_cancel")
        self.btn_cancel.clicked.connect(self.reject)
        final_layout.addWidget(self.btn_cancel, stretch=1)
        main_layout.addLayout(final_layout)
        
    def on_cell_clicked(self, selected_key):
        for key, btn in self.cell_buttons.items():
            if key != selected_key:
                btn.setChecked(False)
            else:
                btn.setChecked(True)
        self.lbl_status.setText(f"Выбрана ячейка для назначения: {selected_key.upper()}")

    def get_selected_cell_key(self):
        for key, btn in self.cell_buttons.items():
            if btn.isChecked():
                return key
        return None

    def refresh_library_list(self):
        self.list_library.clear()
        sorted_names = sorted(self._global_asset_library.keys(), key=natural_sort_key)
        
        for name in sorted_names:
            item = QListWidgetItem(f"📄 {name}")
            item.setData(Qt.ItemDataRole.UserRole, name)
            item.setToolTip(self._global_asset_library[name])
            self.list_library.addItem(item)
            
        self.btn_auto.setEnabled(len(self._global_asset_library) > 0)

    def refresh_assigned_list(self):
        all_slots = [
            "idle_close_1", "idle_close_2", "idle_close_3",
            "talk_close", "talk_open", "talk_blink",
            "shout_close", "shout_open", "shout_blink",
            "sleep_close_1", "sleep_close_2", "sleep_close_3"
        ]
        
        for slot in all_slots:
            btn = self.cell_buttons.get(slot)
            if not btn:
                continue
                
            path = self.assigned_map.get(slot, "")
            if path and os.path.exists(path):
                btn.setIcon(QIcon(path))
                btn.setText("") 
                btn.setProperty("has_file", True)
            else:
                btn.setIcon(QIcon())
                btn.setText("[ ]")
                btn.setProperty("has_file", False)
                
            btn.update()

    def import_individual_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Добавить кадры в библиотеку", "", "Изображения (*.png)")
        if files:
            for path in files:
                name = os.path.basename(path)
                self._global_asset_library[name] = path
            self.refresh_library_list()
            self.lbl_status.setText(f"Успешно добавлено файлов: {len(files)}")

    def import_entire_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выбрать папку с кадрами", "")
        if folder_path:
            count = 0
            for filename in os.listdir(folder_path):
                if filename.lower().endswith('.png'):
                    full_path = os.path.join(folder_path, filename)
                    self._global_asset_library[filename] = full_path
                    count += 1
            self.refresh_library_list()
            self.lbl_status.setText(f"Из папки импортировано {count} ассетов.")

    def delete_selected_assets(self):
        selected = self.list_library.selectedItems()
        if not selected:
            return
        
        for item in selected:
            name = item.data(Qt.ItemDataRole.UserRole)
            if name in self._global_asset_library:
                path_to_remove = self._global_asset_library[name]
                del self._global_asset_library[name]
                
                for slot, path in list(self.assigned_map.items()):
                    if path == path_to_remove:
                        del self.assigned_map[slot]
                        
        self.refresh_library_list()
        self.refresh_assigned_list()
        self.lbl_status.setText("Ассеты удалены из базы данных менеджера.")

    def assign_current_selection(self):
        lib_item = self.list_library.currentItem()
        slot_key = self.get_selected_cell_key()
        
        if not lib_item:
            self.lbl_status.setText("⚠ Ошибка: Выделите файл в библиотеке слева!")
            return
        if not slot_key:
            self.lbl_status.setText("⚠ Ошибка: Выберите целевую ячейку в сетке справа!")
            return
            
        filename = lib_item.data(Qt.ItemDataRole.UserRole)
        full_path = self._global_asset_library.get(filename)
        
        if full_path:
            self.assigned_map[slot_key] = full_path
            self.refresh_assigned_list()
            self.lbl_status.setText(f"Кадр {filename} добавлен в ячейку {slot_key.upper()}")

    def shortcut_assign_to_next(self, item):
        """Быстрое назначение по двойному клику слева в первую свободную ячейку"""
        filename = item.data(Qt.ItemDataRole.UserRole)
        full_path = self._global_asset_library.get(filename)
        
        all_slots = [
            "idle_close_1", "idle_close_2", "idle_close_3",
            "talk_close", "talk_open", "talk_blink",
            "shout_close", "shout_open", "shout_blink",
            "sleep_close_1", "sleep_close_2", "sleep_close_3"
        ]
        
        for slot in all_slots:
            if slot not in self.assigned_map or not self.assigned_map[slot]:
                self.assigned_map[slot] = full_path
                self.refresh_assigned_list()
                self.lbl_status.setText(f"Авто-подстановка: {filename} ➡ {slot.upper()}")
                return
                
        QMessageBox.information(self, "Менеджер", "Все 12 базовых ячеек таймлайна уже заполнены!")

    def auto_assign_all_library(self):
        """Метод автоматического распределения всех импортированных файлов по порядку ячеек"""
        self.assigned_map.clear()
        sorted_filenames = sorted(self._global_asset_library.keys(), key=natural_sort_key)
        
        all_slots = [
            "idle_close_1", "idle_close_2", "idle_close_3",
            "talk_close", "talk_open", "talk_blink",
            "shout_close", "shout_open", "shout_blink",
            "sleep_close_1", "sleep_close_2", "sleep_close_3"
        ]
        
        for idx, slot in enumerate(all_slots):
            if idx < len(sorted_filenames):
                name = sorted_filenames[idx]
                self.assigned_map[slot] = self._global_asset_library[name]
                
        self.refresh_assigned_list()
        self.lbl_status.setText("Сетка перераспределена по алфавитному порядку файлов.")

    def clear_current_map(self):
        self.assigned_map.clear()
        self.refresh_assigned_list()
        self.lbl_status.setText("Карта анимаций очищена. Файлы сохранены в менеджере.")

    def commit_to_timeline(self):
        if not self.assigned_map:
            if QMessageBox.question(self, "Внимание", "Вы отправляете пустую карту. Сбросить все кадры?", 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No:
                return
        
        self.files_loaded.emit(self.assigned_map)
        self.accept()
