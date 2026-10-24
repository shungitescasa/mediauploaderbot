import tempfile
import time
import traceback

from telegram import CopyTextButton, InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext
import yt_dlp

import uploader
import utils

async def reupload_directory(message: Message, chat_uploader: uploader.UploaderData, file_directory: str, update: Update, ctx: CallbackContext) -> None:
    if update.message is None:
        return

    image_link = None
    deletion_link = None

    attempts = 0
    exception = None

    while attempts < 3:
        try:
            image_link, deletion_link = uploader.upload_directory(chat_uploader, file_directory)
            break
        except Exception as e:
            exception = e
        attempts += 1
        time.sleep(2)

    if image_link == None:
        text = "🛑 Error occurred while re-uploading files"
        if exception is not None:
            traceback.print_tb(exception.__traceback__)
            text += ": " + str(exception)
        await message.delete()
        await update.message.reply_text(text, reply_to_message_id=update.message.message_id)
        return

    row = [
        InlineKeyboardButton(
            "Copy link",
            copy_text=CopyTextButton(text=image_link),
            style="success"
        )
    ]

    if deletion_link is not None:
        row.append(InlineKeyboardButton("Delete", callback_data="/filedelete " + deletion_link, style="danger"))

    await message.delete()
    await update.message.reply_text(f"✅ Saved! Here is your URL: [{image_link}]({image_link})",
        parse_mode=ParseMode.MARKDOWN,
        reply_to_message_id=update.message.message_id,
        reply_markup=InlineKeyboardMarkup([row]))

async def download_telegram_file(update, file_id, file_directory):
    file = await update.get_bot().get_file(file_id)
    file_extension = ""

    if file.file_path is not None:
        file_extension = f".{file.file_path.split('.')[-1]}".lower()

    file_path = f"{file_directory}/{file_id.file_unique_id}{file_extension}"
    await file.download_to_drive(file_path)
    return file_path


async def reupload_file(update: Update, ctx: CallbackContext) -> None:
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

    attachments = [x for x in attachments if x is not None]

    # gif adds two attachments: Animation and Document, so we have to filter them by unique id
    unique_attachments = {}
    for attachment in attachments:
        if attachment is None:
            continue

        file_id = getattr(attachment, "file_unique_id", None)
        key = file_id if file_id else id(attachment)
        unique_attachments[key] = attachment

    attachments[:] = unique_attachments.values()

    processed_files = 0
    file_counter = 0
    failed_files = 0
    attempts = 0

    while True:
        for attachment in attachments.copy():
            processed_files += 1
            try:
                await download_telegram_file(update, attachment, file_directory)
                attachments.remove(attachment)
                file_counter += 1
            except Exception as e:
                failed_files += 1
                traceback.print_tb(e.__traceback__)

        if processed_files == 0 or len(attachments) == 0 or attempts > 5:
            break

        attempts += 1
        time.sleep(1)

    if file_counter == 0:
        await message.edit_text("❌ No files were downloaded. Please try again later!")
        return

    await message.edit_text(f"⏳ Re-uploading {file_counter} file(s)...")
    await reupload_directory(message, chat_uploader, file_directory, update, ctx)


async def reupload_url(update: Update, ctx: CallbackContext) -> None:
    if update.message is None or ctx.args is None:
        return

    chat_uploader = uploader.get_uploader(update.message.chat_id)
    if chat_uploader is None:
        await update.message.reply_text("🛑 File uploader must be set before uploading any files!", reply_to_message_id=update.message.id)
        return

    if len(ctx.args) != 1:
        await update.message.reply_text("🛑 Along with the command, you need to provide a URL (e.g. YouTube, X/Twitter, Tiktok).", reply_to_message_id=update.message.id)
        return

    directory = tempfile.mkdtemp(prefix="mubexternalfiles_")

    cfg = utils.get_configuration()
    ydl_cfg = None

    if 'yt_dlp' in cfg:
        c = cfg['yt_dlp']

        o = [
            "-o", directory + "/%(id)s.%(ext)s",
            "--no-playlist",
            "--merge-output-format", "mp4",
            "--socket-timeout", "15",
            "--retries", "3",
            "--fragment-retries", "3",
            "--extractor-retries", "2",
            "--concurrent-fragments", "4",
            "--max-filesize", "100M",
            "--no-write-thumbnail",
            "--no-write-info-json",
            "--no-write-subs",
            "--no-write-auto-subs",
            "--quiet",
            "--no-warnings",
            "--no-progress",
            "--no-cache-dir",
        ]

        if 'cookies' in c:
            o.append('--cookies')
            o.append(c['cookies'])

        if 'cookiebrowser' in c:
            o.append('--cookies-from-browser')
            o.append(c['cookiebrowser'])

        ydl_cfg = yt_dlp.parse_options(o)

    if ydl_cfg is None:
        await update.message.reply_text("🛑 External Source Downloader is not configured on this instance. Please try again later!", reply_to_message_id=update.message.id)
        return

    ydl_cfg = ydl_cfg.ydl_opts

    ydl = yt_dlp.YoutubeDL(ydl_cfg)

    message = await update.message.reply_text("⏳ Downloading from URL (may take a while)...", reply_to_message_id=update.message.message_id)

    start_time = time.time()
    try:
        ydl.download(ctx.args[0])
    except Exception as e:
        traceback.print_tb(e.__traceback__)
        await message.delete()
        await update.message.reply_text(f"🛑 Failed to download a file. Please try again later!", reply_to_message_id=update.message.id)
        return

    await message.edit_text(f'⏳ Re-uploading (downloaded in {int(time.time() - start_time)}s)...')

    await reupload_directory(message, chat_uploader, directory, update, ctx)
