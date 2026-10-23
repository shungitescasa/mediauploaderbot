import tempfile
import traceback

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

import uploader

async def download_telegram_file(update, file_id, file_directory):
    file = await update.get_bot().get_file(file_id)
    file_extension = ""

    if file.file_path is not None:
        file_extension = f".{file.file_path.split('.')[-1]}".lower()

    file_path = f"{file_directory}/{file_id.file_unique_id}{file_extension}"
    await file.download_to_drive(file_path)
    return file_path


async def reupload_file(update: Update, _: CallbackContext) -> None:
    if update.message is None:
        return

    chat_uploader = uploader.get_uploader(update.message.chat_id)
    if chat_uploader is None:
        await update.message.reply_text("File uploader must be set before uploading any files!")
        return

    message = await update.message.reply_text("⏳ Downloading...", reply_to_message_id=update.message.id)

    file_directory = tempfile.mkdtemp(prefix="mubtelegramfiles_")

    attachments = [
        update.message.video,
        update.message.video_note,
        update.message.voice,
        update.message.audio,
        update.message.animation,
        update.message.document
    ]

    if len(update.message.photo) != 0:
        attachments.append(update.message.photo[-1])

    processed_files = 0
    file_counter = 0
    failed_files = 0

    for attachment in attachments:
        if attachment is not None:
            processed_files += 1
            try:
                await download_telegram_file(update, attachment, file_directory)
                file_counter += 1
            except Exception as e:
                failed_files += 1
                traceback.print_tb(e.__traceback__)

            await message.edit_text(f"⏳ Downloading... ({file_counter} finished files; {failed_files} failed files)")

    if file_counter == 0:
        await message.edit_text("❌ No files were downloaded")
        return

    await message.edit_text(f"⏳ Re-uploading {file_counter} file(s)...")

    try:
        image_link, deletion_link = uploader.upload_directory(chat_uploader, file_directory)

        keyboard = []
        if deletion_link is not None:
            keyboard.append([InlineKeyboardButton("Delete", callback_data="/filedelete " + deletion_link)])

        await message.delete()
        await update.message.reply_text(f"✅ Saved! Here is your URL: [{image_link}]({image_link})",
            parse_mode=ParseMode.MARKDOWN,
            reply_to_message_id=update.message.message_id,
            reply_markup=InlineKeyboardMarkup(keyboard))
    except RuntimeError as e:
        await message.edit_text(f"🛑 {str(e)}")
    except Exception as e:
        traceback.print_tb(e.__traceback__)
        await update.message.reply_text(f"🛑 Error occurred while re-uploading files: {str(e)}", reply_to_message_id=update.message.message_id)
