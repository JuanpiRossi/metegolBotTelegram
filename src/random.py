# -*- coding: utf-8; -*-
from src.utils import exception_handler
import itertools
from random import randint


@exception_handler
def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Mi no entender")


@exception_handler
def random(bot, update, args):
    combinations = itertools.combinations(args, 2)
    if len(args) != 4:
        bot.send_message(chat_id=update.message.chat_id, text="Solo se permiten 4 jugadores")
        return
    combinations = list(combinations)[randint(0,5)]
    
    second_team = []
    for player in args:
        if player not in combinations:
            second_team.append(player)
    bot.send_message(chat_id=update.message.chat_id, text="{} & {}  VS  {} & {}".format(combinations[0],combinations[1],second_team[0],second_team[1]))


@exception_handler
def bard(bot, update, args):
    if str(update.message.from_user.id) == "528527409":
        speak_chat = args[0]
        message = " ".join(args[1:])
        bot.send_message(chat_id=speak_chat, text=str(message))
    else:
        bot.send_message(chat_id=update.message.chat_id, text="Mi no entender")


@exception_handler
def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="""Lista de comandos:
/start - Permite ingresar a la lista de jugadores del bot
/listajugadores - Lista de jugadores
/estadisticasjugadores - Estadisticas de un jugador
/submit - Cargar un partido
/submit2 - Cargar un partido doble
/ranking - Ranking!
/ranking_semanal - Ranking semanal!
/random $p1 $p2 $p3 $p4 - Devuelve 2 equipos randoms con cada persona ingresada
/help - Si no entendes un carajo""")
