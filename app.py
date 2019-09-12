# -*- coding: utf-8; -*-
# TELEGRAM
from telegram.ext import CommandHandler, Updater, CallbackQueryHandler, Filters, MessageHandler

# CONFIG
import enviroment

# COMMAND FUNCTIONS
from src import alive
from src import players
from src import games
from src import ranking
from src import random
from src import weekly

# UTILS
from src.utils import exception_handler, admin_command

# CALLBACKS
from src import callbacks

# EXTRAS
import schedule
import time
import threading


updater = Updater(token=enviroment.BOT_TOKEN)
dispatcher = updater.dispatcher


def shutdown():
    updater.stop()
    updater.is_idle = False


@admin_command
@exception_handler
def stop(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Stopping....")
    threading.Thread(target=shutdown).start()


# Alive
dispatcher.add_handler(CommandHandler('alive', alive.alive))

# Players
dispatcher.add_handler(CommandHandler('start', players.add_player))
dispatcher.add_handler(CommandHandler('listajugadores', players.players_list))
dispatcher.add_handler(CommandHandler('estadisticasjugadores', players.player_statics))
dispatcher.add_handler(CallbackQueryHandler(callbacks.inline_button_callback))

# Games
dispatcher.add_handler(CommandHandler('submit', games.submit))
dispatcher.add_handler(CommandHandler('submit2', games.submit_dobles))

# Ranking
dispatcher.add_handler(CommandHandler('ranking', ranking.ranking))

# Weekly
dispatcher.add_handler(CommandHandler('ranking_semanal', weekly.ranking))

# Players - admin
dispatcher.add_handler(CommandHandler('eliminarjugador', players.remove_player))
dispatcher.add_handler(CommandHandler('stop', stop))

# Utils
dispatcher.add_handler(CommandHandler('bard', random.bard, pass_args=True))
dispatcher.add_handler(CommandHandler('random', random.random, pass_args=True))
dispatcher.add_handler(CommandHandler('help', random.help))
dispatcher.add_handler(MessageHandler(Filters.command, random.unknown))


print("starting")
updater.start_polling()


schedule.every().monday.do(weekly.show_weekly_ranking)

while True:
    schedule.run_pending()
    time.sleep(1)


# OLD
# # Handlers]]
# submit_handler = CommandHandler('submit', submit_result_goals, pass_args=True)
# submit_league_handler = CommandHandler('submitliga', submit_league, pass_args=True)
# join_league_handler = CommandHandler('joinliga', join_league)
# start_league_handler = CommandHandler('startliga', start_league)
# start_torneo_handler = CommandHandler('starttorneo', start_torneo)
# league_leaderboard_handler = CommandHandler('rankingliga', league_leaderboard)
# league_games_handler = CommandHandler('partidosliga', league_games)

# #Admin handlers
# admin_player_games_handler = CommandHandler('partidosjugadoradmin', admin_player_info, pass_args=True)
# remove_player_handler = CommandHandler('eliminarjugador', remove_player, pass_args=True)
# admin_remove_game_handler = CommandHandler('removegame', admin_remove_game, pass_args=True)
# set_elo_handler = CommandHandler('setelo', set_elo, pass_args=True)
# help_admin_handler = CommandHandler('helpadmin', _help_admin)
# recalculate_handler = CommandHandler('recalculate', recalculate_elo)
# agregar_liga_handler = CommandHandler('agregarliga', agregar_a_liga, pass_args=True)
# terminar_liga_handler = CommandHandler('terminarliga', end_league)