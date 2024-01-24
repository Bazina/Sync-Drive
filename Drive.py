import datetime
import io
import os
import shutil

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from EventsManager import EventsManager

FOLDER_TYPE = "application/vnd.google-apps.folder"

SKIP = {
    "application/vnd.google-apps.audio",
    "application/vnd.google-apps.video",
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

events_colors = {
    "create": "#DB8521",
    "update": "#DB8521",
    "download": "#DB8521",
    "done": "#23DB45",
    "move": "#23DBAE",
    "rename": "#23DBAE",
    "restore": "#23DBAE",
    "delete": "#DB5023",
    "skip": "#fff",
    "start": "#fff",
}


class GoogleDriveClient:
    def __init__(self):
        self.drive_service, self.activity_service = self.authenticate()
        self.events_manager = EventsManager()
        self.last_timestamp = None
        self.local_directory = None
        self.drive_id = None
        self.home = None

    def build_drive_client(self, directory, drive_id, last_timestamp):
        """
        Build the Google Drive client.
        :param directory: local directory.
        :param drive_id: Google Drive ID.
        :param last_timestamp: timestamp of the last call.
        :return: None.
        """
        self.drive_id = drive_id
        self.local_directory = directory
        self.last_timestamp = last_timestamp

    @staticmethod
    def authenticate():
        """Shows basic usage of the Drive v3 API.
                Prints the names and ids of the first 10 files the user has access to.
                """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
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
            drive_service = build('drive', 'v3', credentials=creds)
            activity_service = build('driveactivity', 'v2', credentials=creds)
            return drive_service, activity_service
        except HttpError as error:
            print('An error occurred: {}'.format(error))

    @staticmethod
    def list_files_in_folder(folder_id, service):
        """
        List all files in a folder.
        :param folder_id: folder ID.
        :param service: Google Drive service.
        :return: list of files in the folder.
        """
        return service.files().list(
            q="'{}' in parents and trashed=false".format(folder_id),
            fields="files(id, name, mimeType, parents)"
        ).execute().get('files', [])

    def export_and_download_file(self, file_id, file_mime_type, file_path):
        """
        Download a Document file in Its format.
        :param file_id: file ID of any workspace document format file.
        :param file_mime_type: MIME type of the file to be downloaded.
        :param file_path: path to download the file to.
        :return: IO object with location
        """

        try:
            file_name = file_path.split("\\")[-1]
            if file_mime_type in SKIP:
                self.events_manager.update("skip", f"<br><html><p style='color:{events_colors['skip']}'>"
                                                   f"<b>Skipped</b> {file_name},"
                                                   f" because of its type {file_mime_type.split('.')[-1]}.</p></html>")
                return None
            elif file_mime_type in MIMETYPES:
                request = self.drive_service.files().export_media(fileId=file_id,
                                                                  mimeType=MIMETYPES[file_mime_type])
            else:
                request = self.drive_service.files().get_media(fileId=file_id)

            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False
            self.events_manager.update("download", f"<html><br><p style='color:{events_colors['download']}'>"
                                                   f"Start Downloading <b>{file_name}</b>.</p>")
            while not done:
                status, done = downloader.next_chunk()
                if done:
                    progress = 100
                else:
                    progress = int(status.progress() * 100)
                self.events_manager.update("download", f"<html><p style='color:{events_colors['download']}'>"
                                                       f"<b>Downloading</b> {progress}%.</p>"
                                                       f"</html>")
            file.seek(0)

            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file, f)

            # take last 3 directories in path
            shortened_file_path = "\\".join(file_path.split("\\")[-4:-1])
            self.events_manager.update("done", f"<html><p style='color:{events_colors['done']}'>"
                                               f"<b>Done</b> downloading"
                                               f" {file_name} to {shortened_file_path}.</p></html>")

        except HttpError as error:
            print('An error occurred: {}'.format(error))

    @staticmethod
    def build_real_link_if_shortcut(file_metadata):
        """
        Build the real link of a shortcut.
        :param file_metadata: file metadata.
        :return: real shortcut file metadata.
        """
        if file_metadata['mimeType'] == "application/vnd.google-apps.shortcut":
            if file_metadata['shortcutDetails']['targetMimeType'] == ("%s" % FOLDER_TYPE):
                file_metadata['webViewLink'] = file_metadata['webViewLink'].replace("file/", "folder/")
                file_metadata['webViewLink'] = file_metadata['webViewLink'].replace(file_metadata['id'],
                                                                                    file_metadata[
                                                                                        'shortcutDetails'][
                                                                                        'targetId'])
                file_metadata[
                    'iconLink'
                ] = 'https://drive-thirdparty.googleusercontent.com/16/type/%s' % FOLDER_TYPE
            else:
                file_metadata['webViewLink'] = file_metadata['webViewLink'].replace(file_metadata['id'],
                                                                                    file_metadata[
                                                                                        'shortcutDetails'][
                                                                                        'targetId'])
            file_metadata['mimeType'] = file_metadata['shortcutDetails']['targetMimeType']
            file_metadata['id'] = file_metadata['shortcutDetails']['targetId']
        return file_metadata

    def build_file_metadata(self, new_file_id):
        """
        Build the metadata of a file.
        :param new_file_id: file ID.
        :return: file metadata.
        """
        try:
            file_metadata = self.drive_service.files().get(
                fileId=new_file_id,
                fields="id, name, mimeType, parents, shortcutDetails"
            ).execute()
        except HttpError as error:
            print('An error occurred: {}'.format(error))
            return None

        if not file_metadata['parents']:
            return file_metadata

        file_parents_names = self.build_file_path(file_metadata=file_metadata)

        if file_metadata.get('shortcutDetails'):
            file_metadata = self.build_real_link_if_shortcut(file_metadata)

        new_file_metadata = file_metadata
        new_file_metadata['directory'] = file_parents_names

        return new_file_metadata

    def build_file_path(self, file_id="", file_metadata=None):
        """
        Build the path to a file.
        :param file_id: file ID.
        :param file_metadata: file metadata.
        :return: path to the file.
        """
        if not file_metadata:
            file_metadata = self.drive_service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, parents, shortcutDetails"
            ).execute()

        if file_metadata['name'] == self.home:
            return [self.local_directory]

        file_parents_names = []
        file_parent_id = file_metadata['parents'][0]
        while True:
            parent_metadata = self.drive_service.files().get(
                fileId=file_parent_id,
                fields="id, name, parents"
            ).execute()

            parent_name = parent_metadata['name']

            if not parent_metadata.get('parents') or parent_name == self.home:
                break
            else:
                file_parents_names.append(parent_name)
                file_parent_id = parent_metadata['parents'][0]

        file_parents_names.append(self.local_directory)
        file_parents_names.reverse()

        return file_parents_names

    def pull_changes_with_limit(self, timestamp, page_size=100):
        """
        Pull changes from Google Drive with a limit.
        :param timestamp: timestamp of the call.
        :param page_size: number of changes to pull.
        :return: activities data.
        """
        return self.activity_service.activity().query(
            body={
                'ancestorName': f'items/{self.drive_id}',
                'pageSize': page_size,
                'filter': f'time >= "{timestamp}"'
                          f' detail.action_detail_case:(CREATE MOVE RENAME DELETE EDIT RESTORE)'
            }
        ).execute()

    @staticmethod
    def is_activities_data_empty(activities_data):
        """
        Check if the activities data is empty.
        :param activities_data: activities data.
        :return: True if empty, False otherwise.
        """
        return (not activities_data or not activities_data['activities'] or
                len(activities_data['activities']) == 0)

    @staticmethod
    def create_missing_folders(file_metadata):
        """
        Create missing folders in the path.
        :param file_metadata: file metadata.
        :return: path to the file.
        """
        parents = file_metadata[1:]
        path = file_metadata[0]
        for folder in parents:
            path = os.path.join(path, folder)
            if not os.path.exists(path):
                os.mkdir(path)
                print(f"created {folder}")
        return path

    def get_changes_and_download(self, call_timestamp):
        """
        Get changes from Google Drive and sync them.
        It handles the following actions:
        - Create: create a folder or download a file.
        - Delete: delete a file or folder.
        - Rename: rename a file or folder.
        - Move: move a file or folder.
        :param call_timestamp: timestamp of the call.
        :return: None.
        """
        self.events_manager.update("start", f"<html><h2 style='color:{events_colors['start']}'>"
                                            f"Syncing...</h2></html>")

        self.home = self.drive_service.files().get(
            fileId=self.drive_id,
            fields="name"
        ).execute()["name"]

        current_timestamp = call_timestamp
        changed_files = self.pull_changes_with_limit(self.last_timestamp, 100)

        if self.is_activities_data_empty(changed_files):
            self.events_manager.update("skip", f"<html><br><h3 style='color:{events_colors['skip']}'>"
                                               f"No changes to sync.</h3></html>")

            self.last_timestamp = current_timestamp
            print(f"{self.last_timestamp}\ttime stamp updated with no changed files")
            return

        timestamp_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        for activity in reversed(changed_files['activities']):
            for target in activity['targets']:
                file_id = target['driveItem']['name'].split('/')[1]
                timestamp = activity['timestamp']

                # check if timestamp has fraction of seconds
                if '.' in timestamp:
                    timestamp_datetime = datetime.datetime.strptime(timestamp, timestamp_format)
                else:
                    timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
                last_timestamp_datetime = datetime.datetime.strptime(self.last_timestamp, timestamp_format)

                if timestamp_datetime.date() < last_timestamp_datetime.date():
                    print(f"this file id: {file_id} should have been notified before")
                    continue

                file_metadata = self.build_file_metadata(file_id)
                if file_metadata is None:
                    continue

                action = list(activity['primaryActionDetail'].keys())[0]
                path = os.path.join(*file_metadata['directory'])
                if action != 'delete' and action != 'rename':
                    path = self.create_missing_folders(file_metadata['directory'])

                if action == 'create':
                    self.create_event(file_id, file_metadata, path)
                elif action == 'edit':
                    self.edit_event(file_id, file_metadata, path)
                elif action == 'delete':
                    self.delete_event(file_metadata, path)
                elif action == 'restore':
                    self.restore_event(file_metadata, path)
                elif action == 'rename':
                    self.rename_event(activity, file_metadata, path)
                elif action == 'move':
                    self.move_event(activity, file_metadata)

        self.last_timestamp = current_timestamp
        print(f"{self.last_timestamp}\tupdated at the end of the call")
        self.events_manager.update("done", f"<html><br><h3 style='color:{events_colors['done']}'>"
                                           f"Syncing done.</h3></html>")

    def rename_event(self, activity, file_metadata, path):
        """
        Rename a file or folder.
        :param activity: Google Drive Activity object.
        :param file_metadata: file metadata.
        :param path: path to the file.
        :return: None.
        """
        file_metadata['oldTitle'] = activity['primaryActionDetail']['rename']['oldTitle']
        file_metadata['newTitle'] = activity['primaryActionDetail']['rename']['newTitle']
        if os.path.exists(os.path.join(path, file_metadata['oldTitle'])):
            os.rename(os.path.join(path, file_metadata['oldTitle']), os.path.join(path, file_metadata['newTitle']))

            shortened_file_path = "\\".join(os.path.join(path, file_metadata['newTitle']).split("\\")[-4:-1])
            self.events_manager.update("rename",
                                       f"<html><br><p style='color:{events_colors['rename']}'>"
                                       f"<b>Renamed {file_metadata['oldTitle']}</b> to"
                                       f" <b>{file_metadata['newTitle']}</b> in {shortened_file_path}.</p></html>")

    def move_event(self, activity, file_metadata):
        """
        Move a file or folder.
        :param activity: Google Drive Activity object.
        :param file_metadata: file metadata.
        :return: None.
        """
        move_action = activity['primaryActionDetail']['move']
        removed_parent = move_action['removedParents'][0]['driveItem']
        removed_parent_id = removed_parent['name'].split('/')[1]
        if removed_parent_id != self.drive_id:
            old_path = os.path.join(*self.build_file_path(removed_parent_id), removed_parent['title'])
        else:
            old_path = self.local_directory
        old_path = os.path.join(old_path, file_metadata['name'])

        added_parent = move_action['addedParents'][0]['driveItem']
        added_parent_id = added_parent['name'].split('/')[1]
        new_path = os.path.join(*self.build_file_path(added_parent_id), added_parent['title'])

        if not os.path.exists(os.path.join(str(new_path), file_metadata['name'])):
            shutil.move(str(old_path), str(new_path))
            shortened_old_path = "\\".join(old_path.split("\\")[-4:-1])
            shortened_new_path = "\\".join(new_path.split("\\")[-4:-1])
            self.events_manager.update("move",
                                       f"<html><br><p style='color:{events_colors['move']}'>"
                                       f"<b>Moved {file_metadata['name']}</b> from"
                                       f" {shortened_old_path} to {shortened_new_path}.</p></html>")

    def delete_event(self, file_metadata, path):
        """
        Delete a file or folder.
        :param file_metadata: file metadata.
        :param path: path to the file.
        :return: None.
        """
        if os.path.exists(os.path.join(path, file_metadata['name'])):
            shortened_file_path = "\\".join(os.path.join(path, file_metadata['name']).split("\\")[-4:-1])
            if file_metadata['mimeType'] == FOLDER_TYPE:
                shutil.rmtree(os.path.join(path, file_metadata['name']))
                self.events_manager.update("delete",
                                           f"<html><br><p style='color:{events_colors['delete']}'>"
                                           f"<b>Deleted</b> {file_metadata['name']}"
                                           f" folder in {shortened_file_path}.</p></html>")
            else:
                os.remove(os.path.join(path, file_metadata['name']))
                self.events_manager.update("delete", f"<html><br><p style='color:{events_colors['delete']}'>"
                                                     f"<b>Deleted {file_metadata['name']}</b>"
                                                     f" in {shortened_file_path}.</p></html>")

    def create_event(self, file_id, file_metadata, path):
        """
        Create a file or folder.
        :param file_id: file ID.
        :param file_metadata: file metadata.
        :param path: path to the file.
        :return:
        """
        if file_metadata['mimeType'] != FOLDER_TYPE and not os.path.exists(os.path.join(path, file_metadata['name'])):
            self.export_and_download_file(file_id, file_metadata['mimeType'], os.path.join(path, file_metadata['name']))
        elif file_metadata['mimeType'] == FOLDER_TYPE and not os.path.exists(os.path.join(path, file_metadata['name'])):
            os.mkdir(os.path.join(path, file_metadata['name']))
            shortened_file_path = "\\".join(os.path.join(path, file_metadata['name']).split("\\")[-4:-1])
            self.events_manager.update("create", f"<html><br><p style='color:{events_colors['create']}'>"
                                                 f"<b>Created {file_metadata['name']}</b>"
                                                 f" folder in {shortened_file_path}.</p></html>")

    def edit_event(self, file_id, file_metadata, path):
        """
        A file was edited and need to be downloaded again.
        :param file_id: file ID.
        :param file_metadata: file metadata.
        :param path: path to the file.
        :return: None.
        """
        if file_metadata['mimeType'] != FOLDER_TYPE:
            shortened_file_path = "\\".join(os.path.join(path, file_metadata['name']).split("\\")[-4:-1])
            self.export_and_download_file(file_id, file_metadata['mimeType'], os.path.join(path, file_metadata['name']))
            self.events_manager.update("update", f"<html><br><p style='color:{events_colors['update']}'>"
                                                 f"<b>Updated {file_metadata['name']}</b>"
                                                 f" in {shortened_file_path}.</p></html>")

    def restore_event(self, file_metadata, path):
        """
        Restore a file or folder.
        :param file_metadata: file metadata.
        :param path: path to the file.
        :return: None.
        """
        if file_metadata['mimeType'] == FOLDER_TYPE:
            os.mkdir(os.path.join(path, file_metadata['name']))
            shortened_file_path = "\\".join(os.path.join(path, file_metadata['name']).split("\\")[-4:-1])
            self.events_manager.update("restore", f"<html><br><p style='color:{events_colors['restore']}'>"
                                                  f"<b>Restored {file_metadata['name']}</b>"
                                                  f" folder in {shortened_file_path}.</p></html>")
        else:
            self.export_and_download_file(file_metadata['id'], file_metadata['mimeType'],
                                          os.path.join(path, file_metadata['name']))
            shortened_file_path = "\\".join(os.path.join(path, file_metadata['name']).split("\\")[-4:-1])
            self.events_manager.update("restore", f"<html><br><p style='color:{events_colors['restore']}'>"
                                                  f"<b>Restored {file_metadata['name']}</b>"
                                                  f" in {shortened_file_path}.</p></html>")
