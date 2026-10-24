from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


import uploader
import utils

async def user_introduction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    await update.message.reply_text("Hi! I'm Media Re-uploader Bot. I reupload everything you send me.")

    current_uploader = uploader.get_uploader(update.message.chat_id)
    if current_uploader is not None:
        await update.message.reply_text(f"At the moment, the uploader is {current_uploader.parsed_url().hostname}")
        return

    await update.message.reply_text("To begin, let's choose a file uploader:", reply_markup=InlineKeyboardMarkup(utils.uploaders_to_buttons()))

async def edit_uploader(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return

    text = "⚙️ File uploader configuration\n\n"
    keyboard = []

    chat_uploader = uploader.get_uploader(update.message.chat_id)
    if chat_uploader is None:
        text += "You don't have file uploader. Set one!"
        keyboard = utils.uploaders_to_buttons()
    else:
        text += "Your file uploader: " + chat_uploader.base_url()
        keyboard.append([InlineKeyboardButton("Reset", callback_data="/resetuploader")])

    await update.message.reply_text(text=text, reply_to_message_id=update.message.id, reply_markup=InlineKeyboardMarkup(keyboard))
