from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, InlineQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, ParseMode
import tokenConfig
from metegolCommands import add_player,\
                            remove_player,\
                            players_list,\
                            player_info,\
                            _help,\
                            unknown,\
                            submit_result_goals,\
                            player_statics,\
                            get_elo,\
                            admin_player_info,\
                            admin_remove_game,\
                            _help_admin,\
                            set_elo,\
                            alive,\
                            recalculate_elo,\
                            link,\
                            start_league,\
                            common_message,\
                            join_league,\
                            submit_league,\
                            league_leaderboard,\
                            league_games,\
                            get_elo_weekly,\
                            bardeandopuntocom,\
                            agregar_a_liga

updater = Updater(token=tokenConfig.BOT_TOKEN)
dispatcher = updater.dispatcher


# Handlers]]
add_player_handler = CommandHandler('nuevojugador', add_player, pass_args=True)
players_list_handler = CommandHandler('listajugadores', players_list)
ranking_handler = CommandHandler('ranking', get_elo)
get_elo_weekly_handler = CommandHandler('semanal', get_elo_weekly)
player_info_handler = CommandHandler('estadisticasjugador', player_statics, pass_args=True)
player_games_handler = CommandHandler('partidosjugador', player_info, pass_args=True)
submit_handler = CommandHandler('submit', submit_result_goals, pass_args=True)
submit_league_handler = CommandHandler('submitliga', submit_league, pass_args=True)
link_handler = CommandHandler('link', link, pass_args=True)
alive_handler = CommandHandler('alive', alive)
join_league_handler = CommandHandler('joinliga', join_league)
start_league_handler = CommandHandler('startliga', start_league)
league_leaderboard_handler = CommandHandler('rankingliga', league_leaderboard)
league_games_handler = CommandHandler('partidosliga', league_games)
help_handler = CommandHandler('help', _help)
barding_handler = CommandHandler("bard",bardeandopuntocom, pass_args=True)
common_message_handler = MessageHandler(Filters.text, common_message)

#Admin handlers
admin_player_games_handler = CommandHandler('partidosjugadoradmin', admin_player_info, pass_args=True)
remove_player_handler = CommandHandler('eliminarjugador', remove_player, pass_args=True)
admin_remove_game_handler = CommandHandler('removegame', admin_remove_game, pass_args=True)
set_elo_handler = CommandHandler('setelo', set_elo, pass_args=True)
help_admin_handler = CommandHandler('helpadmin', _help_admin)
recalculate_handler = CommandHandler('recalculate', recalculate_elo)
agregar_liga_handler = CommandHandler('agregarliga', agregar_a_liga, pass_args=True)


# Dispatchers
dispatcher.add_handler(add_player_handler)
dispatcher.add_handler(players_list_handler)
dispatcher.add_handler(ranking_handler)
dispatcher.add_handler(barding_handler)
# dispatcher.add_handler(get_elo_weekly_handler)
dispatcher.add_handler(player_info_handler)
dispatcher.add_handler(player_games_handler)
dispatcher.add_handler(league_games_handler)
dispatcher.add_handler(submit_handler)
dispatcher.add_handler(link_handler)
dispatcher.add_handler(alive_handler)
dispatcher.add_handler(submit_league_handler)
dispatcher.add_handler(join_league_handler)
dispatcher.add_handler(league_leaderboard_handler)
dispatcher.add_handler(start_league_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(common_message_handler)

#Admin Dispatchers
dispatcher.add_handler(admin_player_games_handler)
dispatcher.add_handler(admin_remove_game_handler)
dispatcher.add_handler(remove_player_handler)
dispatcher.add_handler(set_elo_handler)
dispatcher.add_handler(help_admin_handler)
dispatcher.add_handler(recalculate_handler)
dispatcher.add_handler(agregar_liga_handler)


unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

updater.start_polling()
updater.idle()
