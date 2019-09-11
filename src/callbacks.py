# -*- coding: utf-8; -*-
from src.players import _get_player_statics, _remove_player
from src.games import _submit_score_1, _submit_score_2, _submit_score, _submit_cancel, _submit_confirm, _submit_dobles_oponentes1, _submit_dobles_oponentes2
from src.utils import exception_handler

@exception_handler
def inline_button_callback(bot, update):
    data = update.callback_query.data.split("&")
    flag = update.callback_query.data.split("&")[0]
    data = "".join(data[1:])

    bot.delete_message(chat_id=update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id, reply_markup=None)
    if flag == "player":
        _get_player_statics(bot, data, update.callback_query.message.chat_id)
    elif flag == "player-remove":
        _remove_player(bot, data, update.callback_query.message.chat_id)
    elif flag == "game_submit":
        _submit_score_1(bot, data, update.callback_query.message.chat_id)
    elif flag == "game_score1":
        _submit_score_2(bot, data, update.callback_query.message.chat_id)
    elif flag == "game_score2":
        _submit_score(bot, data, update.callback_query.message.chat_id)
    elif flag == "game_dobles1":
        _submit_dobles_oponentes1(bot, data, update.callback_query.message.chat_id)
    elif flag == "game_dobles2":
        _submit_dobles_oponentes2(bot, data, update.callback_query.message.chat_id)
    elif flag == "game_submit_confirm":
        _submit_confirm(bot, data, update.callback_query.message.chat_id)
    elif flag == "game_submit_cancel":
        _submit_cancel(bot, data, update.callback_query.message.chat_id)
    elif flag == "cancelar":
        pass
    else:
        raise Exception("Error en callback handler")