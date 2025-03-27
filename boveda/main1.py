import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTreeView, QListView, QPushButton, QLabel, QLineEdit,
                             QProgressBar, QFileSystemModel, QSplitter, QMessageBox)
from PyQt5.QtCore import QDir, Qt, QModelIndex, QThread, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import subprocess
import re

BASE_PATH = os.path.expanduser("~/Alexandria")

class FileWorker(QThread):
    progress_updated = pyqtSignal(int)
    search_complete = pyqtSignal(list)
    
    def __init__(self, root_dir, search_term):
        super().__init__()
        self.root_dir = root_dir
        self.search_term = search_term.lower()
        self.canceled = False
        
    def run(self):
        matching_files = []
        bib_files = []
        
        # Primeiro coletamos todos os arquivos .bib
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith('.bib'):
                    bib_files.append(os.path.join(root, file))
        
        total = len(bib_files)
        for i, bib_file in enumerate(bib_files):
            if self.canceled:
                return
                
            self.progress_updated.emit(int((i / total) * 100))
            
            try:
                with open(bib_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    if self.search_term in content:
                        original_file = bib_file[:-4]  # Remove o .bib
                        if os.path.exists(original_file):
                            matching_files.append(original_file)
            except:
                continue
        
        self.search_complete.emit(matching_files)
        self.progress_updated.emit(100)
    
    def cancel(self):
        self.canceled = True

class Alexandria(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alexandria")
        self.resize(1000, 700)
        
        # Verifica e cria o diretório base se não existir
        if not os.path.exists(BASE_PATH):
            os.makedirs(BASE_PATH)
        
        self.init_ui()
        self.file_worker = None
        
    def init_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Barra de tarefas superior
        toolbar = QHBoxLayout()
        self.add_file_btn = QPushButton("Adicionar Arquivo")
        self.add_file_btn.clicked.connect(self.add_file)
        toolbar.addWidget(self.add_file_btn)
        main_layout.addLayout(toolbar)
        
        # Divisor principal (árvore à esquerda, lista à direita)
        splitter = QSplitter(Qt.Horizontal)
        
        # Tree view (esquerda)
        self.tree_model = QFileSystemModel()
        self.tree_model.setRootPath(BASE_PATH)
        self.tree_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setRootIndex(self.tree_model.index(BASE_PATH))
        self.tree_view.hideColumn(1)  # Esconde coluna de tamanho
        self.tree_view.hideColumn(2)  # Esconde coluna de tipo
        self.tree_view.hideColumn(3)  # Esconde coluna de data
        self.tree_view.setHeaderHidden(True)
        self.tree_view.clicked.connect(self.update_file_list)
        splitter.addWidget(self.tree_view)
        
        # List view (direita)
        self.list_model = QStandardItemModel()
        self.list_view = QListView()
        self.list_view.setModel(self.list_model)
        self.list_view.doubleClicked.connect(self.open_file)
        splitter.addWidget(self.list_view)
        
        splitter.setSizes([300, 700])
        main_layout.addWidget(splitter)
        
        # Filtro (parte inferior)
        filter_layout = QVBoxLayout()
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        filter_layout.addWidget(self.progress_bar)
        
        # Controles de filtro
        filter_controls = QHBoxLayout()
        filter_controls.addWidget(QLabel("Filtrar:"))
        
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Digite termos para buscar nos arquivos .bib")
        filter_controls.addWidget(self.filter_input)
        
        self.search_btn = QPushButton("Buscar")
        self.search_btn.clicked.connect(self.start_search)
        filter_controls.addWidget(self.search_btn)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.cancel_search)
        self.cancel_btn.setVisible(False)
        filter_controls.addWidget(self.cancel_btn)
        
        filter_layout.addLayout(filter_controls)
        main_layout.addLayout(filter_layout)
        
        # Atualiza a lista de arquivos inicialmente
        self.update_file_list(self.tree_model.index(BASE_PATH))
    
    def add_file(self):
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo", "", 
                                                  "Todos os arquivos (*.*);;PDF (*.pdf);;Texto (*.txt)")
        if file_path:
            dest_dir = BASE_PATH
            selected_index = self.tree_view.currentIndex()
            if selected_index.isValid():
                dest_dir = self.tree_model.filePath(selected_index)
            
            dest_path = os.path.join(dest_dir, os.path.basename(file_path))
            
            # Verifica se o arquivo já existe
            if os.path.exists(dest_path):
                reply = QMessageBox.question(self, 'Arquivo Existente', 
                                           'O arquivo já existe. Deseja substituir?',
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            
            try:
                # Copia o arquivo
                import shutil
                shutil.copy2(file_path, dest_path)
                
                # Atualiza a visualização
                self.update_file_list(selected_index if selected_index.isValid() else self.tree_model.index(BASE_PATH))
                
                QMessageBox.information(self, "Sucesso", "Arquivo adicionado com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao adicionar arquivo: {str(e)}")
    
    def update_file_list(self, index):
        """Atualiza a lista de arquivos com base no diretório selecionado na árvore"""
        path = self.tree_model.filePath(index)
        self.list_model.clear()
        
        # Coleta todos os arquivos (exceto .bib) no diretório e subdiretórios
        for root, _, files in os.walk(path):
            for file in files:
                if not file.endswith('.bib'):
                    item = QStandardItem(os.path.join(root, file).replace(BASE_PATH, '').lstrip(os.sep))
                    item.setData(os.path.join(root, file), Qt.UserRole + 1)  # Armazena o caminho completo
                    self.list_model.appendRow(item)
    
    def open_file(self, index):
        """Abre o arquivo com o programa padrão"""
        file_path = index.data(Qt.UserRole + 1)
        if os.path.exists(file_path):
            try:
                if sys.platform == 'win32':
                    os.startfile(file_path)
                elif sys.platform == 'darwin':
                    subprocess.run(['open', file_path])
                else:
                    subprocess.run(['xdg-open', file_path])
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível abrir o arquivo: {str(e)}")
    
    def start_search(self):
        """Inicia a busca nos arquivos .bib"""
        search_term = self.filter_input.text().strip()
        if not search_term:
            QMessageBox.warning(self, "Aviso", "Digite um termo para buscar")
            return
        
        selected_index = self.tree_view.currentIndex()
        if not selected_index.isValid():
            search_root = BASE_PATH
        else:
            search_root = self.tree_model.filePath(selected_index)
        
        # Configura a interface para busca
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.search_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        
        # Cria e inicia o worker
        if self.file_worker:
            self.file_worker.cancel()
            
        self.file_worker = FileWorker(search_root, search_term)
        self.file_worker.progress_updated.connect(self.progress_bar.setValue)
        self.file_worker.search_complete.connect(self.display_search_results)
        self.file_worker.start()
    
    def cancel_search(self):
        """Cancela a busca em andamento"""
        if self.file_worker:
            self.file_worker.cancel()
        self.search_finished()
    
    def display_search_results(self, files):
        """Exibe os resultados da busca"""
        self.list_model.clear()
        for file in files:
            item = QStandardItem(file.replace(BASE_PATH, '').lstrip(os.sep))
            item.setData(file, Qt.UserRole + 1)
            self.list_model.appendRow(item)
        
        self.search_finished()
    
    def search_finished(self):
        """Finaliza a operação de busca"""
        self.progress_bar.setVisible(False)
        self.search_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        self.file_worker = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Alexandria()
    window.show()
    sys.exit(app.exec_())
