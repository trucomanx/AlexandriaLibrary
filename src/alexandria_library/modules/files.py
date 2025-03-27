from PyQt5.QtWidgets import QFileDialog, QMessageBox
import shutil
import os
import subprocess
import sys


def open_folder_from_path(file_path):
    folder_path = os.path.dirname(file_path)
    if os.path.exists(folder_path):
        if os.name == 'nt':
            os.startfile(folder_path)
        else:
            opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
            subprocess.call([opener, folder_path])

def open_file_from_index(parent,index):
        if parent.list_view.model() == parent.all_files_model:
            file_path = parent.all_files_model.data(index)
        else:
            file_path = parent.file_model.filePath(index)
            
        if os.path.exists(file_path):
            if os.name == 'nt':
                os.startfile(file_path)
            else:
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.call([opener, file_path])

def save_file_in(parent,BASE_PATH,func_refresh):
    file_dialog = QFileDialog()
    file_path, _ = file_dialog.getOpenFileName(parent, "Salvar Arquivo")

    if file_path:
        try:
            dir_path = file_dialog.getExistingDirectory(parent, "Save in?",
                                   BASE_PATH,
                                   QFileDialog.ShowDirsOnly)
            shutil.copy2(file_path, dir_path)
            func_refresh()
            
        except Exception as e:
            QMessageBox.warning(parent, "Erro", f"Não foi possível criar o arquivo: {str(e)}")
