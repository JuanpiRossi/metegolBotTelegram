import logging
from botConfig import GROUPS,ADMIN
import datetime
from mongoConnection import startMongo,find_one,find,update_doc,insert_one,remove_by_query
from botConfig import WKHTMLTOIMAGE_PATH, PLAYERS_COLLECTION, LEAGUES_COLLECTION, WEEKLY, MULTIPLIER
import imgkit
import uuid
import os
import re

def _get_logger():
    logger = logging.getLogger('metegol')
    fh = logging.FileHandler('/var/sources/spam.log')
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

def _calculate_elo(elo_player_a, elo_player_b, player_a_goals, player_b_goals, goal_multiplier=None):
    divisor = 400
    player_a_transformed = float(10**(float(elo_player_a)/divisor))
    player_b_transformed = float(10**(float(elo_player_b)/divisor))

    player_a_expect_score = float(player_a_transformed) / float(player_a_transformed+player_b_transformed)
    player_b_expect_score = float(player_b_transformed) / float(player_a_transformed+player_b_transformed)

    if player_a_goals>player_b_goals:
        player_constant = _get_elo_constants(elo_player_a,25)
    else:
        player_constant = _get_elo_constants(elo_player_b,25)
    
    goals_multiplier = _get_goal_multiplier(player_a_goals,player_b_goals, multiplier_modifier=goal_multiplier)

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

def _get_goal_multiplier(goals_a,goals_b,multiplier_modifier=None):
    if not multiplier_modifier:
        multiplier_modifier = MULTIPLIER
    goals_diference = abs(goals_a-goals_b)
    return multiplier_modifier*goals_diference

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
    players = find(PLAYERS_COLLECTION,{})
    for player in players:
        for game in player["__$history"]:
            tmp = dict()
            if "type" not in game:
                enemy = _get_enemy(game)
                tmp[enemy] = game[enemy]
                if enemy not in list(jugadores.keys()):
                    jugadores[enemy] = 1800
                if player["__$name"] not in list(jugadores.keys()):
                    jugadores[player["__$name"]] = 1800
                tmp[player["__$name"]] = game["__$own"]
                tmp["__$time"] = game["__$date"]
                tmp["__$gameid"] = game["__$game_id"]
                tmp["type"] = "normal"
                tmp["names"] = [enemy,player["__$name"]]
                if game["__$game_id"] not in [g["__$gameid"] for g in games if "__$gameid" in g]:
                    games.append(tmp)
            elif game["type"] == "liga":
                tmp["type"] = "liga"
                tmp["__$name"] = player["__$name"]
                tmp["__$time"] = game["__$date"]
                tmp["players"] = game["players"]
                tmp["points"] = game["points"]
                games.append(tmp)


    games = sorted(games,key=lambda k: k["__$time"])

    for game in games:
        if game["type"] == "normal":
            play = game["names"]
            jugadores[play[0]], jugadores[play[1]] = _calculate_elo(jugadores[play[0]], jugadores[play[1]], game[play[0]], game[play[1]])
        elif game["type"] == "liga":
            jugadores[game["__$name"]] = jugadores[game["__$name"]] + (game["points"]*game["players"])
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

def _validate_end_league(bot,update,league,ignore_games=False):
    if not ignore_games:
        for partido in league["partidos"]:
            if partido["games"] != league["config"]["cant_partidos"]:
                return
    league["__$STATE"] = "END"
    update_doc(LEAGUES_COLLECTION,{"__$STATE":"PLAYING"},league)
    bot.send_message(chat_id=league["__$grupo"], text='Finalizo la liga: ' + str(league["config"]["nombre_liga"]))
    date = datetime.datetime.today()
    for player in _calculta_league_position(league):
        player_data = find_one(PLAYERS_COLLECTION,{"__$name":re.compile("^"+player["NAME"]+"$", re.IGNORECASE)})
        player_data["__$elo"]+=(player["POINTS"]*len(league["players"]))
        player_data["__$history"].append({"type":"liga","points":player["POINTS"],"name":league["config"]["nombre_liga"],"__$date":date,"players":len(league["players"])})
        update_doc(PLAYERS_COLLECTION,{"__$name":re.compile("^"+player["NAME"]+"$", re.IGNORECASE)},player_data)
    _render_league_image(bot, update, league, overrideChatId=league["__$grupo"])
    _render_league_games(bot, update, league, overrideChatId=league["__$grupo"])

def _render_league_image(bot, update, league, overrideChatId=None):
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
    if not overrideChatId:
        bot.send_photo(chat_id=update.message.chat_id, photo=file, timeout=60)
    else:
        bot.send_photo(chat_id=overrideChatId, photo=file, timeout=60)
    file.close()
    os.remove(file_name)

def _render_league_games(bot, update, league, overrideChatId=None):
    html ="""<!DOCTYPE html><html><head><style>table {font-family: arial, sans-serif;border-collapse: collapse;width: 400x;}td, th {border: 1px solid #dddddd;text-align: left;padding: 8px;}.header {background-color: #dddddd;}.nameColumn {width: 75px;}.pointColumn {width: 60px;}</style></head><body><h2>Partidos</h2><table><tr><td class='nameColumn header'>Jugador A</td><td class='nameColumn header'>Jugador B</td><td class='pointColumn header'>Goles A</td><td class='pointColumn header'>Goles B</td><td class='pointColumn header'>PJ</td></tr>"""
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
    if not overrideChatId:
        bot.send_photo(chat_id=update.message.chat_id, photo=file, timeout=60)
    else:
        bot.send_photo(chat_id=overrideChatId, photo=file, timeout=60)
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
    
def submit_simple(bot, update, args):
    player_a = find_one(PLAYERS_COLLECTION,{"$or":[{"__$name":re.compile("^"+args[0]+"$", re.IGNORECASE)},{"__$tel_name":args[0][1:]}]})
    player_a_week = find_one(WEEKLY,{"$or":[{"__$name":re.compile("^"+args[0]+"$", re.IGNORECASE)},{"__$tel_name":args[0][1:]}]})
    if not player_a:
        bot.send_message(chat_id=update.message.chat_id, text="El primero jugador no existe")
        return False
    player_b = find_one(PLAYERS_COLLECTION,{"$or":[{"__$name":re.compile("^"+args[2]+"$", re.IGNORECASE)},{"__$tel_name":args[2][1:]}]})
    player_b_week = find_one(WEEKLY,{"$or":[{"__$name":re.compile("^"+args[2]+"$", re.IGNORECASE)},{"__$tel_name":args[2][1:]}]})
    if not player_b:
        bot.send_message(chat_id=update.message.chat_id, text="El segundo jugador no existe")
        return False
    player_a_elo,player_b_elo = _calculate_elo(player_a["__$elo"], player_b["__$elo"], int(args[1]), int(args[3]))
    player_a_elo_week,player_b_elo_week = _calculate_elo(player_a_week["__$elo"], player_b_week["__$elo"], int(args[1]), int(args[3]))
    player_a_dif = ("+" if player_a_elo-player_a["__$elo"] > 0 else "-") + str(abs(player_a_elo-player_a["__$elo"]))
    player_b_dif = ("+" if player_b_elo-player_b["__$elo"] > 0 else "-") + str(abs(player_b_elo-player_b["__$elo"]))
    player_a["__$elo"] = player_a_elo
    player_b["__$elo"] = player_b_elo
    player_a_week["__$elo"] = player_a_elo_week
    player_b_week["__$elo"] = player_b_elo_week
    game_id = str(uuid.uuid4())
    match_history_a = {"__$date":datetime.datetime.today(),"__$own":int(args[1]), "__$game_id":game_id}
    match_history_a[str(player_b["__$name"])] = int(args[3])
    match_history_b = {"__$date":datetime.datetime.today(),"__$own":int(args[3]), "__$game_id":game_id}
    match_history_b[str(player_a["__$name"])] = int(args[1])
    player_a["__$history"].append(match_history_a)
    player_b["__$history"].append(match_history_b)
    player_a_week["__$history"].append(match_history_a)
    player_b_week["__$history"].append(match_history_b)
    update_doc(PLAYERS_COLLECTION,{"__$name":player_a["__$name"]},player_a)
    update_doc(PLAYERS_COLLECTION,{"__$name":player_b["__$name"]},player_b)
    update_doc(WEEKLY,{"__$name":player_a["__$name"]},player_a_week)
    update_doc(WEEKLY,{"__$name":player_b["__$name"]},player_b_week)
    bot.send_message(chat_id=update.message.chat_id, text="Partido cargado con exito\n"+
                                                        str(player_a["__$name"])+ " (" + player_a_dif +"): "+str(int(player_a_elo))+"\n"+
                                                        str(player_b["__$name"])+ " (" + player_b_dif +"): "+str(int(player_b_elo))+"\n"+
                                                        str(game_id))

def submit_doble(bot, update, args):
    players_team_a = args[0].split("&")
    players_team_b = args[2].split("&")

    player_a_1 = find_one(PLAYERS_COLLECTION,{"$or":[{"__$name":re.compile("^"+players_team_a[0]+"$", re.IGNORECASE)},{"__$tel_name":players_team_a[0][1:]}]})
    if not player_a_1:
        bot.send_message(chat_id=update.message.chat_id, text="Jugador "+str(players_team_a[0])+" no existe")
        return False
    player_a_2 = find_one(PLAYERS_COLLECTION,{"$or":[{"__$name":re.compile("^"+players_team_a[1]+"$", re.IGNORECASE)},{"__$tel_name":players_team_a[1][1:]}]})
    if not player_a_2:
        bot.send_message(chat_id=update.message.chat_id, text="Jugador "+str(players_team_a[1])+" no existe")
        return False

    player_b_1 = find_one(PLAYERS_COLLECTION,{"$or":[{"__$name":re.compile("^"+players_team_b[0]+"$", re.IGNORECASE)},{"__$tel_name":players_team_b[0][1:]}]})
    if not player_b_1:
        bot.send_message(chat_id=update.message.chat_id, text="Jugador "+str(players_team_b[0])+" no existe")
        return False
    player_b_2 = find_one(PLAYERS_COLLECTION,{"$or":[{"__$name":re.compile("^"+players_team_b[1]+"$", re.IGNORECASE)},{"__$tel_name":players_team_b[1][1:]}]})
    if not player_b_2:
        bot.send_message(chat_id=update.message.chat_id, text="Jugador "+str(players_team_b[1])+" no existe")
        return False

    team_a_elo = int((player_a_1["__$elo"] + player_a_2["__$elo"])/2)
    team_b_elo = int((player_b_1["__$elo"] + player_b_2["__$elo"])/2)
    
    new_team_a_elo,new_team_b_elo = _calculate_elo(team_a_elo, team_b_elo, int(args[1]), int(args[3]))
    team_a_dif = ("+" if new_team_a_elo-team_a_elo > 0 else "-") + str(abs(new_team_a_elo-team_a_elo))
    team_b_dif = ("+" if new_team_b_elo-team_b_elo > 0 else "-") + str(abs(new_team_b_elo-team_b_elo))

    player_a_1["__$elo"] = player_a_1["__$elo"] + int(new_team_a_elo-team_a_elo)
    player_a_2["__$elo"] = player_a_2["__$elo"] + int(new_team_a_elo-team_a_elo)
    player_b_1["__$elo"] = player_b_1["__$elo"] + int(new_team_b_elo-team_b_elo)
    player_b_2["__$elo"] = player_b_2["__$elo"] + int(new_team_b_elo-team_b_elo)

    game_id = str(uuid.uuid4())

    match_history = {"__$date":datetime.datetime.today(), "__$game_id":game_id, "type":"double", "team1":players_team_a, "team2":players_team_b}
    match_history[players_team_a[0]] = int(args[1])
    match_history[players_team_a[1]] = int(args[1])
    match_history[players_team_b[0]] = int(args[3])
    match_history[players_team_b[1]] = int(args[3])

    player_a_1["__$history"].append(match_history)
    player_a_2["__$history"].append(match_history)
    player_b_1["__$history"].append(match_history)
    player_b_2["__$history"].append(match_history)

    update_doc(PLAYERS_COLLECTION,{"__$name":player_a_1["__$name"]},player_a_1)
    update_doc(PLAYERS_COLLECTION,{"__$name":player_a_2["__$name"]},player_a_2)
    update_doc(PLAYERS_COLLECTION,{"__$name":player_b_1["__$name"]},player_b_1)
    update_doc(PLAYERS_COLLECTION,{"__$name":player_b_2["__$name"]},player_b_2)

    bot.send_message(chat_id=update.message.chat_id, text="Partido cargado con exito\n"+
                                                        str(player_a_1["__$name"])+ " (" + team_a_dif +"): "+str(int(player_a_1["__$elo"]))+"\n"+
                                                        str(player_a_2["__$name"])+ " (" + team_a_dif +"): "+str(int(player_a_2["__$elo"]))+"\n"+
                                                        str(player_b_1["__$name"])+ " (" + team_b_dif +"): "+str(int(player_b_1["__$elo"]))+"\n"+
                                                        str(player_b_2["__$name"])+ " (" + team_b_dif +"): "+str(int(player_b_2["__$elo"]))+"\n"+
                                                        str(game_id))

