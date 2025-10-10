import os.path
import traceback
from configparser import ConfigParser
from os import mkdir, unlink
from os.path import exists

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackContext, filters

from extsrc import extsrc_add_handler
from file import upload_file


async def download_locally_file(update, file_id):
    file = await update.get_bot().get_file(file_id)
    file_extension = ""

    if file.file_path is not None:
        file_extension = f".{file.file_path.split('.')[-1]}".lower()

    file_path = f"./temp/{file_id.file_unique_id}{file_extension}"
    await file.download_to_drive(file_path)
    return file_path


async def download_file(update: Update, _: CallbackContext) -> None:
    if not exists("./temp"):
        mkdir("./temp")

    file_path = None
    file_comment = update.message.caption

    if len(update.message.photo) > 0:
        file_path = await download_locally_file(update, update.message.photo[-1])
    elif update.message.video is not None:
        file_path = await download_locally_file(update, update.message.video)
    elif update.message.video_note is not None:
        file_path = await download_locally_file(update, update.message.video_note)
    elif update.message.voice is not None:
        file_path = await download_locally_file(update, update.message.voice)
    elif update.message.audio is not None:
        file_path = await download_locally_file(update, update.message.audio)
    elif update.message.animation is not None:
        file_path = await download_locally_file(update, update.message.animation)
    elif update.message.document is not None:
        file_path = await download_locally_file(update, update.message.document)
    elif update.message.text is not None:
        file_path = f"./temp/{update.message.chat.id}-{update.message.message_id}.txt"
        with open(file_path, "w") as txtf:
            txtf.write(update.message.text)
            txtf.close()

    if file_path is not None:
        try:
            url = upload_file(file_path, file_comment)
            await update.message.reply_text(f'Saved! Here is your URL: [{url}]({url})', ParseMode.MARKDOWN,
                                            reply_to_message_id=update.message.message_id)
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            await update.message.reply_text(f"Error occurred while uploading your file: {str(e)}")
        unlink(file_path)


def run():
    if not os.path.exists("config.ini"):
        raise Exception("config.ini not found. Look up in README for more info...")

    cfg = ConfigParser()
    cfg.read("config.ini")

    if 'telegram' not in cfg or 'token' not in cfg['telegram']:
        raise Exception("No Telegram token found. Set 'token' field in [telegram] section.")

    print("Bot is running...")
    app = ApplicationBuilder().token(cfg['telegram']['token']).build()
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.VIDEO_NOTE |
        filters.VOICE | filters.AUDIO | filters.ANIMATION |
        filters.Document.ALL,
        download_file
    ))
    extsrc_add_handler(app)
    app.run_polling()


if __name__ == "__main__":
    run()
