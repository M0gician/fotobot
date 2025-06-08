"""Image related helper service."""

from telegram import Update
from telegram import constants

from fotobot.services import photo_handler as ph

async def download_file(update: Update, file_path: str) -> None:
    """Download user uploaded file to ``file_path``."""
    await ph.download_image(update, file_path)


def parse_metadata(file_path: str):
    """Return worker and mimetype after validating the file."""
    mimetype = ph.get_mime(file_path)
    ph.check_mime(mimetype)
    worker = ph.get_worker(file_path)
    return worker, mimetype


def render_caption(worker, style: int):
    """Render caption and extract coordinates/orientation."""
    template = ph.get_template(worker, style)
    caption = ph.get_description(worker, template)
    coordinates = ph.get_coordinates(worker)
    orientation = ph.get_orientation(worker)
    return caption, coordinates, orientation


async def send_response(update: Update, file_path: str, caption: str,
                        coordinates=None, orientation=None) -> None:
    """Send processed image or text back to user."""
    parse_mode = constants.ParseMode.HTML
    await ph.send_msg(update, file_path, caption, parse_mode,
                      coordinates, orientation)
