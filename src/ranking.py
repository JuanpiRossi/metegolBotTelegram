# -*- coding: utf-8; -*-
from src.utils import exception_handler, group_validator
from src import mongoConnection as mongo
import config
import uuid
import os
import imgkit


@group_validator
@exception_handler
def ranking(bot, update):
    send_ranking(bot, update.message.chat_id, config.get("MAIN_DB"), config.get("PLAYERS_COLLECTION"))


def send_ranking(bot, chat_id, db, collection):
    players = mongo.find(db, collection, {})
    html = "<!DOCTYPE html><html><head><style>table {font-family: arial, sans-serif;border-collapse: collapse;width: 500px;}td, th {border: 1px solid #dddddd;text-align: left;padding: 8px;}.header {background-color: #dddddd;}.nameColumn {width: 250px;}.pointColumn {width: 50px;}</style></head><body><h2>Ranking</h2><table><tr><td class='nameColumn header'>Nombre</td><td class='pointColumn header'>PJ</td><td class='pointColumn header'>PG</td><td class='pointColumn header'>%G</td><td class='pointColumn header'>DG</td><td class='pointColumn header'>Puntos</td></tr>"
    for player in players:
        average_goals, average_percent_games, games_played = _get_average_stats(player,percent=False)
        if int(games_played) == 0:
            percent = "-"
        else:
            percent = str(round(100*float(float(average_percent_games)/float(games_played)),1))+"%"
        html = html+"<tr><td class='nameColumn'>{NOMBRE}</td><td class='pointColumn'>{PARTJU}</td><td class='pointColumn'>{PARTGA}</td><td class='pointColumn'>{PERCENT}</td><td class='pointColumn'>{GOLES}</td><td class='pointColumn'>{PUNTOS}</td></tr>".format(NOMBRE=player["username"],PARTJU=games_played,PARTGA=average_percent_games,PERCENT=str(percent),GOLES=average_goals,PUNTOS=str(int(player["ELO"])))
    html = html+"</table></body></html>"
    file_name = str(uuid.uuid4())+".png"
    path_wkthmltopdf = config.get("WKHTMLTOIMAGE_PATH")
    config_wk = imgkit.config(wkhtmltoimage=path_wkthmltopdf)
    options = {
        'format': 'png',
        'encoding': "UTF-8",
        'crop-w': '515'
    }
    imgkit.from_string(html, file_name, options=options, config=config_wk)
    file = open(file_name,'rb')
    bot.send_photo(chat_id=chat_id, photo=file, timeout=60)
    file.close()
    os.remove(file_name)


def _get_average_stats(player,percent=True):
    count = 0
    goals = 0
    win_count = 0
    for game in player["games"]:
        count+=1
        goals+=(game["own"]["points"]-game["opponent"]["points"])
        if game["own"]["points"] > game["opponent"]["points"]:
            win_count+=1
    if count == 0:
        return "0.0","-","0"
    if percent:
        return str(round((float(goals)/float(count)),1)), str(round(100*(float(win_count)/float(count)),1)), str(count)
    else:
        return str(round((float(goals)/float(count)),1)), str(win_count), str(count)
