from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


import uploader

async def user_introduction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    await update.message.reply_text("Hi! I'm Media Re-uploader Bot. I reupload everything you send me.")

    current_uploader = uploader.get_uploader(update.message.chat_id)
    if current_uploader is not None:
        await update.message.reply_text(f"At the moment, the uploader is {current_uploader.parsed_url().hostname}")
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
