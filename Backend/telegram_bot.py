import os
import django
import environ
from django.conf import settings
env = environ.Env()
environ.Env.read_env(".env")
os.environ['DJANGO_SETTINGS_MODULE'] = f"tma_backend.settings.{env.str('DJANGO_ENVIRONMENT', default='development')}"

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import *

# Handler for text messages
async def handle_message(update, context):
    text = str(update.message.text).lower()
    await update.message.reply_text(f"Hi {update.message.chat.first_name}")

# Handler for the /start command
async def start(update, context):
    # Create buttons
    keyboard = [
        [InlineKeyboardButton("Start Game", url="t.me/masterversess_bot/Masterverses")],
        [InlineKeyboardButton("Join Community", url="t.me/Master_verses")],
        [InlineKeyboardButton("Earn Rewards", switch_inline_query=f"t.me/masterversess_bot/Masterverses?startapp={update.message.chat.id}")],
        [InlineKeyboardButton("Launch Masterverses", url="https://masterverses.com/")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send a message with text and buttons
    message = (
        f"""
Hey, {update.message.chat.first_name}! 
Welcome to Masterverses! ✨

Tap, pray, and earn rewards with daily tasks, airdrops, referrals, and more. 🙏 Your Masterverses points will soon convert into tokens for deeper spiritual engagement. Keep tapping, earning, and growing! 🕊️

By using this bot, you confirm you've read and agreed to our Privacy Policy.

Let’s start your spiritual journey! 🌟
    """
)
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')


async def about(update, context):
    await update.message.reply_text("Masterverses - your go-to platform for connecting with your spiritual side anytime, anywhere. Whether at home, work, or on the move, Masterverses allows you to pray and engage in self-reflection whenever it suits you. It's time to embrace a more mindful, balanced lifestyle with Masterverses.")


# CallbackQueryHandler to handle button clicks
async def button_handler(update, context):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    if query.data == "start_game":
        # Simulate starting a game
        await query.edit_message_text("🎮 Starting the game... Get ready!")
    elif query.data == "help":
        # Provide additional help
        await query.edit_message_text(
            "Here is how you can use this bot:\n\n"
            "1. **Visit X.com**: Explore the site for more info.\n"
            "2. **Start Game**: Play an interactive game.\n"
            "3. **Ask Questions**: Type your queries for answers."
        )

if __name__ == '__main__':
    # Initialize the Application
    application = Application.builder().token(settings.TELEGRAM_BOT_API).build()

    # Add a CommandHandler for /start
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("about", about))
    # Add a MessageHandler for text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling
    application.run_polling()


