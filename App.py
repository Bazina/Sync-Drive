import datetime
import json
import os

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *

from AppGUI import Widgets
from Drive import GoogleDriveClient

app = QApplication([])


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

    # read cache.json if exists otherwise set timestamp to 7 days ago
    if os.path.exists("cache.json"):
        with open("cache.json", "r") as f:
            data = json.load(f)
    else:
        data = {"timestamp": "", "local_directory": "", "drive_id": ""}
        with open("cache.json", "w") as f:
            json.dump(data, f)

    drive_client = GoogleDriveClient()
    widgets = Widgets(app, drive_client, data)
    drive_client.events_manager.set_gui_client(widgets)
    widgets.show()
    app.exec_()


if __name__ == "__main__":
    run()
