import os 
import json
from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtGui import QIcon

from .files   import open_folder_from_path
from .files   import open_file_from_path
from .files   import read_file_from_path
from .message import show_message
from .pdfs    import is_pdf
from .pdfs    import get_metadata_pdf

def get_title_from_path(file_path):
    basename = os.path.basename(file_path)  # "documento.txt"
    title = os.path.splitext(basename)[0]  # Remove a extensão
    
    if is_pdf(file_path):
        metadata=get_metadata_pdf(file_path)
        if metadata.get('/Title','')!='':
            title = metadata.get('/Title','')

    
    show_message(   title, 
                    width=600, 
                    height=300, 
                    read_only=False, 
                    title="Title")

def get_metadata_from_path(file_path):
    metadata=get_metadata_pdf(file_path)
    metadata_str = json.dumps(metadata, indent=4, ensure_ascii=False)
        
    show_message(   metadata_str, 
                    width=600, 
                    height=300, 
                    read_only=False, 
                    title="Metadata")

def save_bib_file(  parent,
                    bib_path,
                    default_str, 
                    width=600, 
                    height=300, 
                    read_only=False, 
                    title="Bib file"):
    res = show_message( default_str, 
                        width=600, 
                        height=300, 
                        read_only=False, 
                        ok_label='Save',
                        title="Bib file",
                        show_close_button=True)
    if res!='':
        with open(bib_path, 'w', encoding='utf-8') as arquivo:
            arquivo.write(res)
            parent.refresh()

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
    open_folder_action.setIcon(QIcon.fromTheme("folder-open"))
    open_folder_action.triggered.connect(lambda: open_folder_from_path(file_path))
    menu.addAction(open_folder_action)
    
    get_title_action = QAction("Get title", parent)
    get_title_action.setIcon(QIcon.fromTheme("text-x-generic-template"))
    get_title_action.triggered.connect(lambda: get_title_from_path(file_path))
    menu.addAction(get_title_action)
    
    if is_pdf(file_path):
        get_metadata_action = QAction("Get PDF metadata", parent)
        get_metadata_action.setIcon(QIcon.fromTheme("application-pdf"))
        get_metadata_action.triggered.connect(lambda: get_metadata_from_path(file_path))
        menu.addAction(get_metadata_action)
    
    
    bib_file = file_path + '.bib'
    if os.path.exists(bib_file) and os.path.exists(file_path):
        bib_str = read_file_from_path(bib_file)
        open_bib_action = QAction("Open bib file", parent)
        open_bib_action.setIcon(QIcon.fromTheme("text-x-generic"))
        open_bib_action.triggered.connect(lambda: show_message( bib_str, 
                                                                width=600, 
                                                                height=300, 
                                                                read_only=False, 
                                                                title="Bib file"))
        menu.addAction(open_bib_action)
    else:
        create_bib_action = QAction("Create bib file", parent)
        create_bib_action.setIcon(QIcon.fromTheme("text-x-generic"))
        create_bib_action.triggered.connect(lambda: save_bib_file(  parent,
                                                                    bib_file,
                                                                    "", 
                                                                    width=600, 
                                                                    height=300, 
                                                                    read_only=False, 
                                                                    title="Bib file"))
        menu.addAction(create_bib_action)

    menu.exec_(parent.table_view.viewport().mapToGlobal(pos))
