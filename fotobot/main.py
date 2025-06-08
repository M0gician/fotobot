import logging
from config import TOKEN, LOGGING_LEVEL
from fotobot.bot.app import build_app


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=LOGGING_LEVEL,
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting bot...")
    application = build_app(TOKEN)
    application.run_polling()


if __name__ == "__main__":
    main()

