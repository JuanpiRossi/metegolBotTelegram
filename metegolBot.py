from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, InlineQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, ParseMode
import botConfig
from metegolCommands import add_player,\
                            remove_player,\
                            players_list,\
                            player_info,\
                            _help,\
                            unknown,\
                            submit_result_goals,\
                            player_statics,\
                            get_elo

updater = Updater(token=botConfig.BOT_TOKEN)
dispatcher = updater.dispatcher


# Handlers
add_player_handler = CommandHandler('nuevojugador', add_player, pass_args=True)
remove_player_handler = CommandHandler('eliminarjugador', remove_player, pass_args=True)
players_list_handler = CommandHandler('listajugadores', players_list)
ranking_handler = CommandHandler('ranking', get_elo)
player_info_handler = CommandHandler('estadisticasjugador', player_statics, pass_args=True)
player_games_handler = CommandHandler('partidosjugador', player_info, pass_args=True)
submit_handler = CommandHandler('submit', submit_result_goals, pass_args=True)
help_handler = CommandHandler('help', _help)
unknown_handler = MessageHandler(Filters.command, unknown)

# Dispatchers
dispatcher.add_handler(add_player_handler)
dispatcher.add_handler(remove_player_handler)
dispatcher.add_handler(players_list_handler)
dispatcher.add_handler(ranking_handler)
dispatcher.add_handler(player_info_handler)
dispatcher.add_handler(player_games_handler)
dispatcher.add_handler(submit_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(unknown_handler)

updater.start_polling()
updater.idle()
