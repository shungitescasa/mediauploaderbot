from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from urllib.parse import urlparse


import uploader

async def user_introduction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    await update.message.reply_text("Hi! I'm Media Re-uploader Bot. I reupload everything you send me.")

    current_uploader = uploader.get_uploader(update.message.chat_id)
    if current_uploader is not None:
        url = urlparse(current_uploader.url)
        await update.message.reply_text(f"At the moment, the uploader is {url.hostname}")
        return

    keyboard = []
    row = []

    for k in uploader.ACCEPTABLE_UPLOADERS:
        row.append(InlineKeyboardButton(k, callback_data="/setuploader " + k.lower()))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if len(row) != 0:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("To begin, let's choose a file uploader:", reply_markup=reply_markup)

async def inline_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    data = query.data
    if data is None or query.from_user.id is None:
        return

    if data.startswith("/setuploader"):
        value = data[13:]

        if value not in uploader.ACCEPTABLE_UPLOADERS:
            await query.edit_message_text(text=f"Unknown uploader value: {value}")
        elif value == "Manual":
            pass
        else:
            uploader.set_uploader(query.from_user.id, uploader.ACCEPTABLE_UPLOADERS[value])
            await query.edit_message_text(text=f"You've set {value} as your uploader. You can now upload files!")
