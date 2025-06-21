from os import unlink
from time import time

import yt_dlp
from file import upload_file
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes

STATES = dict(
    extsrc_url=1
)


async def download_from_extenal_source(update: Update, url: str):
    ydl = yt_dlp.YoutubeDL({
        "format": "worst",
        "outtmpl": "./temp/%(id)s.%(ext)s"
    })
    msg = await update.message.reply_text('Downloading from external source (may take a while)...',
                                          reply_to_message_id=update.message.message_id)

    start_time = time()
    ydl.download(url)

    await msg.edit_text(f'Uploading to file hosting (downloaded in {int(time() - start_time)}s)...')

    info = ydl.extract_info(url)
    file_path = f"./temp/{info['id']}.{info['ext']}"
    url = upload_file(file_path, '')

    await msg.delete()
    await update.message.reply_text(f'Saved! Here is your URL: [{url}]({url})', ParseMode.MARKDOWN,
                                    reply_to_message_id=update.message.message_id)

    unlink(file_path)


async def extsrc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        await download_from_extenal_source(update, context.args[0])
        return ConversationHandler.END
    else:
        await update.message.reply_text("Send an URL and I will try to reupload it to file hosting.")
        return STATES["extsrc_url"]


async def extsrc_continue(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await download_from_extenal_source(update, update.message.text)
    return ConversationHandler.END


async def cancel(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Command cancelled.")
    return ConversationHandler.END


def extsrc_add_handler(app):
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("extsrc", extsrc)],
        states={
            STATES["extsrc_url"]: [MessageHandler(filters.TEXT & ~filters.COMMAND, extsrc_continue)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    ))
