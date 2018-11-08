import logging
from botConfig import GROUPS,ADMIN
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

def _authenticate_admin(update):
    if update.message.chat.id not in ADMIN:
        return False
    return True

def _get_elo_constants(elo_player,constant_array=[]):
    if not constant_array:
        constant_array = [(600,120),(800,52),(1200,44),(2600,16),(1400,40),(1600,36),(1800,32),(1000,48),(2000,28),(2200,24),(2400,20),(2800,8),(3000,2)]
    if type(constant_array)!=list:
        return constant_array
    constant_array = sorted(constant_array, key=lambda k: k[0])
    for ele in constant_array:
        if elo_player < ele[0]:
            return ele[1]
    return 1

def _calculate_elo(elo_player_a, elo_player_b, player_a_goals, player_b_goals):
    player_a_transformed = 10**(elo_player_a/400)
    player_b_transformed = 10**(elo_player_a/400)

    player_a_expect_score = player_a_transformed / (player_a_transformed+player_b_transformed)
    player_b_expect_score = player_b_transformed / (player_a_transformed+player_b_transformed)

    if player_a_goals>player_b_goals:
        player_constant = _get_elo_constants(elo_player_a)
    else:
        player_constant = _get_elo_constants(elo_player_b)
    
    goals_multiplier = _get_goal_multiplier(player_a_goals,player_b_goals)

    new_player_a_elo = int(elo_player_a + goals_multiplier*player_constant*(int(player_a_goals>player_b_goals)-player_a_expect_score))
    new_player_b_elo = int(elo_player_b + goals_multiplier*player_constant*(int(player_b_goals>player_a_goals)-player_b_expect_score))

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

def _get_goal_multiplier(goals_a,goals_b,multiplier_modifier=[]):
    if not multiplier_modifier:
        # 1, 2, 3, 4, 5, 6, 7, 8 (el primer elemento es el default, por si a alguno se le ocurre jugar por mas de 8 goles)
        multiplier_modifier = [7,1,1.5,2,2.5,3,3.5,4,4.5]
    max_goals = len(multiplier_modifier)-1
    goals_diference = abs(goals_a-goals_b)
    
    if goals_diference > max_goals:
        return multiplier_modifier[0]
    else:
        return multiplier_modifier[goals_diference]

def _get_average_stats(player):
    count = 0
    goals = 0
    win_count = 0
    for game in player["__$history"]:
        count+=1
        goals+=game["__$own"]
        enemy = [en for en in list(game.keys()) if "__$" not in en]
        if len(enemy)==1:
            enemy = enemy[0]
        if game["__$own"] > game[enemy]:
            win_count+=1
    return str(round(float(goals)/float(count),1)), str(100*round(float(win_count)/float(count),1))