import sqlite3

import utils


class UploaderData:
    def __init__(self, url: str, field: str, headers: str|None, image_link: str, deletion_link: str|None):
        self.url = url
        self.field = field
        self.headers = headers
        self.image_link = image_link
        self.deletion_link = deletion_link

def init_uploader_db():
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

        cur.close()
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

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
        print(e)
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
                f"UPDATE file_uploader_preferences SET url = ?, field = ?, headers = ?, image_link = ?, deletion_link = ? WHERE id = ?",
                (uploader.url, uploader.field, uploader.headers, uploader.image_link, uploader.deletion_link, chat_id,)
            )
        else:
            cur.execute(
                f"INSERT INTO file_uploader_preferences(id, url, field, headers, image_link, deletion_link) VALUES (?, ?, ?, ?, ?, ?)",
                (chat_id, uploader.url, uploader.field, uploader.headers, uploader.image_link, uploader.deletion_link,)
            )

        conn.commit()
        cur.close()
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

ACCEPTABLE_UPLOADERS = {
    "tnd.quest": UploaderData("https://tnd.quest/upload", "file[]", "Accept: application/json", "{data.urls.download_url}", "{data.urls.deletion_url}"),
    "kappa.lol": UploaderData("https://kappa.lol/api/upload", "file", None, "{link}", "{delete}"),
    "Manual": None
}
