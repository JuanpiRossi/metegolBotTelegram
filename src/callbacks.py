from src.players import _get_player_statics, _remove_player
from src.utils import exception_handler

@exception_handler
def inline_button_callback(bot, update):
    data = update.callback_query.data.split("&")
    bot.editMessageReplyMarkup(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, reply_markup=None)
    if data[0] == "player":
        _get_player_statics(bot, data[1:], update.callback_query.message.chat_id)
    elif data[0] == "player-remove":
        _remove_player(bot, data[1:], update.callback_query.message.chat_id)