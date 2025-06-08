import logging
import textwrap
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    constants
)
from telegram.ext import (
    Application,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler
)
from telegram import __version__ as TG_VER
from fotobot.services.helper import escape
from fotobot.services.photo_handler import photo_handler

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

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

STYLE, DEFAULT, FULL, PRETTY = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""

    style_default = """
    Default

    ——————————
    Camera: Nikon ℤ 8
    Lens: Nikkor ℤ 50mm f/1.8 S
    50.0 mm, f/2.8, 1/250s, ISO 64
    """

    style_full = """
    Full   

    Camera: Canon EOS R5
    Lens: Canon RF 35mm F1.8 MACRO IS STM
    Focal Length: 35.0 mm
    Aperture: f/11.0
    Shutter Speed: 1/125s
    ISO: ISO 200
    Exposure Compensation: -2/3 EV
    DateTime Original: 2020:07:19 12:18:02
    """

    style_pretty = """
    Pretty 

    💭:
    ——————————
    📸: NIKON Z fc / 23mm f/1.2
    📝: 23.0 mm, f/7.1, 1/400s, ISO 100
    📅: 2022:07:23 16:37:51
    """
    
    reply_keyboard = [[
        escape(textwrap.dedent(style_default)), 
        escape(textwrap.dedent(style_full)), 
        escape(textwrap.dedent(style_pretty))
    ]]

    await update.message.reply_text(
        escape("Pick an output format you want to use :)"),
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Which format?"
        ),
        parse_mode=constants.ParseMode.HTML
    )
    return STYLE

async def style(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    style = update.message.text[:8].strip()
    await update.message.reply_text(
        "I see! Please send me a photo of <code>.jpg/.png/.heif/.avif</code> as file",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=constants.ParseMode.HTML
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


def build_app(token: str) -> Application:
    application = (
        Application.builder()
        .token(token)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.ALL, start)],
        states={
            STYLE: [MessageHandler(filters.Regex("^(Default|Full|Pretty)"), style)],
            DEFAULT: [MessageHandler(filters.Document.IMAGE, default)],
            FULL: [MessageHandler(filters.Document.IMAGE, full)],
            PRETTY: [MessageHandler(filters.Document.IMAGE, pretty)],
        },
        fallbacks=[MessageHandler(filters.TEXT, start)],
    )
    application.add_handler(conv_handler)
    return application
