from logging import getLogger, StreamHandler, FileHandler, Formatter
from logging.handlers import RotatingFileHandler


def my_logger(name, logfile='booya_ping.log', level='INFO', stream=False, rotate=False):
    logger = getLogger(name)
    logger.handlers.clear()

    formatter = Formatter(
        "%(asctime)s %(levelname)s-%(module)s-%(funcName)s-%(lineno)d %(message)s"
    )

    ## stream
    if stream:
        streamHandler = StreamHandler()
        streamHandler.setFormatter(formatter)
        streamHandler.setLevel(level)
        logger.addHandler(streamHandler)

    if rotate:
        fileHandler = RotatingFileHandler(logfile,  encoding='utf-8', maxBytes=10000, backupCount=5)
    else:
        fileHandler = FileHandler(logfile, encoding='utf-8', mode='a')
    fileHandler.setFormatter(formatter)
    fileHandler.setLevel(level)

    logger.addHandler(fileHandler)
    logger.setLevel(level)

    return logger
