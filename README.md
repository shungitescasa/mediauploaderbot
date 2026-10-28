# mediauploaderbot

A Telegram bot for re-uploading images, voice messages and other files to file sharing websites.

## Installation

1. Clone the repository.
2. Create a Python virtual environment and activate it.

```bash
python3 -m venv .venv
. .venv/bin/activate
```

3. Install the dependencies

```bash
pip install -r requirements.txt
```

4. Create a configuration file named `mediauploaderbot.ini`

```ini
[telegram]
token = 123456789:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

[database]
url = ./database.db

; UNCOMMENT THIS SECTION TO ENABLE /url COMMAND
;[yt_dlp]
; You can use a file or a browser for cookies.
;cookies = PATH_TO_COOKIE_FILE
;cookiebrowser = BROWSER_NAME_TO_USE_FOR_COOKIES
```

5. Run the bot.

```bash
python3 main.py
```
