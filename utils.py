from configparser import ConfigParser
import os.path
from typing import List

from telegram import InlineKeyboardButton

import uploader

def get_configuration() -> ConfigParser:
    path = "mediauploaderbot.ini"
    if not os.path.exists(path):
        raise RuntimeError(f"{path} not found. Look up in README for more info...")

    cfg = ConfigParser()
    cfg.read(path)

    if 'telegram' not in cfg or 'token' not in cfg['telegram']:
        raise Exception("No Telegram token found. Set 'token' field in [telegram] section.")

    if "database" not in cfg or "url" not in cfg["database"]:
        raise Exception("No database configuration found. Set 'url' field in [database] section.")

    return cfg

def uploaders_to_buttons() -> List[List[InlineKeyboardButton]]:
    keyboard = []
    row = []

    for k in uploader.ACCEPTABLE_UPLOADERS:
        row.append(InlineKeyboardButton(k, callback_data="/setuploader " + k.lower()))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if len(row) != 0:
        keyboard.append(row)

    return keyboard
