import os
import logging
import html
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv
from main import get_matches_info, get_overall_stats, format_matches
from fc_clubs_api.schemas import Platform, ClubSearchInput  # Added ClubSearchInput
from fc_clubs_api.api import EAFCApiService  # Added EAFCApiService
from telegram.error import TelegramError
from database import add_user, remove_user, get_all_users
from fc_clubs_api.models import OverallStats  # Import the OverallStats model
# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)

# Retrieve the bot token from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    logger.error(
        "TELEGRAM_BOT_TOKEN is not set. Please set it in the environment variables."
    )
    exit(1)

def escape_text_html(text: str) -> str:
    return html.escape(text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    add_user(user_id)  # Save the user ID
    welcome_message = (
        "👋 Hello! I'm the FC Clubs Bot.\n\n"
        "Send me the name of a club (e.g., <b>Metallist</b>) and I'll provide you with the latest match information."
    )
    await update.message.reply_text(welcome_message, parse_mode="HTML")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_message = (
        "📖 <b>Help</b>\n\n"
        "To get match information for a club, simply send the club's name. For example:\n"
        "<code>Metallist</code>\n\n"
        "Ensure that the club name is spelled correctly."
    )
    await update.message.reply_text(help_message, parse_mode="HTML")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    remove_user(user_id)  # Remove the user ID
    farewell_message = "👋 You've been unsubscribed from FC Clubs Bot notifications."
    await update.message.reply_text(farewell_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    club_name = update.message.text.strip()
    if not club_name:
        await update.message.reply_text("❌ Please provide a valid club name.")
        return

    await update.message.reply_text(
        f"🔍 Fetching match information for <b>{escape_text_html(club_name)}</b>...",
        parse_mode="HTML",
    )

    platform = Platform.COMMON_GEN5  # Adjust based on your platform enums

    try:
        # Fetch matches information
        matches_info = get_matches_info(club_name, platform)

        if not matches_info:
            await update.message.reply_text("⚠️ No matches found for the specified club.")
            return

        # Search for the club to get its ID
        api_service = EAFCApiService()
        input_data = ClubSearchInput(clubName=club_name, platform=platform)
        search_response = api_service.search_club(input_data)

        if not search_response:
            await update.message.reply_text("⚠️ No clubs found matching the search criteria.")
            return

        selected_club = search_response[0]
        selected_club_id = selected_club.clubId

        # Fetch overall stats using the club's ID
        overall_stats = get_overall_stats(selected_club_id, platform)

        if not overall_stats:
            await update.message.reply_text("⚠️ No overall stats found for the specified club.")
            return

    except Exception as e:
        logger.error(f"Error fetching matches or stats: {e}")
        await update.message.reply_text(
            "❌ An error occurred while fetching match information. Please try again later."
        )
        return

    # Format the matches with indicators and separators, including overall stats
    formatted_text = format_matches(matches_info, club_name, overall_stats)

    # Escape the text for HTML
    escaped_text = formatted_text  # Assuming format_matches returns HTML-formatted text

    logger.debug(f"Escaped Text (HTML): {escaped_text}")

    if len(escaped_text) > 4000:
        # Send as a document if text is too long
        with open("matches_output.txt", "w", encoding="utf-8") as file:
            file.write(formatted_text)
        with open("matches_output.txt", "rb") as file:
            await update.message.reply_document(
                file,
                filename="matches_output.txt",
                caption="📄 Here is the match information:",
            )
        os.remove("matches_output.txt")
    else:
        try:
            await update.message.reply_text(
                escaped_text, parse_mode="HTML", disable_web_page_preview=True
            )
        except TelegramError as e:
            logger.error(f"Failed to send message: {e}")
            await update.message.reply_text(
                "❌ An error occurred while sending the message. Please try again later."
            )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        try:
            await update.message.reply_text(
                "❌ An unexpected error occurred. Please try again later."
            )
        except TelegramError as e:
            logger.error(f"Failed to send error message: {e}")

def main():
    from database import initialize_db
    from fc_clubs_api.api import EAFCApiService  # Ensure EAFCApiService is accessible

    initialize_db()  # Initialize the database

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Register the error handler
    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
