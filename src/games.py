# -*- coding: utf-8; -*-
from src import mongoConnection as mongo
import config
from src.utils import exception_handler, admin_command, redis_set, redis_get, _calculate_elo, group_validator
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import json
from copy import deepcopy
from src import weekly


@group_validator
@exception_handler
def submit(bot, update):
    users = mongo.find(config.get("MAIN_DB"), config.get("PLAYERS_COLLECTION"), {
                       "code": {"$ne": str(update.message.from_user.id)}})

    keyboard = []
    for user in users:
        data = {
            "own": {
                "code": [str(update.message.from_user.id)],
                "name": [str(update.message.from_user.username)]
            },
            "opponent": {
                "code": [str(user["code"])],
                "name": [str(user["username"])]
            }
        }
        uid = redis_set(json.dumps(data))
        keyboard.append([InlineKeyboardButton(
            user["username"], callback_data="game_submit&"+uid)])

    keyboard.append([InlineKeyboardButton("Cancelar", callback_data="cancelar")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(chat_id=update.message.chat_id,
                     text='Seleccioná oponente:', reply_markup=reply_markup)


@group_validator
@exception_handler
def submit_dobles(bot, update):
    users = mongo.find(config.get("MAIN_DB"), config.get("PLAYERS_COLLECTION"), {
                       "code": {"$ne": str(update.message.from_user.id)}})

    keyboard = []
    for user in users:
        if user["code"] != str(update.message.from_user.id):
            data = {
                "own": {
                    "code": [str(update.message.from_user.id), str(user["code"])],
                    "name": [str(update.message.from_user.username), str(user["username"])]
                },
                "opponent": {
                    "code": [],
                    "name": []
                }
            }
            uid = redis_set(json.dumps(data))
            keyboard.append([InlineKeyboardButton(
                user["username"], callback_data="game_dobles1&"+uid)])

    keyboard.append([InlineKeyboardButton("Cancelar", callback_data="cancelar")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(chat_id=update.message.chat_id,
                     text='Seleccioná compañero:', reply_markup=reply_markup)


def _submit_dobles_oponentes1(bot, data, chat_id):
    data = json.loads(redis_get(data))
    users = mongo.find(config.get("MAIN_DB"), config.get("PLAYERS_COLLECTION"), {
                       "code": {"$nin": data["own"]["code"]}})

    keyboard = []
    for user in users:
        tmp = deepcopy(data)
        tmp["opponent"]["code"].append(user["code"])
        tmp["opponent"]["name"].append(user["username"])
        uid = redis_set(json.dumps(tmp))
        keyboard.append([InlineKeyboardButton(
            user["username"], callback_data="game_dobles2&"+uid)])

    keyboard.append([InlineKeyboardButton("Cancelar", callback_data="cancelar")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(
        chat_id=chat_id, text='Seleccioná primer oponente:', reply_markup=reply_markup)


def _submit_dobles_oponentes2(bot, data, chat_id):
    data = json.loads(redis_get(data))
    users = mongo.find(config.get("MAIN_DB"), config.get("PLAYERS_COLLECTION"), {
                       "code": {"$nin": data["own"]["code"]}})

    keyboard = []
    for user in users:
        if user["code"] not in data["opponent"]["code"]:
            tmp = deepcopy(data)
            tmp["opponent"]["code"].append(user["code"])
            tmp["opponent"]["name"].append(user["username"])
            uid = redis_set(json.dumps(tmp))
            keyboard.append([InlineKeyboardButton(
                user["username"], callback_data="game_submit&"+uid)])

    keyboard.append([InlineKeyboardButton("Cancelar", callback_data="cancelar")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(
        chat_id=chat_id, text='Seleccioná segundo oponente:', reply_markup=reply_markup)


def _submit_score_1(bot, data, chat_id):
    data = json.loads(redis_get(data))

    keyboard = []
    for i in range(3):
        keyboard.append([])
        for x in range(3):
            data["own"]["points"] = int(i*3+x)
            uid = redis_set(json.dumps(data))
            keyboard[-1].append(InlineKeyboardButton(str(i*3+x),
                                                     callback_data="game_score1&"+uid))

    keyboard.append([InlineKeyboardButton("Cancelar", callback_data="cancelar")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(chat_id=chat_id, text='Ingrese tus puntos:',
                     reply_markup=reply_markup)


def _submit_score_2(bot, data, chat_id):
    data = json.loads(redis_get(data))

    keyboard = []
    for i in range(3):
        keyboard.append([])
        for x in range(3):
            data["opponent"]["points"] = int(i*3+x)
            uid = redis_set(json.dumps(data))
            keyboard[-1].append(InlineKeyboardButton(str(i*3+x),
                                                     callback_data="game_score2&"+uid))

    keyboard.append([InlineKeyboardButton("Cancelar", callback_data="cancelar")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(
        chat_id=chat_id, text='Ingrese los puntos de su oponente:', reply_markup=reply_markup)


def _submit_score(bot, data, chat_id):
    keyboard = [[
        InlineKeyboardButton(
            "Confirmar", callback_data="game_submit_confirm&"+data),
        InlineKeyboardButton("Cancelar", callback_data="game_submit_cancel")
    ]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    data = json.loads(redis_get(data))

    text_out = " - ".join(data["own"]["name"]) + ": " + str(data["own"]["points"]) + \
        "\n" + " - ".join(data["opponent"]["name"]) + \
        ": " + str(data["opponent"]["points"])

    bot.send_message(chat_id=chat_id, text=text_out, reply_markup=reply_markup)


def _submit_cancel(bot, data, chat_id):
    bot.send_message(chat_id=chat_id, text="Éxito al cancelar accion")


def _submit_confirm(bot, data, chat_id):
    data = json.loads(redis_get(data))
    own = list(mongo.find(config.get("MAIN_DB"), config.get("PLAYERS_COLLECTION"), {"code":{"$in": data["own"]["code"]}}))
    opponent = list(mongo.find(config.get("MAIN_DB"), config.get("PLAYERS_COLLECTION"), {"code":{"$in": data["opponent"]["code"]}}))

    own_elo = sum([user["ELO"] for user in own]) / len(own)
    opponent_elo = sum([user["ELO"] for user in opponent]) / len(opponent)
    own_elo_offset, opponent_elo_offset = _calculate_elo(
        own_elo,
        opponent_elo,
        int(data["own"]["points"]),
        int(data["opponent"]["points"])
    )

    for player in list(own):
        game = {
            "own": data["own"],
            "opponent": data["opponent"]
        }
        player["games"].append(game)
        player["ELO"] += own_elo_offset
        mongo.update_doc(config.get("MAIN_DB"), config.get("PLAYERS_COLLECTION"), {"code": player["code"]}, player)
        _send_elo_changes(bot, player, own_elo_offset, game)

    for player in list(opponent):
        game = {
            "own": data["opponent"],
            "opponent": data["own"]
        }
        player["games"].append(game)
        player["ELO"] += opponent_elo_offset
        mongo.update_doc(config.get("MAIN_DB"), config.get("PLAYERS_COLLECTION"), {"code": player["code"]}, player)
        _send_elo_changes(bot, player, opponent_elo_offset, game)
    
    weekly.submit(data)
            
    if (int(data["own"]["points"]) == 8 and int(data["opponent"]["points"]) == 0) or (int(data["own"]["points"]) == 0 and int(data["opponent"]["points"]) == 8):
        bot.sendDocument(chat_id=config.get("MAIN_GROUP"), document=open("/var/sources/metegolBotTelegram/8a0.gif","rb"), timeout=120)
    if (int(data["own"]["points"]) == 7 and int(data["opponent"]["points"]) == 0) or (int(data["own"]["points"]) == 0 and int(data["opponent"]["points"]) == 7):
        bot.sendDocument(chat_id=config.get("MAIN_GROUP"), document=open("/var/sources/metegolBotTelegram/7a0.gif","rb"), timeout=120)
    if (int(data["own"]["points"]) == 7 and int(data["opponent"]["points"]) == 1) or (int(data["own"]["points"]) == 1 and int(data["opponent"]["points"]) == 7):
        bot.sendDocument(chat_id=config.get("MAIN_GROUP"), document=open("/var/sources/metegolBotTelegram/7a1.gif","rb"), timeout=120)

    text_out = " - ".join(data["own"]["name"]) + ": " + str(data["own"]["points"]) + \
        "\n" + " - ".join(data["opponent"]["name"]) + \
        ": " + str(data["opponent"]["points"])

    bot.send_message(chat_id=config.get("MAIN_GROUP"), text=text_out)


def _send_elo_changes(bot, player, elo_offset, game):
    bot.send_message(chat_id=config.get("MAIN_GROUP"), text=player["username"] + " // " + str(int(player["ELO"])) + " (" + str(int(elo_offset)) + ") => " + str(int(player["ELO"])+int(elo_offset)))
