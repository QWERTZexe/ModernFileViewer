import sys
import os
import markdown
import zipfile
import mimetypes
import shutil
import tempfile
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, QMessageBox, QTreeWidget, QTreeWidgetItem,
                             QPushButton, QFileDialog, QLabel, QTextEdit, QVBoxLayout, QToolBar, QScrollArea, QHBoxLayout)
from PyQt6.QtGui import QIcon, QPixmap, QFont, QImage, QAction, QMovie
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
import fitz  # PyMuPDF for PDF rendering
import py7zr
import subprocess
import tarfile

cwd=os.path.dirname(os.path.abspath(sys.argv[0]))
unrar_dll_path = fr"{cwd}\utils\UnRAR64.dll"
os.environ['UNRAR_LIB_PATH'] = unrar_dll_path

from unrar import rarfile
import patoolib
from JavaHighlighter import JavaHighlighter
from PythonHighlighter import PythonHighlighter
from KotlinHighlighter import KotlinHighlighter
from JSONViewer import JSONViewer
from PEViewer import PEViewer
from FileTypeChoiceDialog import FileTypeChoiceDialog

def is_archive(file_name):
    try:
        # Check for ZIP
        if zipfile.is_zipfile(file_name):
            return 'zip'
        
        # Check for RAR
        if rarfile.is_rarfile(file_name):
            return 'rar'
        
        # Check for 7z
        if py7zr.is_7zfile(file_name):
            return '7z'
        
        # Check for self-extracting ZIP
        with open(file_name, 'rb') as f:
            data = f.read(1024)
            if b'PK\x03\x04' in data:
                return 'zip'
        
        # Check for 7z signature (even in EXE files)
        with open(file_name, 'rb') as f:
            if f.read(6) == b'7z\xbc\xaf\x27\x1c':
                return '7z'
        
        # Add more checks for other archive formats here
        
    except Exception as e:
        print(f"Error checking archive type: {str(e)}")
    return None
def decompile_class_file(self, class_file_path):
    try:
        fernflower_jar = f"{cwd}/utils/fernflower.jar"
        temp_dir = tempfile.mkdtemp()
        command = [
            'java', '-cp', fernflower_jar,
            'org.jetbrains.java.decompiler.main.decompiler.ConsoleDecompiler',
            class_file_path,
            temp_dir
        ]
        subprocess.run(command, check=True)
        decompiled_file = os.path.join(temp_dir, os.path.basename(class_file_path).replace('.class', '.java'))
        if os.path.exists(decompiled_file):
            with open(decompiled_file, 'r', encoding='utf-8') as file:
                decompiled_code = file.read()
            return decompiled_code
    except Exception as e:
        QMessageBox.warning(self, "Error", f"Failed to decompile .class file: {str(e)}")    
    finally:
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir, ignore_errors=True)
    return None
class FileTypeButton(QPushButton):
    def __init__(self, icon_path, text):
        super().__init__()
        self.setFixedSize(100, 100)
        self.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 2px solid #dcdcdc;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel()
        icon_label.setPixmap(QIcon(icon_path).pixmap(60, 60))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        text_label = QLabel(text)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setFont(QFont('Consolas', 12))
        layout.addWidget(text_label)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.viewers = []  # List to keep references to FileViewer instances
        self.initUI()

    def initUI(self):
        self.setWindowTitle('File Viewer')
        self.setGeometry(100, 100, 400, 400)

        central_widget = QWidget()
        grid_layout = QGridLayout()

        file_types = [
            ("⭐AUTO⭐", "icons/auto.png", self.openAutoDetect),
            ("PNG", "icons/png.png", lambda: self.openFile("PNG Files (*.png)", "image/png", ["png"])),
            ("JPG", "icons/jpg.png", lambda: self.openFile("JPEG Files (*.jpg *.jpeg)", "image/jpeg",["jpg"])),
            ("JFIF", "icons/jfif.png", lambda: self.openFile("JFIF Files (*.jfif)", "image/jpeg",["jfif"])),
            ("GIF", "icons/gif.png", lambda: self.openFile("GIF Files (*.gif)", "image/gif",["gif"])),
            ("ICO", "icons/ico.png", lambda: self.openFile("ICO Files (*.ico)", "image/x-icon",["ico"])),
            ("TXT", "icons/txt.png", lambda: self.openFile("Text Files (*.txt)", "text/plain",["txt"])),
            ("MD", "icons/md.png", lambda: self.openFile("Markdown Files (*.md)", "None",["md"])),
            ("PY", "icons/py.png", lambda: self.openFile("Python Files (*.py)", "text/plain",["py"])),
            ("JAVA", "icons/java.png", lambda: self.openFile("Java Files (*.java)", "None",["java"])),
            ("KT", "icons/kt.png", lambda: self.openFile("Kotlin Files (*.kt)", "None",["kt"])),
            ("JSON", "icons/json.png", lambda: self.openFile("JSON Files (*.json)", "application/json",["json"])),
            ("CLASS", "icons/class.png", lambda: self.openFile("Class Files (*.class)", "None",["class"])),
            ("HTML", "icons/html.png", lambda: self.openFile("HTML Files (*.html)", "text/html",["html"])),
            ("HTM", "icons/htm.png", lambda: self.openFile("HTM Files (*.htm)", "text/html",["htm"])),
            ("PDF", "icons/pdf.png", lambda: self.openFile("PDF Files (*.pdf)", "application/pdf",["pdf"])),
            ("ZIP", "icons/zip.png", lambda: self.openFile("ZIP Files (*.zip)", "zip", ["zip"])),
            ("JAR", "icons/jar.png", lambda: self.openFile("JAR Files (*.jar)", "java-archive", ["jar"])),
            ("RAR", "icons/rar.png", lambda: self.openFile("RAR Files (*.rar)", "x-compressed", ["rar"])),
            ("7Z", "icons/7z.png", lambda: self.openFile("7Z Files (*.7z)", "x-compressed", ["7z"])),
            ("TAR", "icons/tar.png", lambda: self.openFile("TAR Files (*.tar)", "tar", ["tar"])),
            ("DLL", "icons/dll.png", lambda: self.openFile("DLL Files (*.dll)", "application/x-msdownload", ["dll"])),
            ("EXE", "icons/exe.png", lambda: self.openFile("EXE Files (*.exe)", "application/x-msdownload", ["exe"]))
        ]

        for i, (text, icon_path, func) in enumerate(file_types):
            button = FileTypeButton(icon_path, text)
            button.clicked.connect(func)
            grid_layout.addWidget(button, i // 4, i % 4)

        central_widget.setLayout(grid_layout)
        self.setCentralWidget(central_widget)

    def openAutoDetect(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)")
        if file_name:
            file_type, _ = mimetypes.guess_type(file_name)
            if file_type:
                self.openFileViewer(file_name, file_type)
            else:
                QMessageBox.warning(self, "File Type Error", "Unable to determine file type.")

    def openFile(self, file_filter, expected_mime_type, extension):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", file_filter)
        if file_name:
            file_type, _ = mimetypes.guess_type(file_name)
            print(expected_mime_type, extension)
            print(file_type, extension)
            if str(expected_mime_type) in str(file_type):
                a=0
                for ext in extension:
                    if file_name.endswith(f".{ext}"):
                        a=1
                if a==1:
                    self.openFileViewer(file_name, file_type)
                else:
                    QMessageBox.warning(self, "File Extension Error", f"The selected file has a valid mimetype but a different extension. Rename this file to one of these extensions: {', '.join(extension)}")
            else:
                suggested_editor = self.suggestEditor(file_type)
                QMessageBox.warning(self, "File Type Error", f"The selected file is not a valid {file_filter.split(' ')[0]} file.\nSuggested editor: {suggested_editor}")

    def suggestEditor(self, file_type):
        suggestions = {
            'image/png': 'PNG Viewer',
            'image/jpeg': 'JPG/JFIF Viewer',
            'text/plain': 'Text Editor',
            'text/html': 'HTML/HTM Viewer',
            'application/pdf': 'PDF Viewer'
        }
        return suggestions.get(file_type, 'Unknown Editor')

    def openFileViewer(self, file_name, file_type):
        viewer = FileViewer(file_name, file_type, self)
        viewer.show()
        self.viewers.append(viewer)  # Keep a reference to the viewer


class FileViewer(QMainWindow):
    def __init__(self, file_name, file_type, main_window=None):
        super().__init__()
        self.file_name = file_name
        self.file_type = str(file_type)
        self.zoom_level = 1.0
        self.main_window = main_window
        self.temp_files = []  # Store temporary file objects
        self.temp_viewers = []  # Store viewers for temporary files
        self.archive_handlers = {
            '.zip': self.handle_zip,
            '.jar': self.handle_zip,  # JAR files are essentially ZIP files
            '.rar': self.handle_rar,
            '.7z': self.handle_7z,
            '.tar': self.handle_tar
        }
        self.initUI()
    def openFileViewer(self, file_name, file_type):
        viewer = FileViewer(file_name, file_type, self.main_window)
        viewer.show()
        self.main_window.viewers.append(viewer)  # Keep a reference to the viewer
    def initUI(self):
        self.setWindowTitle(f'Viewing: {os.path.basename(self.file_name)}')
        self.setGeometry(200, 200, 800, 600)

        self.toolbar = QToolBar("Zoom")
        self.addToolBar(self.toolbar)

        self.zoom_in_action = QAction(QIcon('icons/zoom_in.png'), 'Zoom In', self)
        self.zoom_in_action.triggered.connect(self.zoomIn)
        self.toolbar.addAction(self.zoom_in_action)

        self.zoom_out_action = QAction(QIcon('icons/zoom_out.png'), 'Zoom Out', self)
        self.zoom_out_action.triggered.connect(self.zoomOut)
        self.toolbar.addAction(self.zoom_out_action)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.setCentralWidget(self.scroll_area)

        self.content_widget = QWidget()
        self.layout = QVBoxLayout(self.content_widget)
        self.scroll_area.setWidget(self.content_widget)

        file_extension = os.path.splitext(self.file_name)[1].lower()
        if self.file_type.startswith('image/'):
            if self.file_type == 'image/gif':
                self.displayGIF()
            else:
                self.displayImage()
        elif file_extension in ['.py', '.java', '.class', ".kt"]:    
            self.displayCodeWithHighlighting(file_extension)      
        elif self.file_type in ['text/plain', 'text/markdown']:
            self.displayText()
        elif self.file_type == 'text/html':
            self.displayHTML()
        elif file_extension in ['.dll', '.exe']:
            self.displayPE()
        elif file_extension == '.md':
            self.displayMarkdown()
        elif self.file_type == 'application/pdf':
            self.displayPDF()
        elif file_extension in ['.zip', '.jar', '.rar', '.7z', '.tar']:
            self.displayCompressedFile()
        elif file_extension == '.json':
            self.displayJSON()
        else:
            self.displayUnsupported()
    def displayJSON(self):
        try:
            with open(self.file_name, 'r', encoding='utf-8') as file:
                json_data = file.read()
            
            json_viewer = JSONViewer(json_data)
            self.setCentralWidget(json_viewer)
            
            # Add expand/collapse buttons
            toolbar = QToolBar()
            self.addToolBar(toolbar)
            
            expand_action = QAction("Expand All", self)
            expand_action.triggered.connect(json_viewer.expandAll)
            toolbar.addAction(expand_action)
            
            collapse_action = QAction("Collapse All", self)
            collapse_action.triggered.connect(json_viewer.collapseAll)
            toolbar.addAction(collapse_action)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load JSON file: {str(e)}")
    def displayPE(self):
        archive_type = is_archive(self.file_name)
        
        if archive_type:
            dialog = FileTypeChoiceDialog(self)
            choice = dialog.get_choice()
            
            if choice == "PE":
                try:
                    pe_viewer = PEViewer(self.file_name, self)
                    self.setCentralWidget(pe_viewer)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to load PE file: {str(e)}")
            else:
                self.displayCompressedFile(archive_type)
        else:
            try:
                pe_viewer = PEViewer(self.file_name, self)
                self.setCentralWidget(pe_viewer)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load file: {str(e)}")
    def displayCodeWithHighlighting(self, file_extension):
        if file_extension == '.class':
            content = decompile_class_file(self, self.file_name)
            if content is None:
                content = "Failed to decompile .class file"
            file_extension = '.java'  # Use Java highlighter for decompiled .class files
        else:
            try:
                with open(self.file_name, 'r', encoding='utf-8') as file:
                    content = file.read()
            except UnicodeDecodeError:
                # If UTF-8 fails, try with system default encoding
                with open(self.file_name, 'r') as file:
                    content = file.read()

        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(content)
        self.text_edit.setReadOnly(True)
        font = QFont("Consolas", 12)
        self.text_edit.setFont(font)

        if file_extension == '.py':
            self.highlighter = PythonHighlighter(self.text_edit.document())
        elif file_extension == '.java':
            self.highlighter = JavaHighlighter(self.text_edit.document())
        elif file_extension == '.kt':
            self.highlighter = KotlinHighlighter(self.text_edit.document())
        self.layout.addWidget(self.text_edit)

    def displayCompressedFile(self, archive_type = None):
        self.zip_widget = QWidget()
        layout = QVBoxLayout(self.zip_widget)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["File Name", "Size"])
        self.tree.setColumnWidth(0, 300)
        layout.addWidget(self.tree)

        button_layout = QHBoxLayout()
        
        view_button = QPushButton("View Selected")
        view_button.clicked.connect(self.viewSelected)
        button_layout.addWidget(view_button)

        extract_button = QPushButton("Extract Selected")
        extract_button.clicked.connect(self.extractSelected)
        button_layout.addWidget(extract_button)

        layout.addLayout(button_layout)

        self.layout.addWidget(self.zip_widget)

        ext = os.path.splitext(self.file_name)[1].lower()
        handler = getattr(self, f'handle_{archive_type}', None)
        if handler:
            handler()
        else:
            #QMessageBox.warning(self, "Error", f"Unsupported archive type: {archive_type}")
            handler = self.archive_handlers.get(ext, self.handle_generic)
            handler()

        self.tree.itemDoubleClicked.connect(self.viewFileFromArchive)

    def handle_zip(self):
        with zipfile.ZipFile(self.file_name, 'r') as zip_ref:
            root = {}
            for file_info in zip_ref.infolist():
                parts = file_info.filename.split('/')
                parent = root
                for part in parts[:-1]:
                    if part not in parent:
                        parent[part] = {}
                    parent = parent[part]
                if parts[-1]:
                    parent[parts[-1]] = {'__file_info__': {
                        'filename': file_info.filename,
                        'file_size': file_info.file_size,
                        'is_dir': file_info.is_dir()
                    }}
            self.addItems(self.tree.invisibleRootItem(), root)

    def displayDecompiledClass(self, decompiled_code):
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(decompiled_code)
        self.text_edit.setReadOnly(True)
        font = QFont("Consolas", 12)
        self.text_edit.setFont(font)
        self.layout.addWidget(self.text_edit)

    def handle_rar(self):
        try:
            with rarfile.RarFile(self.file_name, 'r') as rar_ref:
                root = {}
                for file_info in rar_ref.infolist():

                    parts = file_info.filename.split('/')
                    parent = root
                    for i, part in enumerate(parts):
                        if i == len(parts) - 1:  # Last part (file)
                            parent[part] = {'__file_info__': {
                                'filename': file_info.filename,
                                'file_size': file_info.file_size,
                                'is_dir': False
                            }}
                        else:  # Directory
                            if part not in parent:
                                parent[part] = {}
                            parent = parent[part]
                self.addItems(self.tree.invisibleRootItem(), root)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to read archive: {str(e)}")

    def extract_from_rar(self, file_info):
        try:
            temp_dir = tempfile.mkdtemp()
            with rarfile.RarFile(self.file_name, 'r') as rar_ref:
                rar_ref.extract(file_info['filename'], temp_dir)
            extracted_path = os.path.join(temp_dir, file_info['filename'])
            if os.path.exists(extracted_path):
                with open(extracted_path, 'rb') as file:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_info['filename'])[1])
                    temp_file.write(file.read())
                    temp_file.flush()
                    self.temp_files.append(temp_file)  # Keep the file object in memory
                shutil.rmtree(temp_dir)
                return temp_file
        except rarfile.Error as e:
            QMessageBox.warning(self, "Error", f"Failed to extract file from RAR archive: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Unexpected error while extracting file: {str(e)}")
        finally:
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)
        return None
    def handle_7z(self):
        with py7zr.SevenZipFile(self.file_name, 'r') as sz_ref:
            root = {}
            for file_info in sz_ref.list():
                parts = file_info.filename.split('/')
                parent = root
                for part in parts[:-1]:
                    if part not in parent:
                        parent[part] = {}
                    parent = parent[part]
                if parts[-1]:
                    parent[parts[-1]] = {'__file_info__': {
                        'filename': file_info.filename,
                        'file_size': file_info.uncompressed,
                        'is_dir': file_info.is_directory
                    }}
            self.addItems(self.tree.invisibleRootItem(), root)
    def handle_tar(self):
        with tarfile.open(self.file_name, 'r:*') as tar_ref:
            root = {}
            for file_info in tar_ref.getmembers():
                parts = file_info.name.split('/')
                parent = root
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:  # Last part
                        if file_info.isdir():
                            if part not in parent:
                                parent[part] = {}
                        else:
                            parent[part] = {'__file_info__': {
                                'filename': file_info.name,
                                'file_size': file_info.size,
                                'is_dir': False
                            }}
                    else:  # Directory
                        if part not in parent:
                            parent[part] = {}
                        parent = parent[part]
            self.addItems(self.tree.invisibleRootItem(), root)
    def handle_generic(self):
        try:
            file_list = patoolib.list_archive(self.file_name)
            root = {}
            for file_path in file_list:
                parts = file_path.split('/')
                parent = root
                for part in parts[:-1]:
                    if part not in parent:
                        parent[part] = {}
                    parent = parent[part]
                if parts[-1]:
                    parent[parts[-1]] = {'__file_info__': {'filename': file_path, 'file_size': 0}}

            self.addItems(self.tree.invisibleRootItem(), root)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to read archive: {str(e)}")

    def addItems(self, parent, elements):
        folders = []
        files = []

        for key, value in elements.items():
            if '__file_info__' in value:
                files.append((key, value))
            else:
                folders.append((key, value))

        folders.sort(key=lambda x: x[0].lower())
        files.sort(key=lambda x: x[0].lower())

        for key, value in folders + files:
            item = QTreeWidgetItem(parent)
            item.setText(0, key)
            if '__file_info__' in value:
                file_info = value['__file_info__']
                size_in_bytes = file_info['file_size']
                formatted_size = self.formatSize(size_in_bytes)
                item.setText(1, formatted_size if not file_info['is_dir'] else "")
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(0, Qt.CheckState.Unchecked)
                item.setData(0, Qt.ItemDataRole.UserRole, file_info)
                icon_path = f"icons/{'folder' if file_info['is_dir'] else os.path.splitext(key)[1][1:]}.png"
                if os.path.exists(icon_path):
                    item.setIcon(0, QIcon(icon_path))
            else:
                self.addItems(item, value)


    def viewSelected(self):
        selected_items = self.tree.selectedItems()
        for item in selected_items:
            self.viewFileFromArchive(item, 0)

    def viewFileFromArchive(self, item, column):
        file_info = item.data(0, Qt.ItemDataRole.UserRole)
        if file_info and not file_info['is_dir']:
            ext = os.path.splitext(self.file_name)[1].lower()
            temp_file = self.extractFileFromArchive(ext, file_info)
            if temp_file:
                viewer = FileViewer(temp_file.name, mimetypes.guess_type(file_info['filename'])[0], self.main_window)
                viewer.show()
                self.temp_viewers.append(viewer)  # Keep a reference to the viewer

    def extractFileFromArchive(self, ext, file_info):
        if ext == '.zip' or ext == '.jar':
            return self.extract_from_zip(file_info)
        elif ext == '.rar':
            return self.extract_from_rar(file_info)
        elif ext == '.7z':
            return self.extract_from_7z(file_info)
        elif ext == '.tar':
            return self.extract_from_tar(file_info)
        else:
            return self.extract_generic(file_info)
    def extract_from_zip(self, file_info):
        with zipfile.ZipFile(self.file_name, 'r') as zip_ref:
            with zip_ref.open(file_info['filename']) as file:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_info['filename'])[1])
                temp_file.write(file.read())
                temp_file.flush()
                self.temp_files.append(temp_file)  # Keep the file object in memory
        return temp_file

    def extract_from_rar(self, file_info):
        try:
            temp_dir = tempfile.mkdtemp()
            patoolib.extract_archive(self.file_name, outdir=temp_dir, interactive=False)
            extracted_path = os.path.join(temp_dir, file_info['filename'])
            if os.path.exists(extracted_path):
                with open(extracted_path, 'rb') as file:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_info['filename'])[1])
                    temp_file.write(file.read())
                    temp_file.flush()
                    self.temp_files.append(temp_file)  # Keep the file object in memory
                shutil.rmtree(temp_dir)
                return temp_file
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to extract file: {str(e)}")
        return None


    def extract_from_7z(self, file_info):
        with py7zr.SevenZipFile(self.file_name, 'r') as sz_ref:
            temp_dir = tempfile.mkdtemp()
            sz_ref.extract(temp_dir, [file_info["filename"]])
            extracted_path = os.path.join(temp_dir, file_info["filename"])
            with open(extracted_path, 'rb') as file:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_info["filename"])[1])
                temp_file.write(file.read())
                temp_file.flush()
                self.temp_files.append(temp_file)  # Keep the file object in memory
            shutil.rmtree(temp_dir)
        return temp_file

    def extract_from_tar(self, file_info):
        if file_info['is_dir']:
            return None  # Skip directories
        with tarfile.open(self.file_name, 'r:*') as tar_ref:
            member = tar_ref.getmember(file_info['filename'])
            with tar_ref.extractfile(member) as file:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_info['filename'])[1])
                temp_file.write(file.read())
                temp_file.flush()
                self.temp_files.append(temp_file)  # Keep the file object in memory
        return temp_file
    def extract_generic(self, file_info):
        try:
            temp_dir = tempfile.mkdtemp()
            
            # Try different extraction methods
            extraction_methods = [
                self.extract_with_patoolib,
                self.extract_with_rarfile,
                self.extract_with_zipfile,
                self.extract_with_7z
            ]
            
            extracted = False
            for method in extraction_methods:
                try:
                    method(temp_dir)
                    extracted = True
                    break  # If extraction succeeds, break the loop
                except Exception as e:
                    print(f"Extraction method {method.__name__} failed: {str(e)}")
                    continue  # If this method fails, try the next one
            
            if not extracted:
                raise Exception("Failed to extract with all available methods")

            extracted_path = os.path.join(temp_dir, file_info['filename'])
            if os.path.exists(extracted_path):
                with open(extracted_path, 'rb') as file:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_info['filename'])[1])
                    temp_file.write(file.read())
                    temp_file.flush()
                    self.temp_files.append(temp_file)  # Keep the file object in memory
                return temp_file
            else:
                raise FileNotFoundError(f"Extracted file not found: {extracted_path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to extract file: {str(e)}")
        finally:
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)
        return None

    def extract_with_patoolib(self, temp_dir):
        patoolib.extract_archive(self.file_name, outdir=temp_dir, interactive=False)

    def extract_with_7z(self, temp_dir):
        with py7zr.SevenZipFile(self.file_name, mode='r') as z:
            z.extractall(temp_dir)

    def extract_with_zipfile(self, temp_dir):
        with zipfile.ZipFile(self.file_name, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

    def extract_with_rarfile(self, temp_dir):
        with rarfile.RarFile(self.file_name, 'r') as rar_ref:
            rar_ref.extractall(temp_dir)

    def extractSelected(self):
        selected_dir = QFileDialog.getExistingDirectory(self, "Select Directory for Extraction")
        if selected_dir:
            try:
                # Try different extraction methods
                extraction_methods = [
                    self.extract_with_patoolib,
                    self.extract_with_7z,
                    self.extract_with_zipfile,
                    self.extract_with_rarfile
                ]
                
                extracted = False
                for method in extraction_methods:
                    try:
                        method(selected_dir)
                        extracted = True
                        break  # If extraction succeeds, break the loop
                    except Exception as e:
                        print(f"Extraction method {method.__name__} failed: {str(e)}")
                        continue  # If this method fails, try the next one
                
                if not extracted:
                    raise Exception("Failed to extract with all available methods")

                QMessageBox.information(self, "Extraction Complete", "Selected files have been extracted.")
            except Exception as e:
                QMessageBox.warning(self, "Extraction Error", f"Failed to extract files: {str(e)}")

    def formatSize(self, size_in_bytes):
        """Format the size in a human-readable format (B/KB/MB/GB/TB)."""
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_in_bytes)
        unit_index = 0
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1
        return f"{size:.2f} {units[unit_index]}"

    def displayGIF(self):
        self.gif_label = QLabel(self)
        self.movie = QMovie(self.file_name)
        self.gif_label.setMovie(self.movie)
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.gif_label)
        self.movie.start()
        
        # Disable zoom buttons for GIFs
        self.zoom_in_action.setEnabled(False)
        self.zoom_out_action.setEnabled(False)

    def displayImage(self):
        self.image_label = QLabel(self)
        self.pixmap = QPixmap(self.file_name)
        self.image_label.setPixmap(self.pixmap)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.image_label)

    def displayText(self):
        with open(self.file_name, 'r', encoding='utf-8') as file:
            content = file.read()
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(content)
        self.text_edit.setReadOnly(True)
        font = QFont("Consolas", 12)
        self.text_edit.setFont(font)
        self.layout.addWidget(self.text_edit)

    def displayHTML(self):
        self.web_view = QWebEngineView(self)
        self.web_view.load(QUrl.fromLocalFile(self.file_name))
        self.layout.addWidget(self.web_view)

    def displayMarkdown(self):
        with open(self.file_name, 'r', encoding='utf-8') as file:
            content = file.read()
        html_content = markdown.markdown(content)
        self.web_view = QWebEngineView(self)
        styled_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Consolas', monospace; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        self.web_view.setHtml(styled_html)
        self.layout.addWidget(self.web_view)

    def displayPDF(self):
        self.pdf_widget = QWidget()
        self.pdf_layout = QVBoxLayout(self.pdf_widget)
        self.layout.addWidget(self.pdf_widget)

        self.doc = fitz.open(self.file_name)
        self.pdf_labels = []
        for page in self.doc:
            pix = page.get_pixmap()
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
            label = QLabel()
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.pdf_layout.addWidget(label)
            self.pdf_labels.append(label)

    def displayUnsupported(self):
        label = QLabel("Unsupported file type", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont('Arial', 16))
        self.layout.addWidget(label)

    def zoomIn(self):
        self.zoom_level = min(self.zoom_level * 1.2, 5.0)  # Limit zoom in to 5x
        self.applyZoom()

    def zoomOut(self):
        self.zoom_level = max(self.zoom_level / 1.2, 0.1)  # Limit zoom out to 0.1x
        self.applyZoom()

    def applyZoom(self):
        if hasattr(self, 'image_label'):
            scaled_pixmap = self.pixmap.scaled(self.pixmap.size() * self.zoom_level, 
                                               Qt.AspectRatioMode.KeepAspectRatio, 
                                               Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        elif hasattr(self, 'text_edit'):
            font = self.text_edit.font()
            font.setPointSizeF(font.pointSizeF() * self.zoom_level)
            self.text_edit.setFont(font)
        elif hasattr(self, 'web_view'):
            self.web_view.setZoomFactor(self.zoom_level)
        elif hasattr(self, 'pdf_labels'):
            for i, label in enumerate(self.pdf_labels):
                page = self.doc[i]
                pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_level, self.zoom_level))
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(img)
                label.setPixmap(pixmap)

        self.content_widget.adjustSize()
if __name__ == '__main__':
    mimetypes.init()
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())