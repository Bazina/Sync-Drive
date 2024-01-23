import json
import os
import io
import shutil

from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCursor, QIcon
from PyQt5.QtWidgets import *
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

app = QApplication([])

SKIP = {
    "application/vnd.google-apps.audio",
    "application/vnd.google-apps.video",
    "application/vnd.google-apps.shortcut"
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

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/drive.activity.readonly']


def authenticate():
    """Shows basic usage of the Drive v3 API.
            Prints the names and ids of the first 10 files the user has access to.
            """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)
        return service
    except HttpError as error:
        print('An error occurred: {}'.format(error))


def list_files_in_folder(folder_id, service):
    return service.files().list(
        q="'{}' in parents and trashed=false".format(folder_id),
        fields="files(id, name, mimeType, parents)"
    ).execute().get('files', [])


def export_pdf(file_id, file_mime_type, file_path, service, text_box, level):
    """
    Download a Document file in PDF format.
    :param file_id: file ID of any workspace document format file.
    :param file_mime_type: MIME type of the file to be downloaded.
    :param file_path: path to download the file to.
    :param service: Drive API Client.
    :param text_box: Text box to display the progress.
    :param level: level of the file in the folder hierarchy.
    :return: IO object with location
    """

    try:
        if file_mime_type in SKIP:
            return None
        elif file_mime_type in MIMETYPES:
            request = service.files().export_media(fileId=file_id,
                                                   mimeType=MIMETYPES[file_mime_type])
        else:
            request = service.files().get_media(fileId=file_id)

        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            text_box.setTextColor(QtGui.QColor('#F2B90C'))
            text_box.append('{}Download {}%.'.format(level * "\t", int(status.progress() * 100)))
        file.seek(0)

        with open(file_path, 'wb') as f:
            shutil.copyfileobj(file, f)

        text_box.setTextColor(QtGui.QColor('#1DC90E'))
        text_box.append("{}Done\n".format(level * "\t"))

    except HttpError as error:
        print('An error occurred: {}'.format(error))


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

    def download_recursive(self, table, path, level):
        """

        :param table: folder data in drive.
        :param path: path to download.
        :param level: level of the file in the folder hierarchy.
        :return: None.
        """
        for file in table:
            file_mime_type = file['mimeType']
            file_path = os.path.join(path, file["name"])
            if file_mime_type in MIMETYPES:
                file_path = file_path + EXTENSIONS[file_mime_type]

            x_path_split = file_path.split("\\")

            if file["mimeType"] == 'application/vnd.google-apps.folder':
                self.text_box.setTextColor(QtGui.QColor('#F2F2F2'))
                self.text_box.append("{}{}".format(level * "\t", x_path_split[-1]))
                app.processEvents()
                if not os.path.exists(file_path):
                    self.text_box.setTextColor(QtGui.QColor('#F2B90C'))
                    self.text_box.append("{}Created {} folder in {}".format(level * "\t",
                                                                            x_path_split[-1],
                                                                            x_path_split[-2]))
                    app.processEvents()

                    os.mkdir(file_path)

                file_id = file['id']
                data_folder = list_files_in_folder(file_id, self.drive)
                self.download_recursive(data_folder, file_path, level + 1)
            else:
                if not os.path.exists(file_path):
                    self.text_box.setTextColor(QtGui.QColor('#F2B90C'))
                    self.text_box.append("{}Downloading {} to {}'s {}".format(level * "\t", x_path_split[-1],
                                                                              x_path_split[-3], x_path_split[-2]))
                    app.processEvents()
                    try:
                        export_pdf(file['id'], file['mimeType'], file_path, self.drive, self.text_box, level)
                        app.processEvents()
                    except ValueError as error:
                        # self.text_box.setTextColor(QtGui.QColor('#6CC6E5'))
                        # self.text_box.append("{}Can't be downloaded (Not an error)\n".format(level * "\t"))
                        print(error)
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

            self.drive = authenticate()

            data = list_files_in_folder(drive_id, self.drive)

            self.text_box.clear()
            self.text_box.moveCursor(QTextCursor.Start)
            self.download_recursive(data, directory, 0)

            self.text_box.setTextColor(QtGui.QColor('#282C34'))
            self.text_box.append("The End.")


def run():
    style = """
            QWidget{
                background: #282C34;
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
                background: #353B45;
                border: 1px #DADADA solid;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
                outline: none;
            }
            QPushButton:hover{
                border: 1px #C6C6C6 solid;
                color: #fff;
                background: #414854;
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
