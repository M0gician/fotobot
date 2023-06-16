import logging
from os import remove

import magic
import uuid
import math
from telegram import Update, constants
from telegram.ext import ContextTypes
from config import PHOTO_PATH

from src.exifutils.exiftoolworker import ExifToolWorker
from src.exifutils.pillowworker import PillowWorker
from src.exifutils.styles import Style, DEFAULT_STYLE, DEFAULT_STYLE_FF, FULL_INFO_STYLE, PRETTY_STYLE, PRETTY_STYLE_FF
from src.handlers.helper import remove_original_doc_from_server

SUPPORTED_MIME_LIST = ("image/jpeg", "image/png")

def get_description(photo_path: str, style: Style) -> str:
    logging.info("Using Pillow backend...")
    worker = PillowWorker(photo_path)
    if "Unknown" in worker.get_lens():
        logging.info("Switch to ExifTool backend...")
        worker = ExifToolWorker(photo_path)
    return worker.get_description(style)


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, style: int) -> None:
    logger = logging.getLogger(__name__)
    logging.info("photo_handler started")
    user = update.message.from_user
    photo_path = f"{PHOTO_PATH}/{uuid.uuid4()}_img"
    try:
        photo_file = await update.message.effective_attachment.get_file()
        await photo_file.download_to_drive(photo_path)
    except Exception as e:
        logging.error("Cannot download file!")
        logging.error(e.args)
        await update.message.reply_text("Cannot download file! (Max File Size: 20MB) Please try again.")
        return
    logging.info(f"Download completed from user {user.full_name}")

    logging.info("Guessing file type")
    mime_guesser = magic.Magic(mime=True)
    mimetype = mime_guesser.from_file(photo_path)
    description = ""

    if mimetype is None:
        logging.error("Cannot guess file type!")

        try:
            logging.info("Preparing for file deletion from server (kind guess)")
            remove("documents/image")
        except Exception as e:
            logging.error("Can't remove file (kind guess)")
            logging.error(e.args)
        description = "Unknown file type!"

    logging.info(f"File MIME type: {mimetype}")

    if mimetype not in SUPPORTED_MIME_LIST:
        logging.info(f"{mimetype} not supported!")
        logging.info("Removing file...")
        try:
            remove("documents/image")
        except Exception as e:
            logging.error("Can't remove file")
            logging.error(e.args)
        description = f"{mimetype} not supported!"
    else:
        logging.info("Parsing EXIF data...")
        try:
            output_style = DEFAULT_STYLE
            if style == Style.FULL.value:
                output_style = FULL_INFO_STYLE
            elif style == Style.PRETTY.value:
                output_style = PRETTY_STYLE
            logging.info(f"Output Style {Style(style).name}...")
            description = get_description(photo_path, output_style)
            remove_original_doc_from_server(photo_path, logger)
        except Exception as e:
            logging.error("Cannot parse EXIF data!")
            logging.error(e.args)
            description = "Cannot parse EXIF data!"
            remove_original_doc_from_server(photo_path, logger)

    await update.message.reply_text(description, parse_mode=constants.ParseMode.HTML)
    return
