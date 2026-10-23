from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from extsrc import extsrc_add_handler

import utils
import uploader
import commands


def run():
    cfg = utils.get_configuration()

    uploader.init_uploader_db()

    print("Bot is running...")
    app = ApplicationBuilder().token(cfg['telegram']['token']).build()
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.VIDEO_NOTE |
        filters.VOICE | filters.AUDIO | filters.ANIMATION |
        filters.Document.ALL,
        commands.reupload_file
    ))
    app.add_handler(CommandHandler("start", commands.user_introduction))
    app.add_handler(CallbackQueryHandler(commands.inline_buttons))
    extsrc_add_handler(app)
    app.run_polling()


if __name__ == "__main__":
    run()
