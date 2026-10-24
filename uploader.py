import mimetypes
import random
import sqlite3
import os
import string
import traceback
from typing import Tuple
import requests

import utils


class UploaderData:
    def __init__(self, url: str, field: str, headers: str|None, image_link: str, deletion_link: str|None):
        self.url = url
        self.field = field
        self.headers = headers
        self.image_link = image_link
        self.deletion_link = deletion_link

    def parsed_url(self):
        from urllib.parse import urlparse
        return urlparse(self.url)

    def base_url(self):
        u = self.parsed_url()
        return u.scheme + "://" + u.hostname

def init_uploader_db() -> bool:
    cfg = utils.get_configuration()

    try:
        conn = sqlite3.connect(cfg["database"]["url"])
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS file_uploader_preferences(
                id INTEGER PRIMARY KEY,
                url TEXT NOT NULL,
                field TEXT NOT NULL,
                headers TEXT,
                image_link TEXT NOT NULL,
                deletion_link TEXT
            );
            """)

        conn.commit()
        cur.close()
    except sqlite3.Error as e:
        traceback.print_tb(e.__traceback__)
        return False
    finally:
        if conn:
            conn.close()

    return True

def get_uploader(chat_id: int) -> UploaderData|None:
    cfg = utils.get_configuration()
    res = None

    try:
        conn = sqlite3.connect(cfg["database"]["url"])
        cur = conn.cursor()

        cur.execute("SELECT url, field, headers, image_link, deletion_link FROM file_uploader_preferences WHERE id = ?", (chat_id,))

        res = cur.fetchone()

        conn.commit()
        cur.close()
    except sqlite3.Error as e:
        traceback.print_tb(e.__traceback__)
        return None
    finally:
        if conn:
            conn.close()

    if res:
        return UploaderData(res[0], res[1], res[2], res[3], res[4])
    else:
        return None


def set_uploader(chat_id: int, uploader: UploaderData):
    cfg = utils.get_configuration()

    already_exists = get_uploader(chat_id) is not None

    try:
        conn = sqlite3.connect(cfg["database"]["url"])
        cur = conn.cursor()

        if already_exists:
            cur.execute(
                "UPDATE file_uploader_preferences SET url = ?, field = ?, headers = ?, image_link = ?, deletion_link = ? WHERE id = ?",
                (uploader.url, uploader.field, uploader.headers, uploader.image_link, uploader.deletion_link, chat_id,)
            )
        else:
            cur.execute(
                "INSERT INTO file_uploader_preferences(id, url, field, headers, image_link, deletion_link) VALUES (?, ?, ?, ?, ?, ?)",
                (chat_id, uploader.url, uploader.field, uploader.headers, uploader.image_link, uploader.deletion_link,)
            )

        conn.commit()
        cur.close()
    except sqlite3.Error as e:
        traceback.print_tb(e.__traceback__)
        return False
    finally:
        if conn:
            conn.close()

    return True

def delete_uploader(chat_id: int) -> bool:
    cfg = utils.get_configuration()

    try:
        conn = sqlite3.connect(cfg["database"]["url"])
        cur = conn.cursor()
        cur.execute("DELETE FROM file_uploader_preferences WHERE id = ?", (chat_id,))
        conn.commit()
        cur.close()
    except sqlite3.Error as e:
        traceback.print_tb(e.__traceback__)
        return False
    finally:
        if conn:
            conn.close()

    return True

def get_nested(data: dict, path: str) -> str | None:
    if path[0] == "{" and path[-1] == "}":
        path = path[1:-1]

    for key in path.split("."):
        if not isinstance(data, dict) or key not in data:
            return None
        data = data[key]

    return data if isinstance(data, str) else None

def upload_directory(chat_uploader: UploaderData, directory_path: str) -> Tuple[str,str|None]:
    files = []

    with os.scandir(directory_path) as dir:
        for file in dir:
            mime_type, _ = mimetypes.guess_type(file.path)
            if mime_type is None:
                raise Exception("Unknown MIME type: " + file.path)

            files.append((
                chat_uploader.field,
                (file.path.split('/')[-1], open(file.path, 'rb'), mime_type)
            ))

    if len(files) == 0:
        raise RuntimeError("No files to upload")

    response = requests.post(
        chat_uploader.url,
        files=files,
        data=dict(
            password=''.join(random.choices(string.ascii_letters + string.digits, k=16)),
            single_url=1,
            strip_exif_data=1
        ),
        headers=dict(
            accept='application/json'
        )
    )

    content_type = response.headers.get("Content-Type")
    is_json_response = content_type is not None and "application/json" in content_type

    image_link = None
    deletion_link = None

    if response.status_code < 300:
        if is_json_response:
            j = response.json()
            image_link = get_nested(j, chat_uploader.image_link)
            deletion_link = None
            if chat_uploader.deletion_link is not None:
                deletion_link = get_nested(j, chat_uploader.deletion_link)
        else:
            image_link = response.url
    else:
        text = response.text
        if is_json_response:
            j = response.json()
            # tnd.quest
            if 'data' in j and 'error' in j['data']:
                text = j['data']['error']

        raise RuntimeError(f"Failed to upload a file ({response.status_code}): {text}")

    if image_link:
        return (image_link, deletion_link)
    else:
        return (response.url, None)

def delete_file(chat_uploader: UploaderData, url: str) -> bool:
    if url.startswith("/"):
        url = chat_uploader.base_url() + url

    # kappa.lol has specific API for file deletion
    if "kappa.lol" in url or "segs.lol" in url or "femboy.beauty" in url or "gachi.gay" in url:
        from urllib.parse import urlparse
        query = urlparse(url).query
        url = chat_uploader.base_url() + "/api/delete?key=" + query

    response = requests.delete(url)
    return response.status_code == 200 or response.status_code == 404

ACCEPTABLE_UPLOADERS = {
    "tnd.quest": UploaderData("https://tnd.quest/upload", "file[]", "Accept: application/json", "{data.urls.download_url}", "{data.urls.deletion_url}"),
    "kappa.lol": UploaderData("https://kappa.lol/api/upload", "file", None, "{link}", "{delete}"),
    "Manual": None
}
