import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTreeView, QListView, 
                             QFileSystemModel, QSplitter, QToolBar, QAction, 
                             QMenu, QProgressBar, QVBoxLayout, QWidget, 
                             QHBoxLayout, QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import QDir, Qt, QModelIndex, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem

BASE_PATH = os.path.expanduser("~/Alexandria")

class FileWorker(QThread):
    progress_updated = pyqtSignal(int)
    search_complete = pyqtSignal(list)
    directory_files_found = pyqtSignal(list)

    def __init__(self, root_dir, search_text=None, list_all=False):
        super().__init__()
        self.root_dir = root_dir
        self.search_text = search_text.lower() if search_text else None
        self.list_all = list_all
        self.canceled = False

    def run(self):
        if self.list_all:
            self.list_all_files()
        elif self.search_text:
            self.search_files()

    def list_all_files(self):
        all_files = []
        total_files = 0
        processed_files = 0

        # Primeiro contamos o total de arquivos para a barra de progresso
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if not file.endswith('.bib'):
                    total_files += 1

        if total_files == 0:
            self.directory_files_found.emit([])
            return

        # Agora coletamos todos os arquivos
        for root, _, files in os.walk(self.root_dir):
            if self.canceled:
                break

            for file in files:
                if self.canceled:
                    break

                if file.endswith('.bib'):
                    continue

                file_path = os.path.join(root, file)
                all_files.append(file_path)

                processed_files += 1
                progress = int((processed_files / total_files) * 100)
                self.progress_updated.emit(progress)

        self.directory_files_found.emit(all_files)

    def search_files(self):
        matching_files = []
        total_files = 0
        processed_files = 0

        # Contagem total de arquivos para progresso
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if not file.endswith('.bib'):
                    total_files += 1

        if total_files == 0:
            self.search_complete.emit([])
            return

        # Busca real
        for root, _, files in os.walk(self.root_dir):
            if self.canceled:
                break

            for file in files:
                if self.canceled:
                    break

                if file.endswith('.bib'):
                    continue

                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, self.root_dir)

                if self.search_text in file.lower():
                    matching_files.append(file_path)
                else:
                    bib_file = file_path + '.bib'
                    if os.path.exists(bib_file):
                        try:
                            with open(bib_file, 'r', encoding='utf-8') as f:
                                content = f.read().lower()
                                if self.search_text in content:
                                    matching_files.append(file_path)
                        except:
                            pass

                processed_files += 1
                progress = int((processed_files / total_files) * 100)
                self.progress_updated.emit(progress)

        self.search_complete.emit(matching_files)

    def cancel(self):
        self.canceled = True

class Alexandria(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alexandria")
        self.setGeometry(100, 100, 800, 600)
        self.current_file_model = None

        # Configuração dos modelos
        self.dir_model = QFileSystemModel()
        self.dir_model.setRootPath(BASE_PATH)
        self.dir_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)

        # Modelo para arquivos do diretório atual (não recursivo)
        self.file_model = QFileSystemModel()
        self.file_model.setFilter(QDir.Files | QDir.NoDotAndDotDot)
        self.file_model.setNameFilters(["*.pdf", "*.txt", "*.md", "*.png", "*.djvu"])
        self.file_model.setNameFilterDisables(False)

        # Modelo para todos os arquivos (recursivo)
        self.all_files_model = QStandardItemModel()

        # Configuração da interface
        self.init_ui()
        self.create_actions()
        self.create_toolbar()
        self.create_statusbar()

    def init_ui(self):
        # Widgets principais
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.dir_model)
        self.tree_view.setRootIndex(self.dir_model.index(BASE_PATH))
        self.tree_view.setHeaderHidden(True)
        self.tree_view.hideColumn(1)
        self.tree_view.hideColumn(2)
        self.tree_view.hideColumn(3)
        self.tree_view.setSelectionMode(QTreeView.SingleSelection)
        self.tree_view.selectionModel().selectionChanged.connect(self.on_tree_selection_changed)

        self.list_view = QListView()
        self.list_view.setModel(self.all_files_model)  # Começa com o modelo vazio
        self.list_view.doubleClicked.connect(self.open_file)
        self.list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self.show_context_menu)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.tree_view)
        splitter.addWidget(self.list_view)
        splitter.setSizes([200, 600])

        # Filtro de busca
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Buscar em nomes e arquivos .bib...")
        search_button = QPushButton("Buscar")
        search_button.clicked.connect(self.start_search)
        clear_button = QPushButton("Limpar")
        clear_button.clicked.connect(self.clear_search)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_box)
        search_layout.addWidget(search_button)
        search_layout.addWidget(clear_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.progress_bar)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def create_actions(self):
        self.add_file_action = QAction(QIcon.fromTheme('document-new'), "Adicionar Arquivo", self)
        self.add_file_action.triggered.connect(self.add_file)

        self.refresh_action = QAction(QIcon.fromTheme('view-refresh'), "Atualizar", self)
        self.refresh_action.triggered.connect(self.refresh)

    def create_toolbar(self):
        toolbar = QToolBar("Barra de Ferramentas")
        self.addToolBar(toolbar)
        toolbar.addAction(self.add_file_action)
        toolbar.addAction(self.refresh_action)

    def create_statusbar(self):
        self.statusBar().showMessage("Pronto")

    def on_tree_selection_changed(self):
        selected = self.tree_view.selectedIndexes()
        if selected:
            index = selected[0]
            path = self.dir_model.filePath(index)
            self.load_all_files_from_directory(path)

    def load_all_files_from_directory(self, directory):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.worker = FileWorker(directory, list_all=True)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.directory_files_found.connect(self.display_directory_files)
        self.worker.start()

    def display_directory_files(self, file_list):
        self.progress_bar.setVisible(False)
        
        self.all_files_model.clear()
        self.all_files_model.setHorizontalHeaderLabels(["Arquivos"])
        
        for file_path in file_list:
            item = QStandardItem(file_path)
            self.all_files_model.appendRow(item)
        
        self.list_view.setModel(self.all_files_model)
        self.statusBar().showMessage(f"{len(file_list)} arquivos encontrados")

    def add_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "Salvar Arquivo", BASE_PATH)
        if file_path:
            try:
                open(file_path, 'a').close()
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Não foi possível criar o arquivo: {str(e)}")

    def refresh(self):
        self.dir_model.setRootPath("")  # Força atualização
        self.dir_model.setRootPath(BASE_PATH)
        self.tree_view.setRootIndex(self.dir_model.index(BASE_PATH))
        self.on_tree_selection_changed()

    def open_file(self, index):
        if self.list_view.model() == self.all_files_model:
            file_path = self.all_files_model.data(index)
        else:
            file_path = self.file_model.filePath(index)
            
        if os.path.exists(file_path):
            if os.name == 'nt':
                os.startfile(file_path)
            else:
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.call([opener, file_path])

    def show_context_menu(self, pos):
        index = self.list_view.indexAt(pos)
        if not index.isValid():
            return

        if self.list_view.model() == self.all_files_model:
            file_path = self.all_files_model.data(index)
        else:
            file_path = self.file_model.filePath(index)

        menu = QMenu()

        open_folder_action = QAction("Abrir Pasta", self)
        open_folder_action.triggered.connect(lambda: self.open_folder(file_path))
        menu.addAction(open_folder_action)

        bib_file = file_path + '.bib'
        if os.path.exists(bib_file):
            open_bib_action = QAction("Abrir Arquivo .bib", self)
            open_bib_action.triggered.connect(lambda: self.open_file(bib_file))
            menu.addAction(open_bib_action)

        menu.exec_(self.list_view.viewport().mapToGlobal(pos))

    def open_folder(self, file_path):
        folder_path = os.path.dirname(file_path)
        if os.path.exists(folder_path):
            if os.name == 'nt':
                os.startfile(folder_path)
            else:
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.call([opener, folder_path])

    def start_search(self):
        search_text = self.search_box.text().strip()
        if not search_text:
            return

        selected = self.tree_view.selectedIndexes()
        if not selected:
            search_root = BASE_PATH
        else:
            search_root = self.dir_model.filePath(selected[0])

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker = FileWorker(search_root, search_text)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.search_complete.connect(self.display_search_results)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def display_search_results(self, file_list):
        self.progress_bar.setVisible(False)
        
        self.all_files_model.clear()
        self.all_files_model.setHorizontalHeaderLabels(["Resultados da Busca"])
        
        for file_path in file_list:
            item = QStandardItem(file_path)
            self.all_files_model.appendRow(item)
        
        self.list_view.setModel(self.all_files_model)
        self.statusBar().showMessage(f"{len(file_list)} resultados encontrados")

    def clear_search(self):
        self.search_box.clear()
        self.progress_bar.setVisible(False)
        self.on_tree_selection_changed()

    def closeEvent(self, event):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
        event.accept()

if __name__ == "__main__":
    import sys
    
    if not os.path.exists(BASE_PATH):
        os.makedirs(BASE_PATH)
    
    app = QApplication(sys.argv)
    window = Alexandria()
    window.show()
    sys.exit(app.exec_())
