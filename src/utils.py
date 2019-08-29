import logging
import config
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def exception_handler(func):
    def func_wrapper(*args, **kwargs):
        try:
            logger = _get_logger()
            bot = args[0]
            update = args[1]
            func(*args, **kwargs)
        except Exception as ex:
            logger.exception(ex)
            bot.send_message(chat_id=update.message.chat_id, text="Exception: " + str(ex))
            bot.send_message(chat_id=config.get("EXCEPT_MANAGER"), text="Exception: " + str(ex))
    return func_wrapper

def admin_command(func):
    def func_wrapper(*args, **kwargs):
        bot = args[0]
        update = args[1]
        if update.message.from_user.id not in config.get("ADMIN"):
            bot.send_message(chat_id=update.message.chat_id, text="No tenes acceso al comando")
        else:
            func(*args, **kwargs)
    return func_wrapper

def _get_logger():
    logger = logging.getLogger('metegol')
    fh = logging.FileHandler('spam.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger
