from os.path import exists

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackContext, filters
from os import mkdir

async def download_file(update: Update, _: CallbackContext) -> None:
    if not exists("./temp"):
        mkdir("./temp")

    if len(update.message.photo) > 0:
        file_id = update.message.photo[-1]
        file = await update.get_bot().get_file(file_id)
        file_path = f"./temp/{file_id.file_unique_id}"
        await file.download_to_drive(file_path)

    await update.message.reply_text('Saved!')

def run():
    print("Starting the bot...")
    app = ApplicationBuilder().token("xd").build()
    app.add_handler(MessageHandler(filters.PHOTO, download_file))
    app.run_polling()

if __name__ == "__main__":
    run()