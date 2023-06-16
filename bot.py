import logging
import textwrap
from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 5):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    constants
)
from telegram.ext import (
    Application,
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    filters,
    MessageHandler
)

from config import TOKEN
from src.handlers.photo_handler import photo_handler

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

STYLE, DEFAULT, FULL, PRETTY = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""

    start_text = """
    Pick an output format you want to use :\\)
    
    *Default* :
    ——————————
    Camera: Nikon ℤ 8
    Lens: Nikkor ℤ 50mm f/1\\.8 S
    50\\.0 mm, f/2\\.8, 1/250s, ISO 64

    *Full* :
    Make: NIKON CORPORATION
    Model: NIKON D850
    ISO: 64
    ExposureTime: 1/200
    FNumber: 2\\.0
    FocalLength: 105 mm
    DateTimeOriginal: 2017:10:10 12:02:59

    *Pretty* :
    💭:
    ——————————
    📸: NIKON Z fc / 23mm f/1\\.2
    📝: 23\\.0 mm, f/7\\.1, 1/400s, ISO 100
    📅: 2022:07:23 16:37:51
    """
    start_text = textwrap.dedent(start_text)
    reply_keyboard = [["Default", "Full", "Pretty"]]

    await update.message.reply_text(
        start_text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Which format?"
        ),
        parse_mode=constants.ParseMode.MARKDOWN_V2
    )
    return STYLE

async def style(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    style = update.message.text
    await update.message.reply_text(
        "I see\\! Please send me a photo of `\\.jpg/\\.png` as file",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=constants.ParseMode.MARKDOWN_V2
    )
    if style == 'Default':
        return DEFAULT
    elif style == 'Full':
        return FULL
    elif style == 'Pretty':
        return PRETTY
    else:
        return DEFAULT

async def default(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await photo_handler(update, context, DEFAULT)
    return DEFAULT

async def full(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await photo_handler(update, context, FULL)
    return FULL

async def pretty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await photo_handler(update, context, PRETTY)
    return PRETTY


if __name__ == "__main__":
    logger.info("Starting bot...")
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.ALL, start)],
        states={
            STYLE: [MessageHandler(filters.Regex("^(Default|Full|Pretty)$"), style)],
            DEFAULT: [MessageHandler(filters.Document.IMAGE, default)],
            FULL: [MessageHandler(filters.Document.IMAGE, full)],
            PRETTY: [MessageHandler(filters.Document.IMAGE, pretty)],
        },
        fallbacks=[MessageHandler(filters.TEXT, start)],
    )
    application.add_handler(conv_handler)

    application.run_polling()