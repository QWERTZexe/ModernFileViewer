from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel

class FileTypeChoiceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose File Type")
        layout = QVBoxLayout(self)
        
        label = QLabel("This file appears to be both an executable and an archive. How would you like to view it?")
        layout.addWidget(label)
        
        self.pe_button = QPushButton("View as Executable (PE)")
        self.pe_button.clicked.connect(self.accept)
        layout.addWidget(self.pe_button)
        
        self.archive_button = QPushButton("View as Archive")
        self.archive_button.clicked.connect(self.reject)
        layout.addWidget(self.archive_button)

    def get_choice(self):
        result = self.exec()
        if result == QDialog.DialogCode.Accepted:
            return "PE"
        else:
            return "Archive"
