#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""

"""

from functools import wraps

import logging

from telegram import ForceReply, Update, Bot
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import wget
import os
import datetime

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def send_action(action):
    """Sends `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        async def command_func(update, context, *args, **kwargs):
            await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return await func(update, context,  *args, **kwargs)
        return command_func

    return decorator

async def getImage(url, save_as):
    if os.path.exists(save_as):
        os.remove(save_as) # if exist, remove it directly
    wget.download(url, save_as)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE)-> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!, I can respond to your commands. Type /garden or /tower to see a picture.",
        reply_markup=ForceReply(selective=True),
    )

@send_action(ChatAction.TYPING)
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    user = update.effective_user
    await update.message.reply_text(
        rf"Hi {user.first_name}!, I can respond to your commands. Type /garden or /tower to see a picture.")

@send_action(ChatAction.UPLOAD_PHOTO)
async def tower_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    image_url = 'http://192.168.0.157/cgi-bin/api.cgi?cmd=Snap&channel=0&rs=wuuPhkmUCeI9WG7C&user=admin&password=aabbcc112233'
    save_as = './tower.jpeg'
    await getImage(image_url, save_as)
    await context.bot.sendPhoto(chat_id=update.effective_chat.id, photo=open(save_as, 'rb'))

@send_action(ChatAction.UPLOAD_PHOTO)
async def garden_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    image_url = 'http://192.168.0.108/cgi-bin/api.cgi?cmd=Snap&channel=0&rs=wuuPhkmUCeI9WG7C&user=admin&password=aabbcc112233'
    save_as = './garden.jpeg'
    await getImage(image_url, save_as)
    await context.bot.sendPhoto(chat_id=update.effective_chat.id, photo=open(save_as, 'rb'))

#@send_action(ChatAction.UPLOAD_PHOTO)
#async def docks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#    image_url = 'http://192.168.0.108/cgi-bin/api.cgi?cmd=Snap&channel=0&rs=wuuPhkmUCeI9WG7C&user=admin&password=aabbcc112233'
#    save_as = './docks.jpeg'
#    getImage(image_url, save_as)
#    await context.bot.sendPhoto(chat_id=update.effective_chat.id, photo=open(save_as, 'rb'))

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("7829431869:AAGrVnrwCf4IF3ULbEW_GcahXTugOmV25qU").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tower", tower_command))
    application.add_handler(CommandHandler("garden", garden_command))
#    application.add_handler(CommandHandler("docks", docks_command))

    # on non command i.e message - echo the message on Telegram
    #application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
