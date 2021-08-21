import logging
from logging.handlers import TimedRotatingFileHandler

import telebot


def is_valid_number(value: str, min_val: int = 0, max_val: int = None) -> bool:
    if not value.isdigit():
        return False
    if max_val is not None and min_val <= int(value) <= max_val:
        return True
    if max_val is None and int(value) >= min_val:
        return True
    return False


def is_valid_float(value: str):
    if value.replace('.', '').isdigit():
        return True
    return False


def configure_app_logger(name: str):
    formatter_file = logging.Formatter(fmt="%(asctime)s | (%(filename)s:%(lineno)d | funcName: %(funcName)s)"
                                           " | %(levelname)s | %(message)s")
    formatter_cons = logging.Formatter(fmt="%(asctime)s | funcName: %(funcName)s | %(levelname)s | %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter_cons)
    console_handler.setLevel('INFO')

    file_handler = TimedRotatingFileHandler('logs/app.log', when='h', interval=24, backupCount=5)
    file_handler.setFormatter(formatter_file)
    file_handler.setLevel('DEBUG')

    logger = logging.getLogger(name)
    logger.setLevel('DEBUG')
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def configure_telebot_logger():
    formatter = logging.Formatter(
        fmt='%(asctime)s (%(filename)s:%(lineno)d %(threadName)s) %(levelname)s - %(name)s: "%(message)s"')
    file_handler = TimedRotatingFileHandler('logs/telebot.log', when='h', interval=24, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel('DEBUG')

    logger = telebot.logger
    telebot.logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    logger.addHandler(file_handler)

    return logger
