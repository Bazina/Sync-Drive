# Google Drive Sync Script

A Desktop app to synchronize files and folders between your local machine and Google Drive. Integrated with Google Drive
API v3.

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Google Drive Setup](#google-drive-setup)
6. [Usage](#usage)
7. [Contributing](#contributing)

## Introduction

This script enables you to synchronize files and folders between your local machine and Google Drive using Python. It
supports various file types, including Google Docs, Sheets, and Presentations.

## Features

- Sync files and folders between local machine and Google Drive.
- Optional chunked upload for large files.
- Create missing folders in Google Drive during synchronization.
- Recursively sync new files in folders.
- Sync MS Office files (docx, pptx, xlsx) as Google Docs, Sheets, and Presentations, and adjust names accordingly.
- Sync files and folders include
    - Download new files from Google Drive to local machine if they are created or updated in Google Drive.
    - Move files on local machine to its corresponding folder in Google Drive.
    - Delete files and folders on local machine if they are deleted in Google Drive.
    - Rename files and folders on local machine if they are renamed in Google Drive.
- There is cache file to store the last directory path, Google Drive folder ID and last sync time.

## Prerequisites

Before using this script, ensure you have the following:

- Python installed on your machine.
- Access to the Google Drive API (credentials.json file).
- Necessary Python libraries installed (colorama, pandas, google-auth, google-auth-oauthlib, google-auth-httplib2,
  google-api-python-client).

> **Note**
> - This script was tested on Python 3.10.

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/Bazina/Sync-Drive.git
   ```

2. Install dependencies:

   ```bash
   cd Sync-Drive
   pip install -r requirements.txt
   ```

## Google Drive Setup

Here is a [video](https://youtu.be/ifw3b4Uf06g) that walks through the setup process.

1. Set up a Google Cloud Project and enable the Google Drive API and Google Drive Activity API.
2. Create an OAuth consent screen (desktop application) with the required scopes (optional, you can go to step 4).
    - `https://www.googleapis.com/auth/drive`
    - `https://www.googleapis.com/auth/drive.activity.readonly`
3. Put the server domain in the Authorized Domains section.
4. Create an OAuth 2.0 Client ID and download the credentials file (you can leave the Authorized JavaScript origins
   blank).
5. Download the credentials file and rename it to `credentials.json`.
6. Run the script using Python and follow the instructions to authenticate with Google Drive. A `token.json` file will
   be created.

## Usage

You can create an executable file using `pyinstaller`:

```bash
pyinstaller --onefile --name Sync --windowed --icon=google-drive.png --add-data "warning.png;." --noconsole App.py 
```

1. Run the script:

   ```bash
   python App.py
   ```

2. Select the local folder.
3. Enter the Google Drive folder ID to sync.
4. Hit the `Sync` button.
5. The script will synchronize files and folders between the specified local folder and Google Drive.

> **Note**
>
> - The `drive folder id` is the last part of the URL of the Google Drive folder. For example, if the URL
    is `https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j`, the `drive_id` is `1a2b3c4d5e6f7g8h9i0j`.

## Contributing

Contributions are welcomed! Fork the repository, make changes, and submit a pull request.