from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt
import json

class JSONViewer(QTreeWidget):
    def __init__(self, json_data):
        super().__init__()
        self.setHeaderLabels(["Key", "Value"])
        self.setAlternatingRowColors(True)
        self.setColumnWidth(0, 200)
        self.json_data = json_data
        self.populate_tree()

    def populate_tree(self):
        try:
            data = json.loads(self.json_data)
            self.add_json_item(self.invisibleRootItem(), "", data)
        except json.JSONDecodeError:
            error_item = QTreeWidgetItem(["Error", "Invalid JSON"])
            error_item.setForeground(1, QColor("red"))
            self.addTopLevelItem(error_item)

    def add_json_item(self, parent, key, value):
        item = QTreeWidgetItem(parent, [str(key)])
        self.format_item(item, value)
        
        if isinstance(value, dict):
            for k, v in value.items():
                self.add_json_item(item, k, v)
        elif isinstance(value, list):
            for i, v in enumerate(value):
                self.add_json_item(item, str(i), v)
        else:
            item.setText(1, str(value))

    def format_item(self, item, value):
        if isinstance(value, dict):
            item.setForeground(0, QColor("blue"))
            item.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon))
        elif isinstance(value, list):
            item.setForeground(0, QColor("magenta"))
            item.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
        elif isinstance(value, bool):
            item.setForeground(1, QColor("green"))
            item.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_MessageBoxQuestion))
        elif isinstance(value, (int, float)):
            item.setForeground(1, QColor("red"))
            item.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_DriveHDIcon))
        elif isinstance(value, str):
            item.setForeground(1, QColor("blue"))
            item.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogContentsView))
        elif value is None:
            item.setForeground(1, QColor("gray"))
            item.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_MessageBoxCritical))
            item.setText(1, "null")

        item.setFont(0, QFont("Consolas", 10))
        item.setFont(1, QFont("Consolas", 10))
