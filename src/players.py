from src import mongoConnection as mongo
import config
from src.utils import exception_handler, admin_command
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

@exception_handler
def add_player(bot, update):
    user_data = {
        "code": str(update.message.from_user.id),
        "username": str(update.message.from_user.username)
    }
    if mongo.find_one(config.get("PLAYERS_COLLECTION"), {"code": user_data['code']}):
        bot.send_message(chat_id=update.message.chat_id, text="Ya estas cargado!" )
    else:
        mongo.insert_one(config.get("PLAYERS_COLLECTION"), user_data)
        bot.send_message(chat_id=update.message.chat_id, text="Se te agrego exitosamente!" )

@exception_handler
def players_list(bot, update):
    users = mongo.find(config.get("PLAYERS_COLLECTION"), {})
    response = "Jugadores: "
    for user in users:
        response = response + "\n" + user["username"]
    bot.send_message(chat_id=update.message.chat_id, text=response)

@exception_handler
def player_statics(bot, update):
    users = mongo.find(config.get("PLAYERS_COLLECTION"), {})

    keyboard = [ 
        [ InlineKeyboardButton(user["username"], callback_data= "player&"+str(user["code"])) for user in users]
    ]
                
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Seleccioná:', reply_markup=reply_markup)

def _get_player_statics(bot, player, chat_id):
    bot.send_message(chat_id=chat_id, text="Probanding" )

@exception_handler
@admin_command
def remove_player(bot, update):
    users = mongo.find(config.get("PLAYERS_COLLECTION"), {})

    keyboard = [ 
        [ InlineKeyboardButton(user["username"], callback_data= "player-remove&"+str(user["code"])) for user in users]
    ]
                
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Seleccioná:', reply_markup=reply_markup)

def _remove_player(bot, player, chat_id):
    mongo.remove_by_query(config.get("PLAYERS_COLLECTION"), {"code": str(player[0])})
    bot.send_message(chat_id=chat_id, text="Usuario removido con éxito" )
