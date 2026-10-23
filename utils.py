from configparser import ConfigParser
import os.path
import sqlite3

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
