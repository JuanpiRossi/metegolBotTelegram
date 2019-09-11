# -*- coding: utf-8; -*-
def alive(bot, update):
    print("Entro al print" + str(update.message.chat.id))
    bot.send_message(chat_id=update.message.chat_id, text="Estoy vivito en el grupo: " + str(update.message.chat.id))