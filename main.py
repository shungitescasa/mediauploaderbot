import mimetypes
import traceback
from os import mkdir
from os.path import exists

import requests
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackContext, filters


def upload_file(file_path: str, comment: str) -> str:
    mime_type, _ = mimetypes.guess_type(file_path)

    if mime_type is None:
        raise Exception("Unknown MIME type")

    response = requests.post(
        'https://tnd.quest/upload.php',
        files=dict(
            file=(file_path.split('/')[-1], open(file_path, 'rb'), mime_type)
        ),
        data=dict(
            comment=comment,
            visibility=1
        ),
        headers=dict(
            accept='application/json'
        )
    )

    if response.status_code == 201:
        j = response.json()
        return j['data']['urls']['download_url']
    else:
        raise Exception(f"Failed to send a file ({response.status_code}): {response.text}")


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


def run():
    print("Starting the bot...")
    app = ApplicationBuilder().token("xd").build()
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.VIDEO_NOTE |
        filters.VOICE | filters.AUDIO | filters.ANIMATION |
        filters.Document.ALL | (filters.TEXT & ~filters.COMMAND),
        download_file
    ))
    app.run_polling()


if __name__ == "__main__":
    run()
