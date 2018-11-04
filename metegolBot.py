from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, InlineQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, ParseMode
import botConfig
from pymongo import MongoClient, DESCENDING
import logging
import itertools
import imgkit
import uuid
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

def startMongo():
    client = MongoClient('mongodb://aiun:9980054a@144.202.60.128:27017/',)
    return client.statsMetegol

updater = Updater(token=botConfig.BOT_TOKEN)
dispatcher = updater.dispatcher

def add_player(bot, update, args):
    logging.info(args)
    if not args:
        bot.send_message(chat_id=update.message.chat_id, text="Por favor, agregar nombre del jugador")
    elif len(args) != 1:
        bot.send_message(chat_id=update.message.chat_id, text="Por favor, el nombre del jugador no puede tener espacios")
    else:
        try:
            player = db["jugadores"].find_one({"__$name":args[0]})
            if not player:
                mongo_response = db["jugadores"].insert_one({"__$name":args[0]})
            else:
                bot.send_message(chat_id=update.message.chat_id, text="El jugador ya existe")
                return
        except Exception as ex:
            bot.send_message(chat_id=update.message.chat_id, text=str(ex))
            return
        bot.send_message(chat_id=update.message.chat_id, text="Jugador agregado con exito")

def remove_player(bot, update, args):
    logging.info(args)
    if not args:
        bot.send_message(chat_id=update.message.chat_id, text="Por favor, agregar nombre del jugador")
    elif len(args) != 1:
        bot.send_message(chat_id=update.message.chat_id, text="Por favor, el nombre del jugador no puede tener espacios")
    else:
        try:
            query = {}
            query[args[0]] = {"$exists":True}
            db["jugadores"].remove({"__$name":args[0]})
            players = db["jugadores"].find(query)
            for player in players:
                player.pop(args[0])
                db["jugadores"].update({'__$name':player['__$name']}, player, upsert=False)
        except Exception as ex:
            bot.send_message(chat_id=update.message.chat_id, text=str(ex))
            return
        
        bot.send_message(chat_id=update.message.chat_id, text="Jugador eliminado con exito")

def players_list(bot, update):
    try:
        players = db["jugadores"].find({})
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        return
    message = "Jugadores ( {} ):\n".format(players.count())
    for player in players:
        message = message + player["__$name"] + "\n"
    bot.send_message(chat_id=update.message.chat_id, text=message)

def player_info(bot, update, args):
    logging.info(args)
    if not args:
        bot.send_message(chat_id=update.message.chat_id, text="Por favor, agregar nombre del jugador")
    elif len(args) != 1:
        bot.send_message(chat_id=update.message.chat_id, text="Por favor, el nombre del jugador no puede tener espacios")
    else:
        try:
            player = db["jugadores"].find_one({"__$name":args[0]})
        except Exception as ex:
            bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        if not player:
            bot.send_message(chat_id=update.message.chat_id, text="El jugador no existe")
        else:
            message = "Estadisticas de " + str(args[0]) + "\n"
            for key in player:
                if key != "__$name" and key != "_id":
                    message = message + str(args[0]) + ": " + str(player[key]["win"]) + " / " + str(key) + ": " + str(player[key]["lose"]) + "\n"
            bot.send_message(chat_id=update.message.chat_id, text=message)

def two_players_info(bot, update, args):
    logging.info(args)
    if not args:
        bot.send_message(chat_id=update.message.chat_id, text="Por favor, agregar nombre de los jugadores")
    elif len(args) < 2:
        bot.send_message(chat_id=update.message.chat_id, text="Por favor, escriba el nombre de 2 jugadores")
    elif len(args) > 2:
        bot.send_message(chat_id=update.message.chat_id, text="Por favor, solo agregue 2 jugadores")
    else:
        try:
            player = db["jugadores"].find_one({"__$name":args[0]})
        except Exception as ex:
            bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        if not player:
            bot.send_message(chat_id=update.message.chat_id, text="El jugador no existe")
        else:
            bot.send_message(chat_id=update.message.chat_id, text=str(args[0])+": "+str(player[args[1]]["win"])+" / "+str(args[1])+": "+str(player[args[1]]["lose"]))

def submit_result(bot, update, args):
    if not args or len(args) != 5 or args[2] != '/':
        bot.send_message(chat_id=update.message.chat_id, text="Por favor, ingrese con el formato correcto (JUGADOR1 # / JUGADOR2 #)")
    else:
        try:
            int(args[1])
            int(args[4])
        except:
            bot.send_message(chat_id=update.message.chat_id, text="Por favor, cargar valores numericos despues del nombre del jugador")
            return
        try:
            player1 = db["jugadores"].find_one({"__$name":args[0]})
            player2 = db["jugadores"].find_one({"__$name":args[3]})
        except Exception as ex:
            bot.send_message(chat_id=update.message.chat_id, text=str(ex))
            return
        if not player1:
            bot.send_message(chat_id=update.message.chat_id, text="No se encontro al jugador: " + str(args[0]))
            return
        if not player2:
            bot.send_message(chat_id=update.message.chat_id, text="No se encontro al jugador: " + str(args[3]))
            return
        player1[args[3]] = {"win": int(args[1]), "lose": int(args[4])}
        player2[args[0]] = {"win": int(args[4]), "lose": int(args[1])}
        try:
            db["jugadores"].update({'__$name':args[0]}, player1, upsert=False)
            db["jugadores"].update({'__$name':args[3]}, player2, upsert=False)
        except Exception as ex:
            bot.send_message(chat_id=update.message.chat_id, text=str(ex))
            return
        bot.send_message(chat_id=update.message.chat_id, text="Estadisticas cargadas con exito")

def scoreboard(bot, update):
    try:
        players_dict = {}
        results_list = []
        players_name = db["jugadores"].find({}).distinct("__$name")
        players = db["jugadores"].find({})
        for player in players:
            players_dict[player["__$name"]] = player
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        return
    possibilities = list(itertools.combinations(players_name, 2))
    if not possibilities:
        bot.send_message(chat_id=update.message.chat_id, text="Ocurrio un error al calcular las estadisticas")

    for possibility in possibilities:
        tmp = {}
        tmp[possibility[0]] = 0 if not possibility[1] in players_dict[possibility[0]] else players_dict[possibility[0]][possibility[1]]["win"]
        tmp[possibility[1]] = 0 if not possibility[1] in players_dict[possibility[0]] else players_dict[possibility[0]][possibility[1]]["lose"]
        results_list.append(tmp)

    html = "<!DOCTYPE html><html><head><style>table {font-family: arial, sans-serif; border-collapse: collapse;width:500px;}td, th {border: 1px solid #dddddd;text-align: left;padding: 8px;}.centerColumn {background-color: #dddddd;}.nameColumn{max-width:100%;}.pointColumn{width:25px;}</style></head><body><h2>Estadisticas</h2><table>"
    html_end = "</table></body></html>"
    for result in results_list:
        keys = list(result.keys())
        if result[keys[0]] != 0 and result[keys[1]] != 0:
            html = html+"<tr><td class='nameColumn'>{PLAYER1}</td><td class='pointColumn'>{POINT1}</td><td class='centerColumn'> </td><td class='pointColumn'>{POINT2}</td><td class='nameColumn'>{PLAYER2}</td></tr>".format(PLAYER1=str(keys[0]),POINT1=str(result[keys[0]]),POINT2=str(result[keys[1]]),PLAYER2=str(keys[1]))
    html = html+html_end

    file_name = str(uuid.uuid4())+".png"
    path_wkthmltopdf = r'D:\wkhtmltopdf\bin\wkhtmltoimage.exe'
    config = imgkit.config(wkhtmltoimage=path_wkthmltopdf)
    options = {
        'format': 'png',
        'encoding': "UTF-8",
        'crop-w': '515'
    }
    imgkit.from_string(html, file_name, options=options, config=config)
    file = open(file_name,'rb')
    bot.send_photo(chat_id=update.message.chat_id, photo=file)
    file.close()
    os.remove(file_name)

def ranking(bot, update):
    try:
        players_dict = {}
        results_list = []
        points_dict = {}
        points_list = []
        players_name = db["jugadores"].find({}).distinct("__$name")
        players = db["jugadores"].find({})
        for player in players:
            players_dict[player["__$name"]] = player
    except Exception as ex:
        bot.send_message(chat_id=update.message.chat_id, text=str(ex))
        return
    possibilities = list(itertools.combinations(players_name, 2))
    if not possibilities:
        bot.send_message(chat_id=update.message.chat_id, text="Ocurrio un error al calcular las estadisticas")

    for possibility in possibilities:
        tmp = {}
        tmp[possibility[0]] = 0 if not possibility[1] in players_dict[possibility[0]] else players_dict[possibility[0]][possibility[1]]["win"]
        tmp[possibility[1]] = 0 if not possibility[1] in players_dict[possibility[0]] else players_dict[possibility[0]][possibility[1]]["lose"]
        results_list.append(tmp)
    
    for result in results_list:
        keys = list(result.keys())
        if result[keys[0]] != 0 and result[keys[1]] != 0:
            if result[keys[0]] > result[keys[1]]:
                if not keys[0] in points_dict:
                    points_dict[keys[0]] = 3
                else:
                    points_dict[keys[0]] = points_dict[keys[0]] + 3
            elif result[keys[0]] < result[keys[1]]:
                if not keys[1] in points_dict:
                    points_dict[keys[1]] = 3
                else:
                    points_dict[keys[1]] = points_dict[keys[1]] + 3
            else:
                if not keys[0] in points_dict:
                    points_dict[keys[0]] = 1
                else:
                    points_dict[keys[0]] = points_dict[keys[0]] + 1
                if not keys[1] in points_dict:
                    points_dict[keys[1]] = 1
                else:
                    points_dict[keys[1]] = points_dict[keys[1]] + 1
    for player in players_name:
        if player not in list(points_dict.keys()):
            points_dict[player] = 0
    points_list = [{"NOMBRE":key,"PUNTOS":points_dict[key]} for key in points_dict]
    points_list = sorted(points_list, key=lambda k: k['PUNTOS'], reverse=True) 

    html = "<!DOCTYPE html><html><head><style>table {font-family: arial, sans-serif;border-collapse: collapse;width: 300px;}td, th {border: 1px solid #dddddd;text-align: left;padding: 8px;}.header {background-color: #dddddd;}.nameColumn {width: 250px;}.pointColumn {width: 50px;}</style></head><body><h2>Ranking</h2><table><tr><td class='nameColumn header'>Nombre</td><td class='pointColumn header'>Puntos</td></tr>"
    html_end = "</table></body></html>"
    for result in points_list:
        html = html+"<tr><td class='nameColumn'>{NOMBRE}</td><td class='pointColumn'>{PUNTOS}</td></tr>".format(**result)
    html = html+html_end

    file_name = str(uuid.uuid4())+".png"
    path_wkthmltopdf = r'D:\wkhtmltopdf\bin\wkhtmltoimage.exe'
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

def _help(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="""Lista de comandos:
/agregarjugador JUGADOR` - Agregar jugador`
/eliminarjugador JUGADOR` - Eliminar jugador`
/jugadores` - Lista de jugadores`
/estadisticasjugador JUGADOR` - Estadisticas del jugador`
/cargarestadisticas JUGADOR1 # / JUGADOR2 #` - Estadisticas del jugador`
/estadisticas` - Mostrar estadisticas`
/estadisticasjugadores JUGADOR1 JUGADOR2` - Estadisticas entre dos jugadores`
/ranking` - Mostrar ranking`""", parse_mode=ParseMode.MARKDOWN)

def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Mi no entender")


db = startMongo()

# Handlers
add_player_handler = CommandHandler('agregarjugador', add_player, pass_args=True)
remove_player_handler = CommandHandler('eliminarjugador', remove_player, pass_args=True)
players_list_handler = CommandHandler('listajugadores', players_list)
ranking_handler = CommandHandler('ranking', ranking)
player_info_handler = CommandHandler('estadisticasjugador', player_info, pass_args=True)
two_players_info_handler = CommandHandler('estadisticasjugadores', two_players_info, pass_args=True)
submit_result_handler = CommandHandler('cargarestadisticas', submit_result, pass_args=True)
scoreboard_handler = CommandHandler('estadisticas', scoreboard)
help_handler = CommandHandler('help', _help)
unknown_handler = MessageHandler(Filters.command, unknown)

# Dispatchers
dispatcher.add_handler(add_player_handler)
dispatcher.add_handler(remove_player_handler)
dispatcher.add_handler(players_list_handler)
dispatcher.add_handler(ranking_handler)
dispatcher.add_handler(player_info_handler)
dispatcher.add_handler(two_players_info_handler)
dispatcher.add_handler(scoreboard_handler)
dispatcher.add_handler(submit_result_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(unknown_handler)

updater.start_polling()
updater.idle()
