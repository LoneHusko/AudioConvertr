import ctypes
import json
import os.path
import sys
import time
import traceback
from threading import Thread
from queue import Queue
import subprocess
from modules import audio_convert
from PySide6 import QtCore
from PySide6.QtCore import QMetaObject, QObject, Slot
from PySide6.QtGui import Qt, QPalette, QColor, QDoubleValidator, QIntValidator
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel, \
    QStyleFactory, QHBoxLayout, QFileDialog, QListWidget, QSpacerItem, QSizePolicy, QFrame, QLineEdit, QMessageBox, \
    QProgressBar

scaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100


class Invoker(QObject):
    def __init__(self):
        super(Invoker, self).__init__()
        self.queue = Queue()

    def invoke(self, func, *args, **kwargs):
        f = lambda: func(*args, **kwargs)
        self.queue.put(f)
        QMetaObject.invokeMethod(self, "handler", QtCore.Qt.QueuedConnection)

    @Slot()
    def handler(self):
        f = self.queue.get()
        f()


invoker = Invoker()


def invoke_in_main_thread(func, *args, **kwargs):
    invoker.invoke(func,*args, **kwargs)


def format_exception(exctype, value, traceback_obj):

    exception_str = '\n' + ''.join(traceback.format_exception(exctype, value, traceback_obj))

    return exception_str


def exception_hook(exctype, value, traceback_obj):
    time_stamp = time.time()
    time_stamp = time.strftime("%Y_%m_%d__%H_%M_%S", time.localtime(time_stamp))
    exception_str = format_exception(exctype, value, traceback_obj)
    if not os.path.exists("reports"):
        os.mkdir("reports")
    with open(f"reports/{time_stamp}.txt", "w") as f:
        f.write(exception_str)

    QMessageBox.critical(None, "Error", f"<p>An unexpected error occurred: <pre>"
                                        f"{str(exctype.__name__)}: {str(value)}</pre><br>"
                                        f"The application will quit. Please contact support.<br>"
                                        f"A detailed error message has been saved here: <br>"
                                        f"<pre><code>{os.path.abspath(f'reports/{time_stamp}.txt')}</code></pre></p>")

    sys.__excepthook__(exctype, value, traceback_obj)
    app.quit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.volume = 0
        self.encoding = "wma"
        self.sample_rate = 44100
        self.setWindowTitle("AudioConvertr")
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
        
        self.main_layout.addWidget(QLabel("Selected Audio Files (double click item to remove):"))
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
        self.refresh_presets()
        self.hbox2.addWidget(self.new_dropdown)
        self.new_dropdown.currentIndexChanged.connect(self.save_preset_state)


        self.custom_preset = QPushButton("Edit")
        self.custom_preset.setFixedWidth(50 * scaleFactor)
        self.custom_preset.clicked.connect(self.show_custom_preset_popup)
        self.hbox2.addWidget(self.custom_preset)

        spacer = QSpacerItem(20 * scaleFactor, 40 * scaleFactor, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.main_layout.addItem(spacer)

        button = QPushButton("Convert")
        button.clicked.connect(self.convert)
        button.setFixedHeight(30 * scaleFactor)
        self.main_layout.addWidget(button)

    def refresh_presets(self):
        self.new_dropdown.currentIndexChanged.disconnect()
        self.new_dropdown.clear()
        options = self.get_presets()
        self.new_dropdown.addItems(list(options))
        if os.path.exists("preset"):
            with open("preset", "r") as f:
                text = f.read()
                if text in options:
                    self.new_dropdown.setCurrentText(text)
        self.save_preset_state()
        self.new_dropdown.currentIndexChanged.connect(self.save_preset_state)

    @staticmethod
    def get_presets():
        with open("utils/presets.json") as f:
            presets = json.load(f)
            return presets.keys()

    def save_preset_state(self):
        with open("preset", "w") as f:
            f.write(self.new_dropdown.currentText())
        with open("utils/presets.json", "r") as f:
            preset = json.load(f)[self.new_dropdown.currentText()]
        self.volume = preset["volume"]
        self.encoding = preset["encoding"]
        self.sample_rate = preset["sample_rate"]

        print("Volume: ", self.volume)
        print("Encoding: ", self.encoding)
        print("Sample Rate: ", self.sample_rate)

    def save_preset(self):
        with open("utils/presets.json", "r") as f:
            preset = json.load(f)

        self.name_input.setDisabled(True)
        self.volume_input.setDisabled(True)
        self.encoding_combobox.setDisabled(True)
        self.sample_rate_input.setDisabled(True)

        preset[self.name_input.text()] = {}
        preset[self.name_input.text()]["volume"] = int(self.volume_input.text())
        preset[self.name_input.text()]["encoding"] = str(self.encoding_combobox.itemData(self.encoding_combobox.currentIndex()))
        preset[self.name_input.text()]["sample_rate"] = int(self.sample_rate_input.text())

        with open("preset", "w") as f:
            f.write(self.name_input.text())
        self.name_input.setDisabled(False)
        self.volume_input.setDisabled(False)
        self.encoding_combobox.setDisabled(False)
        self.sample_rate_input.setDisabled(False)

        with open("utils/presets.json", "w") as f:
            json.dump(preset, f, indent=4)

        self.refresh_presets()

    def delete_preset(self):
        with open("utils/presets.json", "r") as f:
            preset = json.load(f)
        preset.pop(self.name_input.text())
        with open("utils/presets.json", "w") as f:
            json.dump(preset, f, indent=4)
        self.refresh_presets()

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
        popup_widget.setStyleSheet("background-color: #2b2d30")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        spacer = QSpacerItem(self.height(), self.height(), QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        popup_widget.setLayout(layout)

        layout.addWidget(QLabel("Preset Name:"))
        self.name_input = QLineEdit(self.new_dropdown.currentText()) if self.new_dropdown.currentText() == "Custom" else QLabel(self.new_dropdown.currentText())
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Volume change (db):"))
        self.volume_input = QLineEdit(str(self.volume))
        self.volume_input.setValidator(QDoubleValidator())
        layout.addWidget(self.volume_input)

        encoding_label = QLabel("Audio Encoding:")
        layout.addWidget(encoding_label)

        self.encoding_combobox = QComboBox()
        self.encoding_combobox.currentIndexChanged.connect(
            lambda index: print(self.encoding_combobox.itemData(index))
        )
        try:
            with open("utils/encodings.json", "r") as file:
                encodings = json.load(file)
                if isinstance(encodings, dict):
                    for key, desc in encodings["audio_encodings"].items():
                        self.encoding_combobox.addItem(desc, key)
                else:
                    self.encoding_combobox.addItem("No valid encodings found")
        except FileNotFoundError:
            self.encoding_combobox.addItem("No encodings found (encodings.json missing)")

        layout.addWidget(self.encoding_combobox)
        index = self.encoding_combobox.findData(self.encoding)
        if index != -1:  # Ensure a valid index was found
            text = self.encoding_combobox.itemText(index)  # Retrieve the text at that index
            self.encoding_combobox.setCurrentText(text)  # Set the combobox text
        else:
            pass

        layout.addWidget(QLabel("Sample Rate (Hz):"))
        self.sample_rate_input = QLineEdit(str(self.sample_rate))
        self.sample_rate_input.setValidator(QIntValidator())
        layout.addWidget(self.sample_rate_input)

        close_button = QPushButton("Save and Close")
        delete_button = QPushButton("Delete Preset")
        delete_button.clicked.connect(self.delete_preset)
        delete_button.clicked.connect(popup_widget.close)
        close_button.clicked.connect(self.save_preset)
        close_button.clicked.connect(popup_widget.close)
        hbox = QHBoxLayout()
        hbox.addWidget(close_button)
        if not self.new_dropdown.currentText() == "Custom":
            hbox.addWidget(delete_button)
        layout.addItem(spacer)
        layout.addLayout(hbox)
        popup_widget.show()

    def convert(self):
        if not os.path.exists("output"):
            os.mkdir("output")

        def thread(widget, status):
            files = []
            for i in range(self.file_list_widget.count()):
                files.append(self.file_list_widget.item(i).text())
            if len(files) == 0:
                invoke_in_main_thread(QMessageBox.critical, None, "Error", "No audio files selected.")
                widget.close()
                return

            segment = 100 / len(files)
            failed = 0

            for index, i in enumerate(files):
                name = i.split("/")[-1].split(".")[0]
                invoke_in_main_thread(self.info.setText, name)
                invoke_in_main_thread(self.failed.setText, f"Failed: {failed}")
                try:
                    audio_convert.edit_audio_properties(
                        input_path=i,
                        output_path="output/" + name + ".wav",
                        volume_change_db=self.volume,
                        encoding=self.encoding,
                        sample_rate=self.sample_rate
                    )
                except subprocess.CalledProcessError as e:
                    failed += 1
                status.setValue(segment * (index + 1))
            if failed == 0:
                invoke_in_main_thread(QMessageBox.information, self, "Success", f"Successfully converted audio files.")
            else:
                invoke_in_main_thread(QMessageBox.warning, self, "Partial success", f"{failed} files failed to convert.")
            widget.close()

        popup_widget = QFrame(self)
        popup_widget.setWindowTitle("Custom Preset")
        popup_widget.setFixedSize(self.size())
        popup_widget.setStyleSheet("background-color: #2b2d30")
        layout = QVBoxLayout()
        popup_widget.setLayout(layout)
        popup_widget.show()
        label = QLabel("<h1>Converting...</h1>")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.info = QLabel("")
        self.info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info)
        self.failed = QLabel("")
        self.failed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.failed)
        spacer = QSpacerItem(self.height(), self.height(), QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addItem(spacer)
        status = QProgressBar()
        layout.addWidget(status)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        QApplication.processEvents()
        x = Thread(target=thread, args=(popup_widget, status,))
        x.start()



if __name__ == "__main__":
    sys.excepthook = exception_hook
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("fusion"))
    app.setPalette(QPalette(QColor("#2b2d30")))
    if not os.path.exists("utils/presets.json"):
        with open("utils/presets.json", "w") as f:
            json.dump({
                "Custom": {
                    "volume": 0,
                    "encoding": "pcm_s16le",
                    "sample_rate": 48000
                }
            }, f, indent=4)
    with open("utils/presets.json", "r") as f:
        preset = json.load(f)
        if "Custom" not in preset.keys():
            preset["Custom"] = {
                "volume": 0,
                "encoding": "pcm_s16le",
                "sample_rate": 48000
            }
    with open("utils/presets.json", "w") as f:
        json.dump(preset, f, indent=4)

    window = MainWindow()
    window.show()
    app.exec()
