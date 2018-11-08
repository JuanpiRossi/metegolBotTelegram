from mongoConnection import startMongo,find_one,find,update_doc,insert_one,remove_by_query
from telegram import InlineQueryResultArticle, InputTextMessageContent, ParseMode
import itertools
import imgkit
import uuid
import os
from utilities import _calculate_elo, _get_logger, _authenticate, _authenticate_admin,_bot_history, _get_average_stats
from datetime import datetime
from botConfig import WKHTMLTOIMAGE_PATH

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
        player = find_one("jugadores",{"__$name":args[0]})
        if not player:
            mongo_response = insert_one("jugadores",{"__$name":args[0],"__$elo":1200,"__$history":[]})
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
        remove_by_query("jugadores",{"__$name":args[0]})
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
        players = find("jugadores",{})
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
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, agregar nombre del jugador")
            return
        elif len(args) != 1:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, el nombre del jugador no puede tener espacios")
            return
        
        player = find_one("jugadores",{"__$name":args[0]})
        if not player:
            bot.send_message(chat_id=update.message.chat_id, text="El jugador no existe")
            return
        message = "Partidos de " + str(args[0]) + "\n"
        for game in player["__$history"]:
            enemy = [player for player in list(game.keys()) if "__$" not in player]
            if len(enemy)==1:
                enemy = enemy[0]
                message = message + "- " + str(args[0]) + ": " + str(game["__$own"]) + " | " + str(enemy) + ": " + str(game[enemy]) + "\n"
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
        
        player = find_one("jugadores",{"__$name":args[0]})
        if not player:
            bot.send_message(chat_id=update.message.chat_id, text="El jugador no existe")
            return
        message = "Partidos de " + str(args[0]) + "\n"
        for game in player["__$history"]:
            enemy = [player for player in list(game.keys()) if "__$" not in player]
            if len(enemy)==1:
                enemy = enemy[0]
                message = message + "- " + str(args[0]) + ": " + str(game["__$own"]) + " | " + str(enemy) + ": " + str(game[enemy]) + " / " + game["__$game_id"] + "\n"
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
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, agregar nombre del jugador")
            return
        elif len(args) != 1:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, el nombre del jugador no puede tener espacios")
            return

        player = find_one("jugadores",{"__$name":args[0]})
        if not player:
            bot.send_message(chat_id=update.message.chat_id, text="El jugador no existe")
            return
        message = "Estadisticas de " + str(args[0]) + "\n"
        games_dict = {}
        for game in player["__$history"]:
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
            message = message + str(args[0]) + ": " + str(games_dict[key]["own"]) + " | " + str(key) + ": " + str(games_dict[key]["enemy"]) + " - (" + str(round(percent,1)) + "%)\n"

        average_goals, average_percent_games = _get_average_stats(player)
        message = message + "Promedio de goles: " + str(average_goals) + "\n"
        message = message + "Promedio de partidos ganados: " + str(average_percent_games) + "%\n"
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
            return
        if not args:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, cargue algun dato")
            return
        elif len(args) != 4:
            bot.send_message(chat_id=update.message.chat_id, text="La estructura del comando es: JUGADOR1 # JUGADOR2 #")
            return
        try:
            int(args[1])
            int(args[3])
        except:
            bot.send_message(chat_id=update.message.chat_id, text="Debe cargar goles numericos")
            return


        player_a = find_one("jugadores",{"__$name":args[0]})
        if not player_a:
            bot.send_message(chat_id=update.message.chat_id, text="El primero jugador no existe")
            return
        player_b = find_one("jugadores",{"__$name":args[2]})
        if not player_b:
            bot.send_message(chat_id=update.message.chat_id, text="El segundo jugador no existe")
            return
        player_a_elo,player_b_elo = _calculate_elo(player_a["__$elo"], player_b["__$elo"], int(args[1]), int(args[3]))
        player_a_dif = ("+" if player_a_elo-player_a["__$elo"] > 0 else "-") + str(abs(player_a_elo-player_a["__$elo"]))
        player_b_dif = ("+" if player_b_elo-player_b["__$elo"] > 0 else "-") + str(abs(player_b_elo-player_b["__$elo"]))
        player_a["__$elo"] = player_a_elo
        player_b["__$elo"] = player_b_elo
        game_id = str(uuid.uuid4())
        match_history_a = {"__$date":datetime.today(),"__$own":int(args[1]), "__$game_id":game_id}
        match_history_a[str(args[2])] = int(args[3])
        match_history_b = {"__$date":datetime.today(),"__$own":int(args[3]), "__$game_id":game_id}
        match_history_b[str(args[0])] = int(args[1])
        player_a["__$history"].append(match_history_a)
        player_b["__$history"].append(match_history_b)
        update_doc("jugadores",{"__$name":args[0]},player_a)
        update_doc("jugadores",{"__$name":args[2]},player_b)
        bot.send_message(chat_id=update.message.chat_id, text="Partido cargado con exito\n"+
                                                            str(args[0])+ " (" + player_a_dif +"): "+str(player_a_elo)+"\n"+
                                                            str(args[2])+ " (" + player_b_dif +"): "+str(player_b_elo)+"\n"+
                                                            str(game_id))

    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return
    
def get_elo(bot, update):
    try:
        logger = _get_logger()
        _bot_history("get_elo",update,None)
        if not _authenticate(update):
            bot.send_message(chat_id=update.message.chat_id, text="Grupo invalido")
            return
        players = find("jugadores",{},sort="-__$elo")
        html = "<!DOCTYPE html><html><head><style>table {font-family: arial, sans-serif;border-collapse: collapse;width: 300px;}td, th {border: 1px solid #dddddd;text-align: left;padding: 8px;}.header {background-color: #dddddd;}.nameColumn {width: 250px;}.pointColumn {width: 50px;}</style></head><body><h2>Ranking</h2><table><tr><td class='nameColumn header'>Nombre</td><td class='pointColumn header'>Puntos:</td></tr>"
        for player in players:
            html = html+"<tr><td class='nameColumn'>{NOMBRE}</td><td class='pointColumn'>{PUNTOS}</td></tr>".format(NOMBRE=player["__$name"],PUNTOS=player["__$elo"])
        html = html+"</table></body></html>"
        file_name = str(uuid.uuid4())+".png"
        path_wkthmltopdf = WKHTMLTOIMAGE_PATH
        config = imgkit.config(wkhtmltoimage=path_wkthmltopdf)
        options = {
            'format': 'png',
            'encoding': "UTF-8",
            'crop-w': '315'
        }
        imgkit.from_string(html, file_name, options=options, config=config)
        file = open(file_name,'rb')
        bot.send_photo(chat_id=update.message.chat_id, photo=file)
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
        players = find("jugadores",query)
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
            update_doc("jugadores",{"__$name":player["__$name"]},new_data)
        bot.send_message(chat_id=update.message.chat_id, text="Exito al borrar la partida:\n"+str(partida))
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def set_elo(bot,update,args):
    try:
        logger = _get_logger()
        _bot_history("set_elo",update,args)
        # Validaciones de argumentos
        if not _authenticate_admin(update):
            bot.send_message(chat_id=update.message.chat_id, text="Requiere autorizacion de un administrador")
            return
        if not args or len(args) != 2:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, ingresar nombre de jugador y su nuevo elo")
            return
        
        player = find_one("jugadores",{"__$name":args[0]})
        if not player:
            bot.send_message(chat_id=update.message.chat_id, text="No se encontro al jugador")
            return
        player["__$elo"] = int(args[1])
        update_doc("jugadores",{"__$name":args[0]},player)
        bot.send_message(chat_id=update.message.chat_id, text="Exito al actualizar el elo")
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
/nuevojugador JUGADOR - `Permite agregar un jugador nuevo`
/listajugadores - `Muestra una lista de jugadores`
/ranking - `Muestra el puntaje de los jugadores`
/estadisticasjugador JUGADOR - `Permite ver las estadisticas de un jugador`
/partidosjugador JUGADOR - `Permite ver los partidos de un jugador`
/submit JUGADOR1 GOLES1 JUGADOR2 GOLES2 - `Permite ingresar un nuevo partido`""", parse_mode=ParseMode.MARKDOWN)
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        logger.exception(ex)
        return

def _help_admin(bot, update):
    try:
        logger = _get_logger()
        _bot_history("_help_admin",update,None)
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