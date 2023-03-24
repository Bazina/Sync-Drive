import json
import os

import pydrive.files
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCursor, QIcon
from PyQt5.QtWidgets import *
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

app = QApplication([])

SKIP = {
    "application/vnd.google-apps.audio",
    "application/vnd.google-apps.video"
}

MIMETYPES = {
    # Drive Document files as MS dox
    'application/vnd.google-apps.document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    # Drive Sheets files as MS Excel files.
    'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    # Drive presentation as MS pptx
    'application/vnd.google-apps.presentation':
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
}
EXTENSIONS = {
    'application/vnd.google-apps.document': '.docx',
    'application/vnd.google-apps.spreadsheet': '.xlsx',
    'application/vnd.google-apps.presentation': '.pptx'
}


class Widgets(QWidget):
    def __init__(self):
        super(Widgets, self).__init__()
        self.drive = None
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
        with open("cache.json", "r") as cache:
            cache = cache.read()
            data = json.loads(cache)
            self.t1.setText(data["directory"])
        self.h_layout1.addWidget(self.t1)

        self.h_layout4 = QHBoxLayout()

        self.l4 = QLabel()
        self.l4.setFont(QFont("Roboto", 15))
        self.l4.setText("Drive Folder ID")
        self.h_layout4.addWidget(self.l4)

        self.t4 = QLineEdit()
        self.t4.setFont(QFont("Roboto", 15))
        with open("cache.json", "r") as cache:
            cache = cache.read()
            data = json.loads(cache)
            self.t4.setText(data["id"])
        self.h_layout4.addWidget(self.t4)

        self.h_layout2 = QHBoxLayout()

        self.btn = QPushButton("Sync")
        self.btn.clicked.connect(self.run_driver)
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
        print(response)
        self.t1.setText(response)
        return response

    def init_ui(self):
        self.setWindowTitle('Sync Drive')
        self.setGeometry(0, 0, 1280, 720)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def upload_recur(self, table, path, level):
        for x in table:
            x_mime_type = x['mimeType']
            x_path = os.path.join(path, x["title"])
            if x_mime_type in MIMETYPES:
                x_path = x_path + EXTENSIONS[x_mime_type]

            x_path_split = x_path.split("\\")

            if x["mimeType"] == 'application/vnd.google-apps.folder':
                self.text_box.setTextColor(QtGui.QColor('#F2F2F2'))
                self.text_box.append("{}{}".format(level * "\t", x_path_split[-1]))
                app.processEvents()
                if not os.path.exists(x_path):
                    self.text_box.setTextColor(QtGui.QColor('#F2B90C'))
                    self.text_box.append("{}Created {} folder in {}".format(level * "\t",
                                                                            x_path_split[-1],
                                                                            x_path_split[-2]))
                    app.processEvents()

                    os.mkdir(x_path)

                x_id = x['id']
                data_folder = self.drive.ListFile({'q': f"'{x_id}' in parents and trashed=false"}).GetList()
                self.upload_recur(data_folder, x_path, level + 1)
            else:
                if not os.path.exists(x_path):
                    self.text_box.setTextColor(QtGui.QColor('#F2B90C'))
                    self.text_box.append("{}Downloading {} to {}'s {}".format(level * "\t", x_path_split[-1],
                                                                              x_path_split[-3], x_path_split[-2]))
                    app.processEvents()

                    try:
                        if x_mime_type in SKIP:
                            return
                        if x_mime_type in MIMETYPES:
                            x.GetContentFile(x_path, mimetype=MIMETYPES[x_mime_type])
                        else:
                            x.GetContentFile(x_path)

                        self.text_box.setTextColor(QtGui.QColor('#1DC90E'))
                        self.text_box.append("{}Done\n".format(level * "\t"))
                        app.processEvents()
                    except pydrive.files.FileNotDownloadableError:
                        self.text_box.setTextColor(QtGui.QColor('#6CC6E5'))
                        self.text_box.append("{}Can't be downloaded (Not an error)\n".format(level * "\t"))
                        app.processEvents()

    def run_driver(self):
        directory = self.t1.text()
        drive_id = self.t4.text()
        if directory == "" or not os.path.exists(directory) or drive_id == "":
            self.t1.setFocus()
            self.error_dialog.show()
        else:
            with open("cache.json", "r") as cache:
                cache = cache.read()
                data = json.loads(cache)
                data["directory"] = directory
                data["id"] = drive_id

            with open("cache.json", "w") as cache:
                json.dump(data, cache)

            g_auth = GoogleAuth()
            self.drive = GoogleDrive(g_auth)

            data = self.drive.ListFile({'q': f"'{drive_id}' in parents and trashed=false"}).GetList()

            self.text_box.clear()
            self.text_box.moveCursor(QTextCursor.Start)
            self.upload_recur(data, directory, 0)

            self.text_box.setTextColor(QtGui.QColor('#F2F2F2'))
            self.text_box.append("The End.")


def run():
    style = """
            QWidget{
                background: #262D37;
            }
            QLabel{
                color: #fff;
            }
            QLabel#round_count_label, QLabel#highscore_count_label{
                border: 1px solid #fff;
                border-radius: 8px;
                padding: 2px;
            }
            QPushButton
            {
                color: white;
                background: #0577a8;
                border: 1px #DADADA solid;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
                outline: none;
            }
            QPushButton:hover{
                border: 1px #C6C6C6 solid;
                color: #fff;
                background: #0892D0;
            }
            QLineEdit {
                padding: 1px;
                color: #fff;
                border-style: solid;
                border: 2px solid #FFD700;
                border-radius: 8px;
            }
        """

    app.setStyleSheet(style)
    app.setWindowIcon(QIcon("google-drive.png"))

    widgets = Widgets()
    widgets.show()
    app.exec_()


if __name__ == "__main__":
    run()
