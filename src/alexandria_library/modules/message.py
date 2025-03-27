from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QScrollArea, QPushButton, QApplication

class MessageDialog(QDialog):
    """Display a message with copyable text and an OK button"""
    def __init__(self, message, width=600, height=300, parent=None, read_only=False, title="Message"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(width, height)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create text view for displaying the message
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(message)
        self.text_edit.setReadOnly(read_only)
        self.text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        
        # Add text view to a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.text_edit)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # Copy to clipboard Button
        copy_button = QPushButton("Copy to clipboard")
        copy_button.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(copy_button)
        
        # OK Button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

    def copy_to_clipboard(self):
        """Copy the text from the text edit to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())

def show_message(message, width=600, height=300, read_only=False, title="Message"):
    dialog = MessageDialog(message, width, height, read_only=read_only, title=title)
    dialog.exec_()
    res = dialog.text_edit.toPlainText()
    return res
