# -*- coding: utf-8; -*-
import logging
import config
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import redis
import uuid

def redis_init():
    return redis.Redis(host=config.get("REDIS_HOST"), port=config.get("REDIS_PORT"), db=0)


def redis_set(value):
    uid = str(uuid.uuid4())
    r = redis_init()
    r.set(uid, value, ex=300)
    return uid


def redis_get(uid):
    r = redis_init()
    return r.get(uid)


def exception_handler(func):
    def func_wrapper(*args, **kwargs):
        try:
            logger = _get_logger()
            bot = args[0]
            update = args[1]
            func(*args, **kwargs)
        except Exception as ex:
            logger.exception(ex)
            bot.send_message(chat_id=config.get("EXCEPT_MANAGER"), text="Exception: " + str(ex))
            bot.send_message(chat_id=update.message.chat_id, text="Exception: " + str(ex))
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


def group_validator(func):
    def func_wrapper(*args, **kwargs):
        bot = args[0]
        update = args[1]
        if update.message.chat.id not in config.get("GROUPS"):
            bot.send_message(chat_id=update.message.chat_id, text="Grupo invalido")
        else:
            func(*args, **kwargs)
    return func_wrapper


def _get_logger():
    logger = logging.getLogger('metegol')
    fh = logging.FileHandler('spam.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.setLevel('INFO')
    logger.addHandler(fh)

    return logger


def _calculate_elo(a_elo, b_elo, a_goals, b_goals, goal_multiplier=None):
    expected_a = 1 / (1 + (10**((b_elo-a_elo)/400)))
    expected_b = 1 / (1 + (10**((a_elo-b_elo)/400)))

    goal_multiplier = _get_goal_multiplier(a_goals,b_goals)

    offset_a = int(round(25 * goal_multiplier * (int(a_goals > b_goals) - expected_a)))
    offset_b = int(round(25 * goal_multiplier * (int(b_goals > a_goals) - expected_b)))

    return offset_a, offset_b


def _get_goal_multiplier(goals_a,goals_b,multiplier_modifier=None):
    if not multiplier_modifier:
        multiplier_modifier = config.get("MULTIPLIER")
    goals_diference = abs(goals_a-goals_b)
    return multiplier_modifier*goals_diference