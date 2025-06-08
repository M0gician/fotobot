import logging

import magic
import uuid
import io
import math
import pillow_avif

from PIL import Image
from telegram import Update, constants
from telegram.ext import ContextTypes
from pillow_heif import register_heif_opener
from config import PHOTO_PATH

from fotobot.exif.exiftoolworker import ExifToolWorker
from fotobot.exif.pillowworker import PillowWorker
from fotobot.exif.exifworker import ExifWorker
from fotobot.exif.styles import Style, get_default_style, get_full_style, get_pretty_style
from fotobot.services.helper import remove_original_doc_from_server, reply_photo, reply_text

SUPPORTED_MIME_LIST = (
    "image/jpeg", "image/png", "image/heic",
    "HEIF/heic", "HEIF/heix", "HEIF/hevc",
    "HEIF/heim", "HEIF/heis", "HEIF/hevm", "HEIF/hevs",
    "HEIF/avif"
)
HEIF_MAPPING = {
    "ftypheic": "HEIF/heic",
    "ftypheix": "HEIF/heix",
    "ftyphevc": "HEIF/hevc",
    "ftypheim": "HEIF/heim",
    "ftypheis": "HEIF/heis",
    "ftyphevm": "HEIF/hevm",
    "ftyphevs": "HEIF/hevs",
    "ftypavif": "HEIF/avif",
}
MAX_IMAGE_DIM = 10000

def get_worker(photo_path: str) -> ExifWorker:
    logging.info("Using Pillow backend...")
    worker = PillowWorker(photo_path)
    if "Unknown" in worker.get_lens():
        logging.info("Switch to ExifTool backend...")
        worker = ExifToolWorker(photo_path)
    return worker

def get_description(worker: ExifWorker, template: str) -> str:
    return worker.get_description(template)

def get_coordinates(worker: ExifWorker) -> (float, float):
    return worker.get_f_latitude_longitude()

def get_orientation(worker: ExifWorker) -> int:
    return worker.get_orientation()

def get_template(worker: ExifWorker, style: int) -> str:
    is_full_frame = worker.get_focal_length() == worker.get_focal_length_in_35mm() or worker.get_focal_length_in_35mm().startswith("Unknown")
    # Deal with combo output by Exiftool
    is_exposure_compensation = not worker.get_exposure_compensation().startswith("Unknown")
    is_metering = not worker.get_metering_mode().startswith("Unknown")
    is_author = not worker.get_author().startswith("Unknown")
    is_title = worker.get_title() != ""
    is_location = not worker.get_location().startswith("Unknown")
    is_country = not worker.get_country().startswith("Unknown")
    is_gps = not worker.get_latitude_longitude().startswith("Unknown")
    is_keywords = not worker.get_keywords().startswith("Unknown")
    is_special = worker.get_focal_length_in_35mm().endswith(')')
    is_unknown = worker.get_aperture().startswith("Unknown") and worker.get_iso().startswith("Unknown") and worker.get_shutter_speed().startswith("Unknown")

    if style == Style.FULL.value:
        return get_full_style(
            is_full_frame, is_exposure_compensation, is_metering,
            is_author, is_title, is_country, is_location, is_gps,
            is_keywords
        )
    elif style == Style.PRETTY.value:
        return get_pretty_style(is_full_frame, is_unknown, is_country, is_location, is_title, is_gps)

    return get_default_style(is_full_frame, is_special, is_unknown, is_country, is_location, is_title, is_gps)


def img_resize(photo_path: str, orientation=1) -> Image.Image:
    img = Image.open(photo_path)
    w, h = img.size
    w_max = MAX_IMAGE_DIM * w // (w+h)
    h_max = MAX_IMAGE_DIM - w_max
    logging.info("Image size: width=%s, height=%s", w, h)
    logging.info("Max Image size: width=%s, height=%s", w_max, h_max)

    img = img.resize((min(w_max, w), min(h_max, h)), Image.Resampling.LANCZOS)
    
    if orientation == 3:
        img = img.rotate(180, expand=True)
    elif orientation == 6:
        img = img.rotate(270, expand=True)
    elif orientation== 8:
        img = img.rotate(90, expand=True)

    return img

def img_to_bytes(image: Image) -> bytes:
    b_img = io.BytesIO()
    image.save(b_img, format="JPEG")
    b_img = b_img.getvalue()
    return b_img

def get_mime(photo_path: str) -> str:
    mime_guesser = magic.Magic(mime=True)
    mimetype = mime_guesser.from_file(photo_path)

    if mimetype == "application/octet-stream":
        with open(photo_path, 'rb') as f:
            f.read(4)
            b_signature = f.read(8)
            signature = b_signature.decode('utf-8')
            if signature in HEIF_MAPPING.keys():
                mimetype = HEIF_MAPPING[signature]
    
    return mimetype if mimetype else "Unknown"

async def download_image(update: Update, photo_path: str) -> None:
    try:
        photo_file = await update.message.effective_attachment.get_file()
        await photo_file.download_to_drive(photo_path)
    except Exception as _:
        raise IOError from _

def check_mime(mimetype: str) -> None:
    try:
        if mimetype not in SUPPORTED_MIME_LIST:
            raise TypeError
        if mimetype == "image/heic" or mimetype.startswith("HEIF"):
            register_heif_opener()
    except TypeError as _:
        raise TypeError from _

async def send_msg(update: Update, photo_path: str, caption: str, parse_mode: str, coordinates=None, img_orientation=None) -> None:
    if caption[-1] != "!":
        if img_orientation is not None:
            img_orientation = 1
        img = img_resize(photo_path, img_orientation)
        b_img = img_to_bytes(img)
        await reply_photo(
            update=update,
            photo=b_img,
            caption=caption,
            parse_mode=parse_mode
        )
        if coordinates is not None:
            lat, lon = coordinates
            if lat and lon and not math.isnan(lat) and not math.isnan(lon):
                await update.message.reply_location(latitude=lat, longitude=lon)
    else:
        await reply_text(
            update=update,
            text=caption,
            parse_mode=parse_mode
        )

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, style: int) -> None:
    logger = logging.getLogger(__name__)
    logging.info("photo_handler started")
    user = update.message.from_user

    photo_path = f"{PHOTO_PATH}/{uuid.uuid4()}_img"
    parse_mode = constants.ParseMode.HTML
    description = ""
    coordinates = None
    orientation = None

    try:
        await download_image(update, photo_path)
        logging.info("Download completed from user %s", user.full_name)

        logging.info("Guessing file type")
        mimetype = get_mime(photo_path)
        check_mime(mimetype)
        logging.info("File MIME type: %s", mimetype)

        logging.info("Parsing EXIF data...")
        worker = get_worker(photo_path)
        template = get_template(worker, style)
        logging.info("Output Style %s...", Style(style).name)
        description = get_description(worker, template)
        coordinates = get_coordinates(worker)
        orientation = get_orientation(worker)
        await send_msg(update, photo_path, description, parse_mode, coordinates, orientation)
        remove_original_doc_from_server(photo_path, logger)
    except IOError as e:
        description = "Cannot download file! (Max File Size: 20MB) Please try again."
        logging.error(description)
        logging.error(e.args)
        await reply_text(update, description, parse_mode)
    except TypeError as e:
        if mimetype == 'Unknown':
            description = "Unknown file type!"
        else:
            description = f"{mimetype} not supported!"
        logging.error(description)
        logging.error(e.args)
        await reply_text(update, description, parse_mode)
        remove_original_doc_from_server(photo_path, logger)
    except Exception as e:
        description = "Cannot parse EXIF data!"
        logging.error(description)
        logging.error(e.args)
        await reply_text(update, description, parse_mode)
        remove_original_doc_from_server(photo_path, logger)

