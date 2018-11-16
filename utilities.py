import logging
from botConfig import GROUPS,ADMIN
import datetime
from mongoConnection import startMongo,find_one,find,update_doc,insert_one,remove_by_query
from botConfig import WKHTMLTOIMAGE_PATH, PLAYERS_COLLECTION, LEAGUES_COLLECTION
import imgkit
import uuid
import os
import re

def _get_logger():
    logger = logging.getLogger('metegol')
    fh = logging.FileHandler('spam.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

def _authenticate(update):
    if update.message.chat.id not in GROUPS:
        return False
    return True

def _authenticate_admin(update):
    if update.message.chat.id not in ADMIN:
        return False
    return True

def _get_elo_constants(elo_player,constant_array=[]):
    if not constant_array:
        constant_array = [(600,120),(800,52),(1200,44),(2600,16),(1400,40),(1600,36),(1800,32),(1000,48),(2000,28),(2200,24),(2400,20),(2800,8),(3000,2)]
    if type(constant_array)!=list:
        return constant_array
    constant_array = sorted(constant_array, key=lambda k: k[0])
    for ele in constant_array:
        if elo_player < ele[0]:
            return ele[1]
    return 1

def _calculate_elo(elo_player_a, elo_player_b, player_a_goals, player_b_goals):
    divisor = 400
    player_a_transformed = float(10**(float(elo_player_a)/divisor))
    player_b_transformed = float(10**(float(elo_player_b)/divisor))

    player_a_expect_score = float(player_a_transformed) / float(player_a_transformed+player_b_transformed)
    player_b_expect_score = float(player_b_transformed) / float(player_a_transformed+player_b_transformed)

    if player_a_goals>player_b_goals:
        player_constant = _get_elo_constants(elo_player_a)
    else:
        player_constant = _get_elo_constants(elo_player_b)
    
    goals_multiplier = _get_goal_multiplier(player_a_goals,player_b_goals)

    new_player_a_elo = int(round(elo_player_a + goals_multiplier*player_constant*float(float(int(player_a_goals>player_b_goals))-player_a_expect_score),0))
    new_player_b_elo = int(round(elo_player_b + goals_multiplier*player_constant*float(float(int(player_b_goals>player_a_goals))-player_b_expect_score),0))

    return new_player_a_elo,new_player_b_elo

def _bot_history(command,update,message):
    with open("history.log","a+") as history:
        person = update.message.from_user.username
        if update["message"]["chat"]["type"] == 'group':
            group = update["message"]["chat"]["title"]
            history.write(str(datetime.datetime.now()) + " - " + str(person) + " - " + str(command) + " - " + str(group) + "\n")
        elif update["message"]["chat"]["type"] == 'private':
            history.write(str(datetime.datetime.now()) + " - " + str(person) + " - " + str(command)  + " - " + str(message) + "\n")
        else:
            history.write(str(datetime.datetime.now()) + " - " + str(person) + " - " + str(command) + " - " + str(update) + "\n")

def _get_goal_multiplier(goals_a,goals_b,multiplier_modifier=[]):
    if not multiplier_modifier:
        # 1, 2, 3, 4, 5, 6, 7, 8 (el primer elemento es el default, por si a alguno se le ocurre jugar por mas de 8 goles)
        multiplier_modifier = [10,1,2,3,4,5,6,7,8]
    max_goals = len(multiplier_modifier)-1
    goals_diference = abs(goals_a-goals_b)
    
    if goals_diference > max_goals:
        return multiplier_modifier[0]
    else:
        return multiplier_modifier[goals_diference]

def _get_average_stats(player,percent=True):
    count = 0
    goals = 0
    win_count = 0
    for game in player["__$history"]:
        if "type" not in game:
            count+=1
            enemy = _get_enemy(game)
            goals+=(game["__$own"]-game[enemy])
            if game["__$own"] > game[enemy]:
                win_count+=1
    if count == 0:
        return "0.0","-","0"
    if percent:
        return str(round((float(goals)/float(count)),1)), str(round(100*(float(win_count)/float(count)),1)), str(count)
    else:
        return str(round((float(goals)/float(count)),1)), str(win_count), str(count)

def _get_enemy(game):
    enemy = [en for en in list(game.keys()) if "__$" not in en][0]
    return enemy



def _recalculate_points():
    games = []
    jugadores = {}
    players = find("jugadores_desa",{})
    for player in players:
        for game in player["__$history"]:
            enemy = _get_enemy(game)
            tmp = dict()
            tmp[enemy] = game[enemy]
            if enemy not in list(jugadores.keys()):
                jugadores[enemy] = 1800
            if player["__$name"] not in list(jugadores.keys()):
                jugadores[player["__$name"]] = 1800
            tmp[player["__$name"]] = game["__$own"]
            tmp["__$time"] = game["__$date"]
            tmp["__$gameid"] = game["__$game_id"]
            if game["__$game_id"] not in [g["__$gameid"] for g in games]:
                games.append(tmp)

    games = sorted(games,key=lambda k: k["__$time"])

    for game in games:
        play = list(game.keys())
        jugadores[play[0]], jugadores[play[1]] = _calculate_elo(jugadores[play[0]], jugadores[play[1]], game[play[0]], game[play[1]])
    return jugadores


def _submit_league_game(bot,update,league,player_a,player_b,goals_a,goals_b):
    for index,partido in enumerate(league["partidos"]):
        if player_a.lower() in partido and player_b.lower() in partido:
            if partido["games"] >= league["config"]["cant_partidos"]:
                bot.send_message(chat_id=update.message.chat_id, text='Ya se jugaron todos los partidos de estos jugadores')
                return False
            league["partidos"][index][player_a.lower()]+=goals_a
            league["partidos"][index][player_b.lower()]+=goals_b
            league["partidos"][index]["games"]+=1
            update_doc(LEAGUES_COLLECTION,{"__$STATE":"PLAYING"},league)
            return True
    bot.send_message(chat_id=update.message.chat_id, text='No se encontraron a los jugadores')
    return False

def _validate_end_league(bot,update,league):
    for partido in league["partidos"]:
        if partido["games"] != league["config"]["cant_partidos"]:
            return
    league["__$STATE"] = "END"
    update_doc(LEAGUES_COLLECTION,{"__$STATE":"PLAYING"},league)
    bot.send_message(chat_id=update.message.chat_id, text='Finalizo la liga: ' + str(league["config"]["nombre_liga"]))
    date = datetime.datetime.today()
    for player in _calculta_league_position(league):
        player_data = find_one(PLAYERS_COLLECTION,{"__$name":re.compile("^"+player["NAME"]+"$", re.IGNORECASE)})
        player_data["__$elo"]+=player["POINTS"]
        player_data["__$history"].append({"type":"liga","points":player["POINTS"],"name":league["config"]["nombre_liga"]})
        update_doc(PLAYERS_COLLECTION,{"__$name":re.compile("^"+player["NAME"]+"$", re.IGNORECASE)},player_data)
    _render_league_image(bot, update, league)
    _render_league_games(bot, update, league)

def _render_league_image(bot, update, league):
    html ="""<!DOCTYPE html><html><head><style>table {font-family: arial, sans-serif;border-collapse: collapse;width: 400x;}td, th {border: 1px solid #dddddd;text-align: left;padding: 8px;}.header {background-color: #dddddd;}.nameColumn {width: 75px;}.pointColumn {width: 60px;}</style></head><body><h2>Liga: {NOMBRELIGA}</h2><table><tr><td class='nameColumn header'>Jugador</td><td class='pointColumn header'>Partidos jugados</td><td class='pointColumn header'>Partidos ganados</td><td class='pointColumn header'>Goles a favor</td><td class='pointColumn header'>Puntos</td></tr>""".replace("{NOMBRELIGA}",league["config"]["nombre_liga"])
    players = _calculta_league_position(league)
    for player in players:
        html+="""<tr><td class='nameColumn'>{NAME}</td><td class='pointColumn'>{PJ}</td><td class='pointColumn'>{PG}</td><td class='pointColumn'>{GA}</td><td class='pointColumn'>{POINTS}</td></tr>""".format(**player)
    html+="""</table></body></html>"""
    file_name = str(uuid.uuid4())+".png"
    path_wkthmltopdf = WKHTMLTOIMAGE_PATH
    config = imgkit.config(wkhtmltoimage=path_wkthmltopdf)
    options = {
        'format': 'png',
        'encoding': "UTF-8",
        'crop-w': '415'
    }
    imgkit.from_string(html, file_name, options=options, config=config)
    file = open(file_name,'rb')
    bot.send_photo(chat_id=update.message.chat_id, photo=file, timeout=60)
    file.close()
    os.remove(file_name)

def _render_league_games(bot, update, league):
    html ="""<!DOCTYPE html><html><head><style>table {font-family: arial, sans-serif;border-collapse: collapse;width: 400x;}td, th {border: 1px solid #dddddd;text-align: left;padding: 8px;}.header {background-color: #dddddd;}.nameColumn {width: 75px;}.pointColumn {width: 60px;}</style></head><body><h2>Partidos</h2><table><tr><td class='nameColumn header'>Jugador A</td><td class='nameColumn header'>Jugador B</td><td class='pointColumn header'>Golas A</td><td class='pointColumn header'>Goles B</td><td class='pointColumn header'>PJ</td></tr>"""
    for game in league["partidos"]:
        players = [key for key in list(game.keys()) if key != "games"]
        html+="""<tr><td class='nameColumn'>{JUGA}</td><td class='nameColumn'>{JUGB}</td><td class='pointColumn'>{GA}</td><td class='pointColumn'>{GB}</td><td class='pointColumn'>{PJ}</td></tr>""".format(JUGA=players[0],JUGB=players[1],GA=game[players[0]],GB=game[players[1]],PJ=game["games"])
    html+="""</table></body></html>"""
    file_name = str(uuid.uuid4())+".png"
    path_wkthmltopdf = WKHTMLTOIMAGE_PATH
    config = imgkit.config(wkhtmltoimage=path_wkthmltopdf)
    options = {
        'format': 'png',
        'encoding': "UTF-8",
        'crop-w': '435'
    }
    imgkit.from_string(html, file_name, options=options, config=config)
    file = open(file_name,'rb')
    bot.send_photo(chat_id=update.message.chat_id, photo=file, timeout=60)
    file.close()
    os.remove(file_name)

def _calculta_league_position(league):
    players_points = {}
    for partido in league["partidos"]:
        players = [key for key in list(partido.keys()) if key != "games"]
        for player in players:
            if player not in players_points:
                players_points[player] = {"points":0,"pj":0,"pg":0,"ga":0}
        if not (partido[players[0]] == 0 and partido[players[1]] == 0):
            players_points[players[0]]["pj"]+=partido["games"]
            players_points[players[1]]["pj"]+=partido["games"]
            players_points[players[0]]["ga"]+=partido[players[0]]-partido[players[1]]
            players_points[players[1]]["ga"]+=partido[players[1]]-partido[players[0]]
            if partido[players[0]] > partido[players[1]]:
                players_points[players[0]]["points"]+=3
                players_points[players[0]]["pg"]+=1
            elif partido[players[0]] < partido[players[1]]:
                players_points[players[1]]["points"]+=3
                players_points[players[1]]["pg"]+=1
            else:
                players_points[players[0]]["points"]+=1
                players_points[players[1]]["points"]+=1
    return sorted([{"NAME":player,"POINTS":players_points[player]["points"],"PJ":players_points[player]["pj"],"PG":players_points[player]["pg"],"GA":players_points[player]["ga"]} for player in players_points],key=lambda k: (k["POINTS"],k["GA"]), reverse=True)

def _get_podio():
    #TODO
    pass

def _podio_checker(update,bot):
    #TODO
    pass
    
