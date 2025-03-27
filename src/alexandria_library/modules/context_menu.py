import os 

from PyQt5.QtWidgets import QMenu, QAction

from .files   import open_folder_from_path
from .files   import open_file_from_path
from .files   import read_file_from_path
from .message import show_message

def show_context_menu_from_index(parent, base_path, pos):
    index = parent.table_view.indexAt(pos)
    if not index.isValid():
        return
        
    row   = index.row()
    model = parent.table_view.model()

    filename = model.item(row, 0).text()
    rel_dir  = model.item(row, 1).text()

    file_path = os.path.join(base_path,rel_dir,filename)
    
    menu = QMenu()

    open_folder_action = QAction("Open dir", parent)
    open_folder_action.triggered.connect(lambda: open_folder_from_path(file_path))
    menu.addAction(open_folder_action)
    
    bib_file = file_path + '.bib'
    if os.path.exists(bib_file) and os.path.exists(file_path):
        bib_str = read_file_from_path(bib_file)
        open_bib_action = QAction("Open file .bib", parent)
        open_bib_action.triggered.connect(lambda: show_message( bib_str, 
                                                                width=600, 
                                                                height=300, 
                                                                read_only=False, 
                                                                title="Bib file"))
        menu.addAction(open_bib_action)

    menu.exec_(parent.table_view.viewport().mapToGlobal(pos))
