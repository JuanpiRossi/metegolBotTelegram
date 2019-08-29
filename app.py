# TELEGRAM
from telegram.ext import CommandHandler, Updater, CallbackQueryHandler

# CONFIG
import enviroment
import config

# COMMAND FUNCTIONS
from src import alive
from src import players

# CALLBACKS
from src import callbacks

updater = Updater(token=enviroment.BOT_TOKEN)
dispatcher = updater.dispatcher

# Alive
dispatcher.add_handler(CommandHandler('alive', alive.alive))

# Players
dispatcher.add_handler(CommandHandler('start', players.add_player))
dispatcher.add_handler(CommandHandler('listajugadores', players.players_list))
dispatcher.add_handler(CommandHandler('estadisticasjugadores', players.player_statics))
dispatcher.add_handler(CallbackQueryHandler(callbacks.inline_button_callback))


# Players - admin
dispatcher.add_handler(CommandHandler('eliminarjugador', players.remove_player))

print("starting")
updater.start_polling()
updater.idle()



