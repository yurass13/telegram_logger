import atexit
import json
import logging.config
import logging.handlers
import pathlib
import time


logger = logging.getLogger('test_app')


def setup_logging():
    config_file = pathlib.Path("./log_config.json")

    with open(config_file) as file:
        config = json.load(file)

    logging.config.dictConfig(config=config)

    handler = logging.getHandlerByName('queue_handler')

    if handler is not None:
        handler.listener.start()
        atexit.register(handler.listener.stop)


def main():
    setup_logging()
    # logging.basicConfig(level="INFO")
    logger.debug('Debug')
    logger.info("Info")
    logger.warning("Warning")
    logger.error("Error", extra={'some_extra_param': 'value'})
    logger.critical("Crit")
    logger.fatal('Я упал')
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("Exception")


if __name__ == "__main__":
    main()
