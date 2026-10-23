from telegram import Update
from telegram.ext import ContextTypes

import uploader


async def inline_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    data = query.data
    if data is None or query.from_user.id is None:
        return

    chat_uploader = uploader.get_uploader(query.from_user.id)

    if data.startswith("/setuploader"):
        value = data[13:]

        if value not in uploader.ACCEPTABLE_UPLOADERS:
            await query.edit_message_text(text=f"Unknown uploader value: {value}")
        elif value == "Manual":
            pass
        else:
            uploader.set_uploader(query.from_user.id, uploader.ACCEPTABLE_UPLOADERS[value])
            await query.edit_message_text(text=f"You've set {value} as your uploader. You can now upload files!")
    elif data.startswith("/filedelete") and chat_uploader is not None:
        value = data[12:]

        if uploader.delete_file(chat_uploader, value):
            await query.edit_message_text(text="🗑 Post deleted!")
