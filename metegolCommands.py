from mongoConnection import startMongo,find_one,find,update_doc,insert_one,remove_by_query
from telegram import InlineQueryResultArticle, InputTextMessageContent, ParseMode
import telegram
from random import randint
import itertools
import imgkit
import uuid
import os
import re
from utilities import _calculate_elo, _get_logger, _authenticate, _authenticate_admin,_bot_history, _get_average_stats, _recalculate_points, _submit_league_game,_validate_end_league, _render_league_image, _render_league_games
from datetime import datetime
from botConfig import WKHTMLTOIMAGE_PATH, PLAYERS_COLLECTION, LEAGUES_COLLECTION

def add_player(bot, update, args):
    try:
        logger = _get_logger()
        _bot_history("add_player",update,args)
        # Validaciones de argumentos
        if not args:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, agregar nombre del jugador")
            return
        elif len(args) != 1:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, el nombre del jugador no puede tener espacios")
            return
        elif "__$" in args[0]:
            bot.send_message(chat_id=update.message.chat_id, text="Nombre invalido, no se acepta el simbolo $")
            return
        if not _authenticate(update):
            bot.send_message(chat_id=update.message.chat_id, text="Grupo invalido")
            return
        player = find_one(PLAYERS_COLLECTION,{"__$name":re.compile("^"+args[0]+"$", re.IGNORECASE)})
        if not player:
            mongo_response = insert_one(PLAYERS_COLLECTION,{"__$name":args[0],"__$elo":1200,"__$history":[]})
        else:
            bot.send_message(chat_id=update.message.chat_id, text="El jugador ya existe")
            return
        bot.send_message(chat_id=update.message.chat_id, text="Jugador agregado con exito")
    except Exception as ex:
        logger.exception(ex)
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        return

def remove_player(bot, update, args):
    try:
        logger = _get_logger()
        _bot_history("remove_player",update,args)
        # Validaciones de argumentos
        if not args:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, agregar nombre del jugador")
            return
        elif len(args) != 1:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, el nombre del jugador no puede tener espacios")
            return
        if not _authenticate_admin(update):
            bot.send_message(chat_id=update.message.chat_id, text="Requiere autorizacion de un administrador")
            return

        query = {}
        query[args[0]] = {"$exists":True}
        remove_by_query(PLAYERS_COLLECTION,{"__$name":args[0]})
        bot.send_message(chat_id=update.message.chat_id, text="Jugador eliminado con exito")
    except Exception as ex:
        logger.exception(ex)
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        return
    
def players_list(bot, update):
    try:
        logger = _get_logger()
        _bot_history("players_list",update,None)
        if not _authenticate(update):
            bot.send_message(chat_id=update.message.chat_id, text="Grupo invalido")
            return
        players = find(PLAYERS_COLLECTION,{})
        message = "Jugadores ( {} ):\n".format(players.count())
        for player in players:
            message = message + player["__$name"] + "\n"
        bot.send_message(chat_id=update.message.chat_id, text=message)
    except Exception as ex:
        logger.exception(ex)
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        return

def player_info(bot, update, args):
    try:
        logger = _get_logger()
        _bot_history("player_info",update,args)
        # Validaciones de argumentos
        if not _authenticate(update):
            bot.send_message(chat_id=update.message.chat_id, text="Grupo invalido")
            return
        if not args:
            args = [str(update.message.from_user.id)]
        elif len(args) > 1:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, el nombre del jugador no puede tener espacios")
            return
        player = find_one(PLAYERS_COLLECTION,{"$or":[{"__$name":re.compile("^"+args[0]+"$", re.IGNORECASE)},{"__$tel_name":args[0][1:]},{"__$tel_id":int(args[0])}]})
        if not player:
            bot.send_message(chat_id=update.message.chat_id, text="El jugador no existe")
            return
        message = "Partidos de " + str(args[0]) + "\n"
        for game in player["__$history"]:
            if "type" not in game:
                enemy = [player for player in list(game.keys()) if "__$" not in player]
                if len(enemy)==1:
                    enemy = enemy[0]
                    message = message + "- " + str(player["__$name"]) + ": " + str(game["__$own"]) + " | " + str(enemy) + ": " + str(game[enemy]) + "\n"
                else:
                    logger.error(game)
        bot.send_message(chat_id=update.message.chat_id, text=message)
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def admin_player_info(bot, update, args):
    try:
        logger = _get_logger()
        _bot_history("admin_player_info",update,args)
        # Validaciones de argumentos
        if not _authenticate_admin(update):
            bot.send_message(chat_id=update.message.chat_id, text="Requiere autorizacion de un administrador")
            return
        if not args:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, agregar nombre del jugador")
            return
        elif len(args) != 1:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, el nombre del jugador no puede tener espacios")
            return

        player = find_one(PLAYERS_COLLECTION,{"$or":[{"__$name":re.compile("^"+args[0]+"$", re.IGNORECASE)},{"__$tel_name":args[0][1:]}]})
        if not player:
            bot.send_message(chat_id=update.message.chat_id, text="El jugador no existe")
            return
        message = "Partidos de " + str(player["__$name"]) + "\n"
        for game in player["__$history"]:
            if "type" not in game:
                enemy = [player for player in list(game.keys()) if "__$" not in player]
                if len(enemy)==1:
                    enemy = enemy[0]
                    message = message + "- " + str(player["__$name"]) + ": " + str(game["__$own"]) + " | " + str(enemy) + ": " + str(game[enemy]) + " / " + game["__$game_id"] + "\n"
                else:
                    logger.error(game)
        bot.send_message(chat_id=update.message.chat_id, text=message)
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def player_statics(bot, update, args):
    try:
        logger = _get_logger()
        _bot_history("player_statics",update,args)
        # Validaciones de argumentos
        if not _authenticate(update):
            bot.send_message(chat_id=update.message.chat_id, text="Grupo invalido")
            return
        if not args:
            args = [str(update.message.from_user.id)]
        elif len(args) != 1:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, el nombre del jugador no puede tener espacios")
            return

        player = find_one(PLAYERS_COLLECTION,{"$or":[{"__$name":re.compile("^"+args[0]+"$", re.IGNORECASE)},{"__$tel_name":args[0][1:]},{"__$tel_id":int(args[0])}]})
        if not player:
            bot.send_message(chat_id=update.message.chat_id, text="El jugador no existe")
            return
        message = "Estadisticas de " + str(player["__$name"]) + "\n"
        games_dict = {}
        for game in player["__$history"]:
            if "type" not in game:
                enemy = [player for player in list(game.keys()) if "__$" not in player]
                if len(enemy)==1:
                    enemy = enemy[0]
                    if enemy not in games_dict:
                        games_dict[enemy] = {"own":0,"enemy":0}
                    games_dict[enemy]["own"] = games_dict[enemy]["own"] + int(game["__$own"]>game[enemy])
                    games_dict[enemy]["enemy"] = games_dict[enemy]["enemy"] + int(game[enemy]>game["__$own"])
                else:
                    logger.error(game)
        for key in games_dict:
            percent = 100*(float(games_dict[key]["own"])/float(games_dict[key]["own"]+games_dict[key]["enemy"]))
            message = message + str(player["__$name"]) + ": " + str(games_dict[key]["own"]) + " | " + str(key) + ": " + str(games_dict[key]["enemy"]) + " - (" + str(round(percent,1)) + "%)\n"

        average_goals, average_percent_games, games_played = _get_average_stats(player,percent=True)
        message = message + "Promedio diferencia de goles: " + str(average_goals) + "\n"
        message = message + "Promedio de partidos ganados: " + str(average_percent_games) + "%\n"
        message = message + "Partidos jugados: " + str(games_played) + "\n"
        bot.send_message(chat_id=update.message.chat_id, text=message)
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def submit_result_goals(bot, update, args):
    try:
        logger = _get_logger()
        _bot_history("submit_result_goals",update,args)
        # Validaciones de argumentos
        if not _authenticate(update):
            bot.send_message(chat_id=update.message.chat_id, text="Grupo invalido")
            return False
        if not args:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, cargue algun dato")
            return False
        elif len(args) != 4:
            bot.send_message(chat_id=update.message.chat_id, text="La estructura del comando es: JUGADOR1 # JUGADOR2 #")
            return False
        try:
            int(args[1])
            int(args[3])
        except:
            bot.send_message(chat_id=update.message.chat_id, text="Debe cargar goles numericos")
            return False


        player_a = find_one(PLAYERS_COLLECTION,{"$or":[{"__$name":re.compile("^"+args[0]+"$", re.IGNORECASE)},{"__$tel_name":args[0][1:]}]})
        if not player_a:
            bot.send_message(chat_id=update.message.chat_id, text="El primero jugador no existe")
            return False
        player_b = find_one(PLAYERS_COLLECTION,{"$or":[{"__$name":re.compile("^"+args[2]+"$", re.IGNORECASE)},{"__$tel_name":args[2][1:]}]})
        if not player_b:
            bot.send_message(chat_id=update.message.chat_id, text="El segundo jugador no existe")
            return False
        player_a_elo,player_b_elo = _calculate_elo(player_a["__$elo"], player_b["__$elo"], int(args[1]), int(args[3]))
        player_a_dif = ("+" if player_a_elo-player_a["__$elo"] > 0 else "-") + str(abs(player_a_elo-player_a["__$elo"]))
        player_b_dif = ("+" if player_b_elo-player_b["__$elo"] > 0 else "-") + str(abs(player_b_elo-player_b["__$elo"]))
        player_a["__$elo"] = player_a_elo
        player_b["__$elo"] = player_b_elo
        game_id = str(uuid.uuid4())
        match_history_a = {"__$date":datetime.today(),"__$own":int(args[1]), "__$game_id":game_id}
        match_history_a[str(player_b["__$name"])] = int(args[3])
        match_history_b = {"__$date":datetime.today(),"__$own":int(args[3]), "__$game_id":game_id}
        match_history_b[str(player_a["__$name"])] = int(args[1])
        player_a["__$history"].append(match_history_a)
        player_b["__$history"].append(match_history_b)
        update_doc(PLAYERS_COLLECTION,{"__$name":player_a["__$name"]},player_a)
        update_doc(PLAYERS_COLLECTION,{"__$name":player_b["__$name"]},player_b)
        bot.send_message(chat_id=update.message.chat_id, text="Partido cargado con exito\n"+
                                                            str(player_a["__$name"])+ " (" + player_a_dif +"): "+str(int(player_a_elo))+"\n"+
                                                            str(player_b["__$name"])+ " (" + player_b_dif +"): "+str(int(player_b_elo))+"\n"+
                                                            str(game_id))
        return True
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return False
    
def get_elo(bot, update):
    try:
        logger = _get_logger()
        _bot_history("get_elo",update,None)
        if not _authenticate(update):
            bot.send_message(chat_id=update.message.chat_id, text="Grupo invalido")
            return
        players = find(PLAYERS_COLLECTION,{},sort="-__$elo")
        html = "<!DOCTYPE html><html><head><style>table {font-family: arial, sans-serif;border-collapse: collapse;width: 500px;}td, th {border: 1px solid #dddddd;text-align: left;padding: 8px;}.header {background-color: #dddddd;}.nameColumn {width: 250px;}.pointColumn {width: 50px;}</style></head><body><h2>Ranking</h2><table><tr><td class='nameColumn header'>Nombre</td><td class='pointColumn header'>PJ</td><td class='pointColumn header'>PG</td><td class='pointColumn header'>%G</td><td class='pointColumn header'>DG</td><td class='pointColumn header'>Puntos</td></tr>"
        for player in players:
            average_goals, average_percent_games, games_played = _get_average_stats(player,percent=False)
            if int(games_played) == 0:
                percent = "-"
            else:
                percent = str(round(100*float(float(average_percent_games)/float(games_played)),1))+"%"
            html = html+"<tr><td class='nameColumn'>{NOMBRE}</td><td class='pointColumn'>{PARTJU}</td><td class='pointColumn'>{PARTGA}</td><td class='pointColumn'>{PERCENT}</td><td class='pointColumn'>{GOLES}</td><td class='pointColumn'>{PUNTOS}</td></tr>".format(NOMBRE=player["__$name"],PARTJU=games_played,PARTGA=average_percent_games,PERCENT=str(percent),GOLES=average_goals,PUNTOS=str(int(player["__$elo"])))
        html = html+"</table></body></html>"
        file_name = str(uuid.uuid4())+".png"
        path_wkthmltopdf = WKHTMLTOIMAGE_PATH
        config = imgkit.config(wkhtmltoimage=path_wkthmltopdf)
        options = {
            'format': 'png',
            'encoding': "UTF-8",
            'crop-w': '515'
        }
        imgkit.from_string(html, file_name, options=options, config=config)
        file = open(file_name,'rb')
        bot.send_photo(chat_id=update.message.chat_id, photo=file, timeout=60)
        file.close()
        os.remove(file_name)
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def admin_remove_game(bot, update, args):
    try:
        logger = _get_logger()
        _bot_history("admin_remove_game",update,args)
        # Validaciones de argumentos
        if not _authenticate_admin(update):
            bot.send_message(chat_id=update.message.chat_id, text="Requiere autorizacion de un administrador")
            return
        if not args:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, agregar nombre del jugador")
            return
        if len(args) != 1:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, solo un ID")
            return
        
        query = {"__$history.__$game_id":args[0]}
        players = find(PLAYERS_COLLECTION,query)
        if players.count() == 0:
            bot.send_message(chat_id=update.message.chat_id, text="No se encontro el ID")
            return
        for player in players:
            new_data = player
            partida = [game for game in player["__$history"] if game["__$game_id"] == args[0]][0]
            new_data["__$history"] = [game for game in player["__$history"] if game["__$game_id"] != args[0]]
            partida[player["__$name"]] = partida.pop("__$own")
            partida.pop("__$date")
            partida.pop("__$game_id")
            partida = str(list(partida.keys())[0]) + ": " + str(partida[list(partida.keys())[0]]) + " | " + str(list(partida.keys())[1]) + ": " + str(partida[list(partida.keys())[1]])
            update_doc(PLAYERS_COLLECTION,{"__$name":player["__$name"]},new_data)
        bot.send_message(chat_id=update.message.chat_id, text="Exito al borrar la partida:\n"+str(partida))
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def set_elo(bot,update,args):
    try:
        logger = _get_logger()
        _bot_history("admin_remove_game",update,args)
        # Validaciones de argumentos
        if not _authenticate_admin(update):
            bot.send_message(chat_id=update.message.chat_id, text="Requiere autorizacion de un administrador")
            return
        if not args:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, agregar nombre del jugador")
            return
        if len(args) != 1:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, solo un ID")
            return
        
        query = {"__$history.__$game_id":args[0]}
        players = find(PLAYERS_COLLECTION,query)
        if players.count() == 0:
            bot.send_message(chat_id=update.message.chat_id, text="No se encontro el ID")
            return
        for player in players:
            new_data = player
            partida = [game for game in player["__$history"] if game["__$game_id"] == args[0]][0]
            new_data["__$history"] = [game for game in player["__$history"] if game["__$game_id"] != args[0]]
            partida[player["__$name"]] = partida.pop("__$own")
            partida.pop("__$date")
            partida.pop("__$game_id")
            partida = str(list(partida.keys())[0]) + ": " + str(partida[list(partida.keys())[0]]) + " | " + str(list(partida.keys())[1]) + ": " + str(partida[list(partida.keys())[1]])
            update_doc(PLAYERS_COLLECTION,{"__$name":player["__$name"]},new_data)
        bot.send_message(chat_id=update.message.chat_id, text="Exito al borrar la partida:\n"+str(partida))
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def link(bot,update,args):
    try:
        logger = _get_logger()
        _bot_history("set_elo",update,args)
        # Validaciones de argumentos
        if not _authenticate(update):
            bot.send_message(chat_id=update.message.chat_id, text="Grupo invalido")
            return
        if not args or len(args) != 1:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, ingrese el nombre del jugador al que desea vincular su usuario")
            return
        
        player = find_one(PLAYERS_COLLECTION,{"__$name":re.compile("^"+args[0]+"$", re.IGNORECASE)})
        if not player:
            bot.send_message(chat_id=update.message.chat_id, text="No se encontro al jugador")
            return
        if "__$link" in player:
            bot.send_message(chat_id=update.message.chat_id, text="El jugador ya se encuentra vinculado")
            return
        user_id = update.message.from_user.id
        user_name = update.message.from_user.username
        update_doc(PLAYERS_COLLECTION,{"__$name":re.compile("^"+args[0]+"$", re.IGNORECASE)},{"$set":{"__$tel_id":user_id,"__$tel_name":user_name}})
        bot.send_message(chat_id=update.message.chat_id, text="Exito al vincular jugador")
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def alive(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Estoy vivito en el grupo: " + str(update.message.chat.id))

def recalculate_elo(bot, update):
    try:
        logger = _get_logger()
        if not _authenticate_admin(update):
            bot.send_message(chat_id=update.message.chat_id, text="Requiere autorizacion de un administrador")
            return
        players = _recalculate_points()
        for key in players:
            bot.send_message(chat_id=update.message.chat_id, text="Actualizando " + str(key))
            update_doc(PLAYERS_COLLECTION,{"__$name":key},{"$set":{"__$elo":int(players[key])}})
            bot.send_message(chat_id=update.message.chat_id, text=str(key) + " actualizado con exito")
        bot.send_message(chat_id=update.message.chat_id, text="Puntos actualizados")
    except Exception as ex:
        logger.exception(ex)
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        return    

def start_league(bot, update):
    try:
        logger = _get_logger()
        if not _authenticate(update):
            bot.send_message(chat_id=update.message.chat_id, text="Grupo invalido")
            return
        league = find_one(LEAGUES_COLLECTION,{"__$STATE":{"$ne":"END"}})
        if league:
            league = find_one(LEAGUES_COLLECTION,{"__$STATE":"JOINING"})
            if not league:
                bot.send_message(chat_id=update.message.chat_id, text="Ya hay una liga en progreso")
                return
            start_playing_league(bot, update, league)
            bot.send_message(chat_id=update.message.chat_id, text="Inicio la liga: " + league["config"]["nombre_liga"])
            bot.send_message(chat_id=update.message.chat_id, text="Lista de jugadores:\n" + "\n".join([player for player in league["players"]]))
            return
        insert_one(LEAGUES_COLLECTION,{"__$STATE":"CONFIG","__$DATE":datetime.today(),"__$organizador":{"id":update.message.from_user.id,"name":update.message.from_user.username},"config":{"cant_partidos":1},"__$grupo":update.message.chat_id,"players":[]})
        bot.send_message(chat_id=update.message.chat_id, text="La liga esta siendo configurada por: @" + str(update.message.from_user.username))
        custom_keyboard = [['Solo ida', 'Ida y vuelta']]
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
        bot.send_message(chat_id=update.message.from_user.id, 
                        text="Cantidad de cruces:", 
                 reply_markup=reply_markup)
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return
    
def cruces_partidos(bot, update):
    try:
        logger = _get_logger()
        liga = find_one(LEAGUES_COLLECTION,{"__$STATE":"CONFIG","__$organizador.id":update.message.from_user.id})
        if not liga:
            bot.send_message(chat_id=update.message.chat_id, text="Mi no entender")
            return
        print(liga)
        cant_partidos = 1 if update.message.text == "Solo ida" else 2
        liga["config"]["cant_partidos"] = cant_partidos
        update_doc(LEAGUES_COLLECTION,{"__$STATE":"CONFIG","__$organizador.id":update.message.from_user.id},liga)
        reply_markup = telegram.ReplyKeyboardRemove()
        bot.send_message(chat_id=update.message.from_user.id, text='Ingrese nombre de la liga (con el formato"NombreLiga:*nombre de la liga")', reply_markup=reply_markup)
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def nombre_liga(bot, update):
    try:
        logger = _get_logger()
        liga = find_one(LEAGUES_COLLECTION,{"__$STATE":"CONFIG","__$organizador.id":update.message.from_user.id})
        if not liga:
            bot.send_message(chat_id=update.message.chat_id, text="Mi no entender")
            return
        liga["config"]["nombre_liga"] = str(update.message.text)[11:]
        liga["__$STATE"]= "JOINING"
        update_doc(LEAGUES_COLLECTION,{"__$STATE":"CONFIG","__$organizador.id":update.message.from_user.id},liga)
        reply_markup = telegram.ReplyKeyboardRemove()
        bot.send_message(chat_id=liga["__$grupo"], text="@"+str(liga['__$organizador']["name"])+ " da inicio a la liga: " + str(update.message.text)[11:])
        bot.send_message(chat_id=liga["__$grupo"], text='Escribí /joinliga para unirte a la liga')
        bot.send_message(chat_id=update.message.chat_id, text='Configuracion terminada', reply_markup=reply_markup)
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def join_league(bot, update):
    try:
        logger = _get_logger()
        # Validaciones de argumentos
        if not _authenticate(update):
            bot.send_message(chat_id=update.message.chat_id, text="Grupo invalido")
            return
        liga = find_one(LEAGUES_COLLECTION,{"__$STATE":"JOINING"})
        if not liga:
            bot.send_message(chat_id=update.message.chat_id, text="Mi no entender")
            return
        player = find_one(PLAYERS_COLLECTION,{"__$tel_id":update.message.from_user.id})
        if not player:
            bot.send_message(chat_id=update.message.chat_id, text='No se encontro jugador, recuerde que debe linkear su usuario a un jugador')
            return
        liga["players"].append(player["__$name"].lower())
        update_doc(LEAGUES_COLLECTION,{"__$STATE":"JOINING"},liga)
        bot.send_message(chat_id=liga["__$grupo"], text="@"+str(player["__$tel_name"]+" Exito al unirse a la liga"))
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def start_playing_league(bot, update, league):
    try:
        logger = _get_logger()
        # Validaciones de argumentos
        if not _authenticate(update):
            bot.send_message(chat_id=update.message.chat_id, text="Grupo invalido")
            return
        league["__$STATE"] = "PLAYING"
        league["partidos"] = []
        html ="""<!DOCTYPE html><html><head><style>table {font-family: arial, sans-serif;border-collapse: collapse;width: 400x;}td, th {border: 1px solid #dddddd;text-align: left;padding: 8px;}.header {background-color: #dddddd;}.nameColumn {width: 75px;}.pointColumn {width: 60px;}</style></head><body><h2>Partidos</h2><table><tr><td class='nameColumn header'>Jugador A</td><td class='nameColumn header'>Jugador B</td><td class='pointColumn header'>Golas A</td><td class='pointColumn header'>Goles B</td><td class='pointColumn header'>PJ</td></tr>"""
        for game in list(itertools.combinations(league["players"],2)):
            tmp = {"games":0}
            tmp[game[0]] = 0
            tmp[game[1]] = 0
            html+="""<tr><td class='nameColumn'>{JUGA}</td><td class='nameColumn'>{JUGB}</td><td class='pointColumn'>{GA}</td><td class='pointColumn'>{GB}</td><td class='pointColumn'>{PJ}</td></tr>""".format(JUGA=game[0],JUGB=game[1],GA="0",GB="0",PJ="0")
            league["partidos"].append(tmp)
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
        update_doc(LEAGUES_COLLECTION,{"__$STATE":"JOINI,NG"},league)
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def submit_league(bot, update, args):
    try:
        logger = _get_logger()
        # Validaciones de argumentos
        if not _authenticate(update):
            bot.send_message(chat_id=update.message.chat_id, text="Grupo invalido")
            return
        if not submit_result_goals(bot, update, args):
            return
        player_a = args[0]
        player_b = args[2]
        goals_a = int(args[1])
        goals_b = int(args[3])
        league = find_one(LEAGUES_COLLECTION,{"__$STATE":"PLAYING"})
        if not league:
            bot.send_message(chat_id=update.message.chat_id, text='No hay ninguna liga en curso')
            return
        if not _submit_league_game(bot,update,league,player_a,player_b,goals_a,goals_b):
            return
        bot.send_message(chat_id=update.message.chat_id, text='Partido de liga cargado con exito')
        _validate_end_league(bot,update,league)
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def league_leaderboard(bot, update):
    try:
        logger = _get_logger()
        # Validaciones de argumentos
        if not _authenticate(update):
            bot.send_message(chat_id=update.message.chat_id, text="Grupo invalido")
            return
        league = find_one(LEAGUES_COLLECTION,{"__$STATE":"PLAYING"})
        if not league:
            bot.send_message(chat_id=update.message.chat_id, text='No hay ninguna liga en curso')
            return
        _render_league_image(bot, update, league)
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def league_games(bot, update):
    try:
        logger = _get_logger()
        # Validaciones de argumentos
        if not _authenticate(update):
            bot.send_message(chat_id=update.message.chat_id, text="Grupo invalido")
            return
        league = find_one(LEAGUES_COLLECTION,{"__$STATE":"PLAYING"})
        if not league:
            bot.send_message(chat_id=update.message.chat_id, text='No hay ninguna liga en curso')
            return
        _render_league_games(bot, update, league)
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def _help(bot, update):
    try:
        logger = _get_logger()
        _bot_history("_help",update,None)
        if not _authenticate(update):
            bot.send_message(chat_id=update.message.chat_id, text="Grupo invalido")
            return
        bot.send_message(chat_id=update.message.chat_id, text="""Lista de comandos:
/nuevojugador JUGADOR - Permite agregar un jugador nuevo
/listajugadores - Muestra una lista de jugadores
/ranking - Muestra el puntaje de los jugadores
/estadisticasjugador JUGADOR - Permite ver las estadisticas de un jugador
/partidosjugador JUGADOR - Permite ver los partidos de un jugador
/submit JUGADOR # JUGADOR # - Permite ingresar un nuevo partido
/submitliga JUGADOR # JUGADOR # - Permite ingresar un nuevo partido de liga
/link JUGADOR - Permite vincularse a un jugador actual
/joinliga - Permite unirse a la liga que se esta formando actualmente
/startliga - Permite crear una liga nueva si no hay ninguna en transito o empezar la liga sise esta configurando
/rankingliga - Muestra el ranking actual de la liga
/partidosliga - Muestra los partidos de la liga
/help - Si no entendes un carajo""", parse_mode=ParseMode.MARKDOWN)
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def _help_admin(bot, update):
    try:
        logger = _get_logger()
        if not _authenticate_admin(update):
            bot.send_message(chat_id=update.message.chat_id, text="Requiere autorizacion de un administrador")
            return
        bot.send_message(chat_id=update.message.chat_id, text="""Lista de comandos:
/removegame GAME - `Elimina una partida`
/eliminarjugador JUGADOR - `Elimina un jugador`
/partidosjugadoradmin JUGADOR - `Muestra los partidos con ID`""", parse_mode=ParseMode.MARKDOWN)
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def common_message(bot, update):
    print(update.message.text)
    if "NombreLiga:" in update.message.text:
        nombre_liga(bot, update)
        return
    elif update.message.text == "Solo ida" or update.message.text == "Ida y vuelta":
        cruces_partidos(bot, update)
        return
    
    #EXCEPCIONES
    if str(update.message.from_user.id) == "145482249":
        xavi_gato(bot, update)
    elif "látigo" in update.message.text or "latigo" in update.message.text:
        bot.send_message(chat_id=update.message.chat_id, text="A vos te vamos a dar latigo gil")
    elif "gato" in update.message.text:
        bot.send_message(chat_id=update.message.chat_id, text="Gato vo eh")
    elif "bot" in update.message.text:
        bot.send_message(chat_id=update.message.chat_id, text="El bot soy yo papa")
    elif "asd" in update.message.text:
        bot.send_message(chat_id=update.message.chat_id, text="asdasdasdfaddfasdfbdaskjhfbaweivhbawerihvkbawdiyuvhbasdvikujwaedbviawdyhvb asdkijvhbasdf ikvhsbadvikahsdbv ikasdhjvbdsawiukjhvbawdsiuhjvbsadiouvb sodubfvwdsoufbwsdaioujvbisaduhjbvciaskdub")
    else:
        bot.send_message(chat_id=update.message.chat_id, text="Mi no entender")

def unknown(bot, update):
    try:
        logger = _get_logger()
        _bot_history("unknown",update,None)
        if not _authenticate(update):
            bot.send_message(chat_id=update.message.chat_id, text="Grupo invalido")
            return
        bot.send_message(chat_id=update.message.chat_id, text="Mi no entender")
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def xavi_gato(bot, update):
    try:
        logger = _get_logger()
        mensajes_array = ["Xavi salvaje",
        "Xavi, no me hables, soy un puto robot",
        "Xavi DEJAME EN PAZ",
        "Xavi la puta madre",
        "Xavi...",
        "Mi no entender... xavi...",
        "Cuantos xavis se necesitan para cambiar una lamparita?",
        "Xavi. SOY. UN. BOT!",
        "Xavi, te llama fran",
        "Xavi vamos a comer?",
        "Ivax",
        "List out of xavix",
        "Mira mi huevo",
        "Esto te va a fazinar",
        "Cebollas te hacen llorar?",
        "Necesito mandar plugines a produccion",
        "El de arriba es bobo",
        "Xavi, te nomino a bobo del mes"]
        
        bot.send_message(chat_id=update.message.chat_id, text=str(mensajes_array[randint(0, len(mensajes_array)-1)]))
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return
    
