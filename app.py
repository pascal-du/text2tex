import sys
import os
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QPushButton, QFileDialog, QMessageBox, 
                             QDialog, QLabel, QListWidget, QCheckBox, 
                             QTabWidget, QInputDialog, QComboBox)
from PyQt6.QtCore import Qt

# Import your transpiler
try:
    from transpiler import LatexTranspiler
except ImportError:
    class LatexTranspiler:
        def __init__(self): 
            self.settings = {}
        def update_settings(self, s): 
            self.settings = s
        def transpile(self, t): 
            return f"% Settings used: {self.settings}\n\\documentclass{{article}}\n\\begin{{document}}\n{t}\n\\end{{document}}"

class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.setWindowTitle("Compiler Settings")
        self.resize(400, 300)
        self.settings = current_settings or {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # --- Tab 1: Formatting ---
        fmt_tab = QWidget()
        fmt_layout = QVBoxLayout(fmt_tab)

        # Title Toggle
        self.title_check = QCheckBox("Include Document Title (First Line)")
        self.title_check.setChecked(self.settings.get('include_title', True))
        fmt_layout.addWidget(self.title_check)
        
        fmt_layout.addStretch()
        tabs.addTab(fmt_tab, "Structure")

        # --- Tab 2: Keywords ---
        lists_tab = QWidget()
        lists_layout = QVBoxLayout(lists_tab)
        
        def create_list_section(label_text, key):
            lbl = QLabel(label_text)
            lst = QListWidget()
            lst.addItems(self.settings.get(key, []))
            
            btn_layout = QHBoxLayout()
            add_btn = QPushButton("Add")
            del_btn = QPushButton("Remove")
            
            add_btn.clicked.connect(lambda: self.add_item(lst))
            del_btn.clicked.connect(lambda: self.remove_item(lst))
            
            btn_layout.addWidget(add_btn)
            btn_layout.addWidget(del_btn)
            
            lists_layout.addWidget(lbl)
            lists_layout.addWidget(lst)
            lists_layout.addLayout(btn_layout)
            return lst

        self.anchor_list = create_list_section("Anchor Words (Force Text Mode):", 'anchors')
        
        # Separator
        line = QLabel()
        line.setFrameStyle(QLabel.Shape.HLine | QLabel.Shadow.Sunken)
        lists_layout.addWidget(line)
        
        self.primer_list = create_list_section("Math Primers (Force Math Mode):", 'primers')
        
        tabs.addTab(lists_tab, "Keywords")
        layout.addWidget(tabs)

        # Save Button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.accept)
        layout.addWidget(save_btn)

    def add_item(self, list_widget):
        text, ok = QInputDialog.getText(self, "Add Item", "Value:")
        if ok and text:
            list_widget.addItem(text)

    def remove_item(self, list_widget):
        for item in list_widget.selectedItems():
            list_widget.takeItem(list_widget.row(item))

    def get_settings(self):
        anchors = [self.anchor_list.item(i).text() for i in range(self.anchor_list.count())]
        primers = [self.primer_list.item(i).text() for i in range(self.primer_list.count())]
        
        return {
            'include_title': self.title_check.isChecked(),
            'anchors': anchors,
            'primers': primers
        }

class LatexCompilerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.transpiler = LatexTranspiler()
        
        # Initialize default settings
        self.current_settings = {
            'include_title': True,
            'anchors': ['Figure', 'Table'],
            'primers': ['$']
        }
        
        self.setWindowTitle("AI Text to LaTeX Compiler")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Toolbar Area ---
        toolbar_layout = QHBoxLayout()
        
        # Settings Button
        settings_btn = QPushButton("⚙ Settings")
        settings_btn.clicked.connect(self.open_settings)
        toolbar_layout.addWidget(settings_btn)
        
        toolbar_layout.addStretch()
        
        # --- Mode Selector ---
        toolbar_layout.addWidget(QLabel("Output Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Compile to PDF", "Export .tex Only"])
        toolbar_layout.addWidget(self.mode_combo)
        
        main_layout.addLayout(toolbar_layout)

        # --- Text Area ---
        self.text_area = DragDropTextEdit()
        self.text_area.setPlaceholderText("Paste text here or drag a .txt file...")
        main_layout.addWidget(self.text_area)

        # --- Action Button ---
        self.action_btn = QPushButton("Process")
        self.action_btn.clicked.connect(self.run_process)
        main_layout.addWidget(self.action_btn)

    def open_settings(self):
        dialog = SettingsDialog(self, self.current_settings)
        if dialog.exec():
            self.current_settings = dialog.get_settings()
            self.transpiler.update_settings(self.current_settings)

    def run_process(self):
        """Orchestrates the transpilation and output based on mode selection."""
        raw_content = self.text_area.toPlainText()
        if not raw_content.strip():
            self.show_error("Input Empty", "Please provide text or a file.")
            return

        # 1. Update Settings & Transpile
        self.transpiler.update_settings(self.current_settings)
        try:
            tex_content = self.transpiler.transpile(raw_content)
        except Exception as e:
            self.show_error("Transpilation Error", str(e))
            return

        # 2. Check Mode
        mode = self.mode_combo.currentText()
        if mode == "Export .tex Only":
            self.export_tex_only(tex_content)
        else:
            self.compile_to_pdf(tex_content)

    def export_tex_only(self, tex_content):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save LaTeX File", os.path.expanduser("~"), "TeX Files (*.tex)")
        if not file_path: return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(tex_content)
            QMessageBox.information(self, "Success", f"File saved successfully:\n{file_path}")
        except IOError as e:
            self.show_error("File Save Error", str(e))

    def compile_to_pdf(self, tex_content):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save & Compile", os.path.expanduser("~"), "TeX Files (*.tex)")
        if not file_path: return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(tex_content)
        except IOError as e:
            self.show_error("File Save Error", str(e))
            return
            
        self.execute_pdflatex(file_path)

    def execute_pdflatex(self, tex_file_path):
        working_dir = os.path.dirname(tex_file_path)
        base_name = os.path.basename(tex_file_path)
        
        # --- FIX: HARDCODED PATH ---
        pdflatex_path = "/Library/TeX/texbin/pdflatex"
        
        if not os.path.exists(pdflatex_path):
             self.show_error("Configuration Error", 
                             f"Could not find pdflatex at: {pdflatex_path}\n"
                             "Please check the path in app.py")
             return

        command = [pdflatex_path, '-interaction=nonstopmode', base_name]

        try:
            subprocess.run(
                command, 
                cwd=working_dir, 
                capture_output=True, 
                text=True, 
                check=True
            )
            QMessageBox.information(self, "Success", "PDF compiled successfully!")
            
            pdf_file = tex_file_path.replace(".tex", ".pdf")
            subprocess.run(['open', pdf_file]) 

        except subprocess.CalledProcessError as e:
            error_msg = f"LaTeX Compilation Failed.\n\nLog tail:\n{e.stdout[-500:]}"
            self.show_error("Compilation Error", error_msg)

    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)

class DragDropTextEdit(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): e.accept()
        else: e.ignore()
    def dropEvent(self, e):
        files = [u.toLocalFile() for u in e.mimeData().urls()]
        if files:
            try:
                with open(files[0], 'r', encoding='utf-8') as f: self.setText(f.read())
            except Exception as e: print(e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LatexCompilerApp()
    window.show()
    sys.exit(app.exec())