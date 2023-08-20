import logging
from os import remove

import magic
import uuid
import io
import sys

from PIL import Image
from telegram import Update, constants
from telegram.ext import ContextTypes
from config import PHOTO_PATH

from src.exifutils.exiftoolworker import ExifToolWorker
from src.exifutils.pillowworker import PillowWorker
from src.exifutils.styles import Style, DEFAULT_STYLE, DEFAULT_STYLE_FF, FULL_INFO_STYLE, PRETTY_STYLE, PRETTY_STYLE_FF
from src.handlers.helper import remove_original_doc_from_server

SUPPORTED_MIME_LIST = ("image/jpeg", "image/png")
MAX_IMAGE_DIM = 10000

def get_description(photo_path: str, style: Style) -> str:
    logging.info("Using Pillow backend...")
    worker = PillowWorker(photo_path)
    if "Unknown" in worker.get_lens():
        logging.info("Switch to ExifTool backend...")
        worker = ExifToolWorker(photo_path)
    return worker.get_description(style)

def img_resize(photo_path: str) -> Image.Image:
    img = Image.open(photo_path)
    w, h = img.size
    w_max = MAX_IMAGE_DIM * w // (w+h)
    h_max = MAX_IMAGE_DIM - w_max
    logging.info(f"Image size: width={w}, height={h}")
    logging.info(f"Max Image size: width={w_max}, height={h_max}")

    img = img.resize((min(w_max, w), min(h_max, h)), Image.Resampling.LANCZOS)
    return img

def img_to_bytes(image: Image) -> bytes:
    b_img = io.BytesIO()
    image.save(b_img, format="JPEG")
    b_img = b_img.getvalue()
    return b_img

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

        await update.message.reply_text(
            text=description,
            parse_mode=constants.ParseMode.HTML
        )
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
        except Exception as e:
            logging.error("Cannot parse EXIF data!")
            logging.error(e.args)
            description = "Cannot parse EXIF data!"

        img = img_resize(photo_path)
        b_img = img_to_bytes(img)
        await update.message.reply_photo(
            photo=b_img,
            caption=description,
            parse_mode=constants.ParseMode.HTML
        )
        remove_original_doc_from_server(photo_path, logger)
    return
