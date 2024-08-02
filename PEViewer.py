import pefile
import tempfile
import os
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QFileDialog, QMessageBox, QSplitter
from PyQt6.QtGui import QFont, QColor, QIcon
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

class PEViewer(QWidget):
    def __init__(self, file_name, main_viewer):
        super().__init__()
        self.file_name = file_name
        self.main_viewer = main_viewer
        self.temp_dir = tempfile.mkdtemp()
        self.resource_data = {}
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        # PE Structure Tree
        self.pe_tree = QTreeWidget()
        self.pe_tree.setHeaderLabels(["Field", "Value"])
        self.pe_tree.setAlternatingRowColors(True)
        self.pe_tree.setColumnWidth(0, 300)
        splitter.addWidget(self.pe_tree)

        # Resources Tree
        self.resources_tree = QTreeWidget()
        self.resources_tree.setHeaderLabels(["Resource", "Type", "Size"])
        self.resources_tree.setAlternatingRowColors(True)
        self.resources_tree.setColumnWidth(0, 200)
        self.resources_tree.setColumnWidth(1, 100)
        self.resources_tree.itemDoubleClicked.connect(self.view_resource)
        splitter.addWidget(self.resources_tree)

        button_layout = QHBoxLayout()
        extract_button = QPushButton("Extract All Resources")
        extract_button.clicked.connect(self.extract_all_resources)
        button_layout.addWidget(extract_button)

        layout.addLayout(button_layout)

        self.load_pe()

    def load_pe(self):
        try:
            pe = pefile.PE(self.file_name)

            # Load PE structure
            self.load_pe_structure(pe)

            # Load resources
            self.load_resources(pe)

        except pefile.PEFormatError as e:
            error_item = QTreeWidgetItem(["Error", f"Failed to parse PE file: {str(e)}"])
            error_item.setForeground(1, QColor("red"))
            self.pe_tree.addTopLevelItem(error_item)

    def load_pe_structure(self, pe):
        # Add DOS Header
        dos_header = QTreeWidgetItem(["DOS Header"])
        self.pe_tree.addTopLevelItem(dos_header)
        for field in pe.DOS_HEADER.dump():
            item = QTreeWidgetItem([field[0], str(field[1])])
            dos_header.addChild(item)

        # Add File Header
        file_header = QTreeWidgetItem(["File Header"])
        self.pe_tree.addTopLevelItem(file_header)
        for field in pe.FILE_HEADER.dump():
            item = QTreeWidgetItem([field[0], str(field[1])])
            file_header.addChild(item)

        # Add Optional Header
        optional_header = QTreeWidgetItem(["Optional Header"])
        self.pe_tree.addTopLevelItem(optional_header)
        for field in pe.OPTIONAL_HEADER.dump():
            item = QTreeWidgetItem([field[0], str(field[1])])
            optional_header.addChild(item)

        # Add Sections
        sections = QTreeWidgetItem(["Sections"])
        self.pe_tree.addTopLevelItem(sections)
        for section in pe.sections:
            section_item = QTreeWidgetItem([section.Name.decode().strip(), ""])
            sections.addChild(section_item)
            section_item.addChild(QTreeWidgetItem(["Virtual Address", hex(section.VirtualAddress)]))
            section_item.addChild(QTreeWidgetItem(["Virtual Size", hex(section.Misc_VirtualSize)]))
            section_item.addChild(QTreeWidgetItem(["Raw Data Size", hex(section.SizeOfRawData)]))
            section_item.addChild(QTreeWidgetItem(["Pointer to Raw Data", hex(section.PointerToRawData)]))
            section_item.addChild(QTreeWidgetItem(["Characteristics", hex(section.Characteristics)]))

        # Add Imports
        if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
            imports = QTreeWidgetItem(["Imports"])
            self.pe_tree.addTopLevelItem(imports)
            for entry in pe.DIRECTORY_ENTRY_IMPORT:
                dll_item = QTreeWidgetItem([entry.dll.decode(), ""])
                imports.addChild(dll_item)
                for imp in entry.imports:
                    imp_item = QTreeWidgetItem([str(imp.name), hex(imp.address)])
                    dll_item.addChild(imp_item)

        # Add Exports
        if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
            exports = QTreeWidgetItem(["Exports"])
            self.pe_tree.addTopLevelItem(exports)
            for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
                item = QTreeWidgetItem([str(exp.name), hex(exp.address)])
                exports.addChild(item)

    def load_resources(self, pe):
        if hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
            for resource_type in pe.DIRECTORY_ENTRY_RESOURCE.entries:
                if resource_type.name is not None:
                    resource_type_name = resource_type.name.decode()
                else:
                    resource_type_name = pefile.RESOURCE_TYPE.get(resource_type.struct.Id, f"Unknown ({resource_type.struct.Id})")
                
                type_item = QTreeWidgetItem([resource_type_name])
                self.resources_tree.addTopLevelItem(type_item)

                for resource_id in resource_type.directory.entries:
                    if resource_id.name is not None:
                        resource_name = resource_id.name.decode()
                    else:
                        resource_name = str(resource_id.struct.Id)

                    for resource_lang in resource_id.directory.entries:
                        data_rva = resource_lang.data.struct.OffsetToData
                        size = resource_lang.data.struct.Size
                        data = pe.get_data(data_rva, size)

                        file_name = self.get_resource_filename(resource_type_name, resource_name, resource_lang.struct.Id)
                        item = QTreeWidgetItem([file_name, resource_type_name, f"{size} bytes"])
                        type_item.addChild(item)

                        # Store resource data
                        self.resource_data[file_name] = data

    def get_resource_filename(self, type_name, resource_name, lang_id):
        extension = self.get_resource_extension(type_name)
        return f"{resource_name}_{lang_id}{extension}"

    def get_resource_extension(self, type_name):
        extensions = {
            "RT_ICON": ".ico",
            "RT_BITMAP": ".bmp",
            "RT_MANIFEST": ".mf",
            "RT_VERSION": ".version",
            "RT_STRING": ".txt",
            "RT_MESSAGETABLE": ".bin",
            "RT_GROUP_ICON": ".group_ico",
            "RT_GROUP_CURSOR": ".group_cur",
            "RT_CURSOR": ".cur",
        }
        return extensions.get(type_name, ".bin")

    def view_resource(self, item, column):
        file_name = item.text(0)
        if file_name in self.resource_data:
            data = self.resource_data[file_name]
            temp_file_path = os.path.join(self.temp_dir, file_name)
            with open(temp_file_path, 'wb') as f:
                f.write(data)
            self.main_viewer.openFileViewer(temp_file_path, self.get_mime_type(file_name))

    def get_mime_type(self, file_name):
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_name)
        return mime_type or "application/octet-stream"

    def extract_all_resources(self):
        if not self.resource_data:
            QMessageBox.information(self, "No Resources", "No resources found to extract.")
            return

        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory to Save Resources")
        if dir_path:
            for file_name, data in self.resource_data.items():
                file_path = os.path.join(dir_path, file_name)
                with open(file_path, 'wb') as f:
                    f.write(data)
            QMessageBox.information(self, "Resources Extracted", f"All resources have been extracted to {dir_path}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(dir_path))

    def __del__(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
