# -*- coding: utf-8; -*-
from src import mongoConnection as mongo
from src.utils import exception_handler, _calculate_elo, group_validator
import datetime
import config
from src import ranking as rank
import telegram
import enviroment


def submit(data):
    collection = str(datetime.date.today().year) + "_" + str(datetime.date.today().isocalendar()[1])

    for index,player in enumerate(data["own"]["code"]):
        exists = mongo.find_one(config.get("WEEKLY_DB"), collection, {"code": player})
        if (not exists):
            mongo.insert_one(config.get("WEEKLY_DB"), collection, {
                "code": player,
                "username": data["own"]["name"][index],
                "ELO": 1200,
                "games": []
            })
    for index,player in enumerate(data["opponent"]["code"]):
        exists = mongo.find_one(config.get("WEEKLY_DB"), collection, {"code": player})
        if (not exists):
            mongo.insert_one(config.get("WEEKLY_DB"), collection, {
                "code": player,
                "username": data["opponent"]["name"][index],
                "ELO": 1200,
                "games": []
            })

    own = list(mongo.find(config.get("WEEKLY_DB"), collection, {"code":{"$in": data["own"]["code"]}}))
    opponent = list(mongo.find(config.get("WEEKLY_DB"), collection, {"code":{"$in": data["opponent"]["code"]}}))

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
        mongo.update_doc(config.get("WEEKLY_DB"), collection, {"code": player["code"]}, player)

    for player in list(opponent):
        game = {
            "own": data["opponent"],
            "opponent": data["own"]
        }
        player["games"].append(game)
        player["ELO"] += opponent_elo_offset
        mongo.update_doc(config.get("WEEKLY_DB"), collection, {"code": player["code"]}, player)


@group_validator
@exception_handler
def ranking(bot, update):
    collection = str(datetime.date.today().year) + "_" + \
                     str(datetime.date.today().isocalendar()[1])
    rank.send_ranking(bot, update.message.chat_id, config.get("WEEKLY_DB"), collection)


def show_weekly_ranking():
    bot = telegram.Bot(token=enviroment.BOT_TOKEN)
    collection = str(datetime.date.today().year) + "_" + \
                     str(datetime.date.today().isocalendar()[1])
    rank.send_ranking(bot, config.get("MAIN_GROUP"), config.get("WEEKLY_DB"), collection)
