import logging
from botConfig import GROUPS
import datetime

def _get_logger():
    logger = logging.getLogger('metegol')
    fh = logging.FileHandler('spam.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

def _authenticate(update):
    if update.message.chat.id not in GROUPS:
        return False
    return True

def _get_elo_constants(elo_player):
    if elo_player < 1000:
        return 48
    elif elo_player < 1400:
        return 40
    elif elo_player < 1800:
        return 32
    elif elo_player < 2100:
        return 20
    elif elo_player < 2400:
        return 12
    else:
        return 4

def _calculate_elo(elo_player_a, elo_player_b, player_a_goals, player_b_goals):
    player_a_transformed = 10**(elo_player_a/400)
    player_b_transformed = 10**(elo_player_a/400)

    player_a_expect_score = player_a_transformed / (player_a_transformed+player_b_transformed)
    player_b_expect_score = player_b_transformed / (player_a_transformed+player_b_transformed)

    player_a_constant = _get_elo_constants(elo_player_a)
    player_b_constant = _get_elo_constants(elo_player_b)

    new_player_a_elo = int(elo_player_a + player_a_constant*(int(player_a_goals>player_b_goals)-player_a_expect_score))
    new_player_b_elo = int(elo_player_b + player_b_constant*(int(player_b_goals>player_a_goals)-player_b_expect_score))

    return new_player_a_elo,new_player_b_elo

def _bot_history(command,update,message):
    with open("history.log","a+") as history:
        person = update.message.from_user.username
        if update["message"]["chat"]["type"] == 'group':
            group = update["message"]["chat"]["title"]
            history.write(str(datetime.datetime.now()) + " - " + str(person) + " - " + str(command) + " - " + str(group) + "\n")
        elif update["message"]["chat"]["type"] == 'private':
            history.write(str(datetime.datetime.now()) + " - " + str(person) + " - " + str(command)  + " - " + str(message) + "\n")
        else:
            history.write(str(datetime.datetime.now()) + " - " + str(person) + " - " + str(command) + " - " + str(update) + "\n")