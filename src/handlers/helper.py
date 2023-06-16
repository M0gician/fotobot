from os import remove

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
