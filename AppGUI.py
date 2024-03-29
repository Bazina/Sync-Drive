import datetime
import json
import os

from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCursor, QIcon
from PyQt5.QtWidgets import *


class Widgets(QWidget):
    def __init__(self, app, drive_client, cache_data):
        super(Widgets, self).__init__()
        self.app = app
        self.drive_client = drive_client
        self.last_timestamp = cache_data["timestamp"]
        self.local_directory = cache_data["local_directory"]
        self.drive_id = cache_data["drive_id"]
        self.init_ui()

        self.error_dialog = QMessageBox()
        self.error_dialog.setFont(QFont("Roboto", 15))
        self.error_dialog.setText("The Directory is null! Enter it.")
        self.error_dialog.setWindowTitle("Error")
        self.error_dialog.setWindowIcon(QIcon("warning.png"))

        self.v_layout = QVBoxLayout()

        self.h_layout1 = QHBoxLayout()

        self.btn2 = QPushButton("Select Directory")
        self.btn2.clicked.connect(self.get_directory)
        self.btn2.setFixedSize(170, 50)
        self.btn2.setFont(QFont("Roboto", 15))

        self.h_layout1.addWidget(self.btn2)

        self.t1 = QLineEdit()
        self.t1.setFont(QFont("Roboto", 15))

        self.t1.setText(self.local_directory)
        self.h_layout1.addWidget(self.t1)

        self.h_layout4 = QHBoxLayout()

        self.l4 = QLabel()
        self.l4.setFont(QFont("Roboto", 15))
        self.l4.setText("Drive Folder ID")
        self.h_layout4.addWidget(self.l4)

        self.t4 = QLineEdit()
        self.t4.setFont(QFont("Roboto", 15))

        self.t4.setText(self.drive_id)
        self.h_layout4.addWidget(self.t4)

        self.h_layout2 = QHBoxLayout()

        self.btn = QPushButton("Sync")
        self.btn.clicked.connect(self.sync)
        self.btn.setFixedSize(80, 50)
        self.btn.setFont(QFont("Roboto", 15))
        self.h_layout2.addWidget(self.btn)

        self.h_layout3 = QHBoxLayout()

        self.text_box = QTextBrowser()
        self.text_box.setFont(QFont("Roboto", 15))
        self.h_layout3.addWidget(self.text_box)

        self.v_layout.addLayout(self.h_layout1)
        self.v_layout.addLayout(self.h_layout4)
        self.v_layout.addLayout(self.h_layout2)
        self.v_layout.addLayout(self.h_layout3)
        self.v_layout.setAlignment(Qt.AlignTop)

        self.setLayout(self.v_layout)

    def get_directory(self):
        response = QFileDialog.getExistingDirectory(
            self,
            caption='Select a Folder'
        )
        self.t1.setText(os.path.normpath(response))
        print(os.path.normpath(response))
        return os.path.normpath(response)

    def init_ui(self):
        self.setWindowTitle('Sync Drive')
        self.setGeometry(0, 0, 1280, 720)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def notify(self, event, text):
        self.text_box.append(text)
        self.app.processEvents()

    def sync(self):
        directory = self.t1.text()
        drive_id = self.t4.text()
        if directory == "" or not os.path.exists(directory) or drive_id == "":
            self.t1.setFocus()
            self.error_dialog.show()
        else:
            current_timestamp = datetime.datetime.utcnow().isoformat() + 'Z'
            new_cache_data = {"timestamp": current_timestamp, "local_directory": directory, "drive_id": drive_id}

            self.text_box.clear()
            self.text_box.moveCursor(QTextCursor.Start)

            self.drive_client.build_drive_client(directory, drive_id, self.last_timestamp)

            self.drive_client.get_changes_and_download(current_timestamp)

            with open("cache.json", "w") as cache:
                json.dump(new_cache_data, cache)
