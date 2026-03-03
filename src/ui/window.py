import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTreeWidget, QTreeWidgetItem, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QPushButton, 
                             QFileDialog, QLabel)
from PyQt6.QtCore import Qt

# Импорт наших бэкендов
from src.backend.live import LiveRegistry
from src.backend.offline import MultiHiveRegistry

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registry Reader")
        self.resize(1200, 700)
        
        # Текущий активный источник данных (интерфейс)
        self.registry_source = None 

        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Верхняя панель (Toolbar) ---
        top_bar = QHBoxLayout()
        
        self.btn_live = QPushButton("Подключиться к Live реестру")
        self.btn_live.clicked.connect(self.load_live_registry)
        
        self.btn_file = QPushButton("Открыть файл куста (Hive)")
        self.btn_file.clicked.connect(self.load_offline_registry)
        
        self.status_label = QLabel("Режим: Ожидание")
        self.status_label.setStyleSheet("color: gray; font-weight: bold;")

        top_bar.addWidget(self.btn_live)
        top_bar.addWidget(self.btn_file)
        top_bar.addStretch()
        top_bar.addWidget(self.status_label)
        
        main_layout.addLayout(top_bar)

        # --- Основная рабочая область (Splitter) ---
        content_layout = QHBoxLayout()
        
        # Левая часть: Дерево ключей
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Ключи реестра")
        self.tree.setColumnCount(1)
        self.tree.itemExpanded.connect(self.on_item_expanded)
        self.tree.itemClicked.connect(self.on_item_clicked)
        
        # Правая часть: Таблица значений
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Имя", "Тип", "Значение"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        # Настройка пропорций (1/3 дерево, 2/3 таблица)
        content_layout.addWidget(self.tree, 1)
        content_layout.addWidget(self.table, 2)
        
        main_layout.addLayout(content_layout)

    def load_live_registry(self):
        """Загрузка живого реестра"""
        self.registry_source = LiveRegistry()
        self.status_label.setText("Режим: LIVE (Локальная машина)")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.refresh_tree()

    # В начале файла добавь импорт нового класса:
    # from src.backend.offline import OfflineRegistry, MultiHiveRegistry

    def load_offline_registry(self):
        """Загрузка нескольких файлов кустов"""
        # Диалог выбора НЕСКОЛЬКИХ файлов
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, 
            "Выберите файлы кустов реестра", 
            "", 
            "All Files (*)" # Убрал фильтр по расширениям, чтобы видеть все файлы
        )
        
        if file_paths:
            try:
                # Создаем обертку для всех выбранных файлов
                self.registry_source = MultiHiveRegistry(file_paths)
                
                # Красиво выводим имена файлов в статус (только имена, без пути C:\...)
                file_names = [os.path.basename(p) for p in file_paths]
                names_str = ", ".join(file_names)
                
                self.status_label.setText(f"Загружено файлов: {len(file_paths)} ({names_str})")
                self.status_label.setStyleSheet("color: blue; font-weight: bold;")
                
                self.refresh_tree()
            except Exception as e:
                self.status_label.setText(f"Ошибка загрузки: {e}")
                self.status_label.setStyleSheet("color: red;")

    def refresh_tree(self):
        """Заполняет корневые элементы дерева"""
        self.tree.clear()
        self.table.setRowCount(0)
        
        if not self.registry_source:
            return

        roots = self.registry_source.get_root_keys()
        for root_name in roots:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, root_name)
            item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
            # Храним полный путь в данных элемента
            item.setData(0, Qt.ItemDataRole.UserRole, root_name) 

    def on_item_expanded(self, item: QTreeWidgetItem):
        """Ленивая подгрузка: загружаем подпапки только при раскрытии"""
        if item.childCount() > 0:
            return # Уже загружено

        path = item.data(0, Qt.ItemDataRole.UserRole)
        subkeys = self.registry_source.get_subkeys(path)
        
        for subkey_name in subkeys:
            child = QTreeWidgetItem(item)
            child.setText(0, subkey_name)
            child.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
            # Новый путь = старый путь + \ + имя
            new_path = f"{path}\\{subkey_name}"
            child.setData(0, Qt.ItemDataRole.UserRole, new_path)

    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """При клике показываем значения справа"""
        path = item.data(0, Qt.ItemDataRole.UserRole)
        self.load_values(path)

    def load_values(self, path):
        self.table.setRowCount(0)
        if not self.registry_source:
            return

        values = self.registry_source.get_values(path)
        self.table.setRowCount(len(values))
        
        for row, (name, val_type, val_data) in enumerate(values):
            self.table.setItem(row, 0, QTableWidgetItem(str(name)))
            self.table.setItem(row, 1, QTableWidgetItem(str(val_type)))
            self.table.setItem(row, 2, QTableWidgetItem(str(val_data)))