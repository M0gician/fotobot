from logging import getLogger
from os import remove

import magic
import uuid
from PIL import Image
from telegram import Update
from telegram.ext import ContextTypes
from config import PHOTO_PATH

from src.exifutils.exiftoolworker import ExifToolWorker
from src.exifutils.exifworker import ExifWorker
from src.exifutils.styles import Style, DEFAULT_STYLE, FULL_INFO_STYLE, PRETTY_STYLE
from src.handlers.helper import remove_original_doc_from_server

SUPPORTED_MIME_LIST = ("image/jpeg", "image/png")


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, style: int) -> str:
    logger = getLogger()

    logger.info("photo_handler started")
    user = update.message.from_user
    photo_path = f"{PHOTO_PATH}/{uuid.uuid4()}_img"
    photo_file = await update.message.effective_attachment.get_file()
    await photo_file.download_to_drive(photo_path)
    logger.info(f"Download completed from user {user.full_name}")

    logger.info("Guessing file type")
    mime_guesser = magic.Magic(mime=True)
    mimetype = mime_guesser.from_file(photo_path)
    description = ""

    if mimetype is None:
        logger.error("Cannot guess file type!")

        try:
            logger.info("Preparing for file deletion from server (kind guess)")
            remove("documents/image")
        except Exception as e:
            logger.error("Can't remove file (kind guess)")
            logger.error(e.args)
        description = "Unknown file type!"

    logger.info(f"File MIME type: {mimetype}")

    if mimetype not in SUPPORTED_MIME_LIST:
        logger.info(f"{mimetype} not supported!")
        logger.info("Removing file...")
        try:
            remove("documents/image")
        except Exception as e:
            logger.error("Can't remove file")
            logger.error(e.args)
        description = f"{mimetype} not supported!"
    else:
        logger.info("Parsing EXIF data...")
        try:
            worker = ExifWorker(photo_path)
            output_style = DEFAULT_STYLE
            if style == Style.FULL.value:
                output_style = FULL_INFO_STYLE
            elif style == Style.PRETTY.value:
                output_style = PRETTY_STYLE
            logger.info(f"Output Style {Style(style).name}...")
            description = worker.get_description(output_style)
            remove_original_doc_from_server(photo_path, logger)
        except Exception as e:
            logger.error("Cannot parse EXIF data!")
            logger.error(e.args)
            description = "Cannot parse EXIF data!"
            remove_original_doc_from_server(photo_path, logger)

    await update.message.reply_text(description)