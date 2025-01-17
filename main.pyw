import os.path
import json

from PySide6.QtGui import Qt, QPalette, QColor, QDoubleValidator
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel, \
    QStyleFactory, QHBoxLayout, QFileDialog, QListWidget, QSpacerItem, QSizePolicy, QFrame, QLineEdit
import ctypes, sys

from win32comext.adsi.demos.search import options

scaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MainWindow with Central Widget")
        self.setFixedWidth(500 * scaleFactor)
        self.setFixedHeight(400 * scaleFactor)

        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(QHBoxLayout())
        self.centralWidget().layout().setAlignment(Qt.AlignmentFlag.AlignHCenter)

        central_widget = QWidget()
        self.centralWidget().layout().addWidget(central_widget)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        central_widget.setLayout(self.main_layout)
        
        self.main_layout.addWidget(QLabel("Selected Audio Files (double click to remove):"))
        self.file_list_widget = QListWidget()
        self.main_layout.addWidget(self.file_list_widget)
        self.file_list_widget.itemDoubleClicked.connect(self.remove_selected_file)

        hbox = QHBoxLayout()
        self.main_layout.addLayout(hbox)
        
        file_selector_button = QPushButton("Select Audio Files...")
        file_selector_button.clicked.connect(self.select_files)
        hbox.addWidget(file_selector_button)

        clear_button = QPushButton("Clear all")
        clear_button.clicked.connect(self.remove_all_files)
        hbox.addWidget(clear_button)

        self.main_layout.addWidget(QLabel("Preset:"))
        self.hbox2 = QHBoxLayout()
        self.main_layout.addLayout(self.hbox2)

        self.new_dropdown = QComboBox()
        options = ["Extra Option A", "Extra Option B", "Custom"]
        self.new_dropdown.addItems(options)
        if os.path.exists("preset"):
            with open("preset", "r") as f:
                text = f.read()
                if text in options:
                    self.new_dropdown.setCurrentText(text)
        self.hbox2.addWidget(self.new_dropdown)

        self.custom_preset = QPushButton("Edit")
        self.custom_preset.clicked.connect(self.show_custom_preset_popup)
        self.hbox2.addWidget(self.custom_preset)

        spacer = QSpacerItem(20 * scaleFactor, 40 * scaleFactor, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.main_layout.addItem(spacer)

        button = QPushButton("Convert")
        button.setFixedHeight(30 * scaleFactor)
        self.main_layout.addWidget(button)


    def select_files(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilters(["Audio files (*.mp3 *.wav *.ogg)"])
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            self.file_list_widget.addItems(selected_files)

    def remove_selected_file(self, item):
        self.file_list_widget.takeItem(self.file_list_widget.row(item))

    def remove_all_files(self):
        self.file_list_widget.clear()

    def show_custom_preset_popup(self):
        popup_widget = QFrame(self)
        popup_widget.setWindowTitle("Custom Preset")
        popup_widget.setFixedSize(self.size())
        popup_widget.setStyleSheet("background-color: #1e1f22")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        spacer = QSpacerItem(self.height(), self.height(), QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        popup_widget.setLayout(layout)

        layout.addWidget(QLabel("Preset Name:"))
        name_input = QLineEdit(self.new_dropdown.currentText())
        layout.addWidget(name_input)

        layout.addWidget(QLabel("Volume change (db):"))
        volume_input = QLineEdit("0")
        volume_input.setValidator(QDoubleValidator())
        layout.addWidget(volume_input)

        encoding_label = QLabel("Audio Encoding:")
        layout.addWidget(encoding_label)

        encoding_combobox = QComboBox()
        encoding_combobox.currentIndexChanged.connect(
            lambda index: print(encoding_combobox.itemData(index))
        )
        try:
            with open("utils/encodings.json", "r") as file:
                encodings = json.load(file)
                if isinstance(encodings, dict):
                    for key, desc in encodings["audio_encodings"].items():
                        encoding_combobox.addItem(desc, key)
                else:
                    encoding_combobox.addItem("No valid encodings found")
        except FileNotFoundError:
            encoding_combobox.addItem("No encodings found (encodings.json missing)")

        layout.addWidget(encoding_combobox)
        index = encoding_combobox.findData("wma")  # Find the index of "wma"
        if index != -1:  # Ensure a valid index was found
            text = encoding_combobox.itemText(index)  # Retrieve the text at that index
            encoding_combobox.setCurrentText(text)  # Set the combobox text
        else:
            print("Error: Unable to find the data 'wma' in the combobox")

        close_button = QPushButton("Close")
        save_button = QPushButton("Save Preset")
        delete_button = QPushButton("Delete Preset")
        close_button.clicked.connect(popup_widget.close)
        hbox = QHBoxLayout()
        hbox.addWidget(close_button)
        hbox.addWidget(save_button)
        if not self.new_dropdown.currentText() == "Custom":
            hbox.addWidget(delete_button)
        layout.addItem(spacer)
        layout.addLayout(hbox)
        popup_widget.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("fusion"))
    app.setPalette(QPalette(QColor("#1e1f22")))
    window = MainWindow()
    window.show()
    app.exec()
