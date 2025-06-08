from os import remove
import logging
import telegram
from telegram import Update
import time

def remove_original_doc_from_server(photo_path, logger):
    """
    Function for removing original file that sent by user with name "image" without extension
    :param logger: Logger from logging package
    :param update: Update from telegram.update package
    """
    logger.info("Preparing for original file deletion on server")
    try:
        remove(photo_path)
        logger.info("Original file successfully removed")
    except Exception as e:
        logger.error("Can't remove original file")
        logger.error(e.args)

def escape(text: str) -> str:
    """Escape string to avoid explosion"""
    try:
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    except AttributeError:
        return 'N/A'

def retry_on_error(wait=0.1, retry=0):
    def decorator(func):
        async def inner(*args, **kwargs):
            i = 0
            while True:
                try:
                    await func(*args, **kwargs)
                    break
                except telegram.error.NetworkError:
                    logging.exception(f"Network Error. Retrying...{i}")
                    i += 1
                    time.sleep(wait)
                    if retry != 0 and i == retry:
                        raise telegram.error.NetworkError
        return inner
    return decorator

@retry_on_error(retry=3)
async def reply_photo(update: Update, photo: bytes, caption: str, parse_mode: str):
    try:
        await update.message.reply_photo(
            photo=photo,
            caption=caption,
            parse_mode=parse_mode
        )
    except Exception as e:
        await update.message.reply_text(
            text=f"Error occurred: {str(e)}"
        )

@retry_on_error(retry=3)
async def reply_text(update: Update, text: str, parse_mode: str):
    try:
        await update.message.reply_text(
            text=text,
            parse_mode=parse_mode
        )
    except Exception as e:
        await update.message.reply_text(
            text=f"Error occurred: {str(e)}"
        )
