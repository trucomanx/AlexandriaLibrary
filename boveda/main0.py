import os
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTreeView, QListView, QPushButton, QFileDialog, QAbstractItemView,
                             QLabel, QMessageBox)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtCore import QDir, Qt, QFileInfo

BASE_PATH = os.path.expanduser("~/Alexandria")


class AlexandriaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alexandria")
        self.setGeometry(100, 100, 800, 600)
        
        # Verifica e cria o diretório base se não existir
        if not os.path.exists(BASE_PATH):
            os.makedirs(BASE_PATH)
        
        self.initUI()
        self.load_directory_structure()
    
    def initUI(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Barra de tarefas superior
        toolbar = QHBoxLayout()
        self.add_button = QPushButton("Adicionar Arquivo")
        self.add_button.setIcon(QIcon.fromTheme("document-open"))
        self.add_button.clicked.connect(self.add_file)
        toolbar.addWidget(self.add_button)
        
        # Espaço vazio para alinhar à esquerda
        toolbar.addStretch()
        
        main_layout.addLayout(toolbar)
        
        # Área principal (tree view + list view)
        content_layout = QHBoxLayout()
        
        # Tree View (esquerda)
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_model = QStandardItemModel()
        self.tree_view.setModel(self.tree_model)
        self.tree_view.selectionModel().selectionChanged.connect(self.on_tree_selection_changed)
        content_layout.addWidget(self.tree_view, 1)
        
        # List View (direita)
        self.list_view = QListView()
        self.list_model = QStandardItemModel()
        self.list_view.setModel(self.list_model)
        self.list_view.setViewMode(QListView.IconMode)
        self.list_view.setResizeMode(QListView.Adjust)
        self.list_view.setSelectionMode(QAbstractItemView.SingleSelection)
        content_layout.addWidget(self.list_view, 2)
        
        main_layout.addLayout(content_layout, 1)
    
    def load_directory_structure(self):
        self.tree_model.clear()
        root_item = self.tree_model.invisibleRootItem()
        self.add_tree_items(root_item, BASE_PATH)
        self.tree_view.expandAll()
    
    def add_tree_items(self, parent_item, path):
        dir_name = os.path.basename(path)
        dir_item = QStandardItem(dir_name)
        dir_item.setData(path, Qt.UserRole)
        dir_item.setEditable(False)
        parent_item.appendRow(dir_item)
        
        for item in sorted(os.listdir(path)):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                self.add_tree_items(dir_item, item_path)
    
    def on_tree_selection_changed(self, selected, deselected):
        indexes = selected.indexes()
        if indexes:
            index = indexes[0]
            path = index.data(Qt.UserRole)
            self.load_directory_contents(path)
    
    def load_directory_contents(self, path):
        self.list_model.clear()
        
        # Adiciona todos os arquivos do diretório e subdiretórios
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                file_info = QFileInfo(file_path)
                
                item = QStandardItem(file)
                item.setData(file_path, Qt.UserRole)
                item.setEditable(False)
                
                # Adiciona ícone baseado no tipo de arquivo
                if file.lower().endswith('.pdf'):
                    item.setIcon(QIcon.fromTheme("application-pdf"))
                elif file.lower().endswith(('.txt', '.md')):
                    item.setIcon(QIcon.fromTheme("text-plain"))
                elif file.lower().endswith(('.doc', '.docx')):
                    item.setIcon(QIcon.fromTheme("application-msword"))
                elif file.lower().endswith(('.xls', '.xlsx')):
                    item.setIcon(QIcon.fromTheme("application-vnd.ms-excel"))
                elif file.lower().endswith(('.ppt', '.pptx')):
                    item.setIcon(QIcon.fromTheme("application-vnd.ms-powerpoint"))
                else:
                    item.setIcon(QIcon.fromTheme("text-x-generic"))
                
                self.list_model.appendRow(item)
    
    def add_file(self):
        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(
            self, "Selecionar Arquivos", QDir.homePath(),
            "Documentos (*.pdf *.txt *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.md);;Todos os arquivos (*)"
        )
        
        if file_paths:
            dest_dir = BASE_PATH
            selected_indexes = self.tree_view.selectedIndexes()
            
            if selected_indexes:
                selected_path = selected_indexes[0].data(Qt.UserRole)
                if os.path.isdir(selected_path):
                    dest_dir = selected_path
            
            for file_path in file_paths:
                try:
                    file_name = os.path.basename(file_path)
                    dest_path = os.path.join(dest_dir, file_name)
                    
                    # Verifica se o arquivo já existe
                    if os.path.exists(dest_path):
                        reply = QMessageBox.question(
                            self, 'Arquivo Existente',
                            f'O arquivo "{file_name}" já existe. Deseja substituir?',
                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            continue
                    
                    shutil.copy2(file_path, dest_path)
                    
                except Exception as e:
                    QMessageBox.warning(self, "Erro", f"Não foi possível copiar o arquivo: {str(e)}")
            
            # Atualiza a visualização
            self.load_directory_structure()
            self.load_directory_contents(dest_dir)


if __name__ == "__main__":
    app = QApplication([])
    window = AlexandriaApp()
    window.show()
    app.exec_()
