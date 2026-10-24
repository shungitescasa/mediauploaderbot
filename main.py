from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters

import utils
import uploader
import commands


def run():
    cfg = utils.get_configuration()

    uploader.init_uploader_db()

    app = ApplicationBuilder().token(cfg['telegram']['token']).build()
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.VIDEO_NOTE |
        filters.VOICE | filters.AUDIO | filters.ANIMATION |
        filters.Document.ALL,
        commands.reupload_file
    ))
    app.add_handler(CommandHandler("start", commands.user_introduction))
    app.add_handler(CommandHandler("url", commands.reupload_url))
    app.add_handler(CommandHandler("edit", commands.edit_uploader))
    app.add_handler(CallbackQueryHandler(commands.inline_buttons))

    print("Bot is ready to re-upload files...")

    app.run_polling()


if __name__ == "__main__":
    run()
