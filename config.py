# -*- coding: utf-8; -*-
from enviroment import ENTORNO

def get(key):
    data = {}

    if ENTORNO == "DESA":
        data["WKHTMLTOIMAGE_PATH"]='/usr/local/bin/wkhtmltoimage'
        data["PLAYERS_COLLECTION"]="jugadores_desa"
        data["LEAGUES_COLLECTION"]="ligas_desa"
        data["WEEKLY"]="week_desa"
        data["HALL_OF_FAME"]="hof_desa"
        data["MAIN_GROUP"]="-245994808"
        data["REDIS_HOST"]="localhost"
        data["REDIS_PORT"]="6379"
        data["MAIN_DB"] = "historico"
        data["WEEKLY_DB"] = "weekly_desa"
        data["GROUPS"]=["-245994808","528527409"]
    else:
        data["WKHTMLTOIMAGE_PATH"]='/usr/local/bin/wkhtmltoimage'
        data["PLAYERS_COLLECTION"]="jugadores"
        data["LEAGUES_COLLECTION"]="ligas"
        data["WEEKLY"]="week"
        data["HALL_OF_FAME"]="hof"
        data["MAIN_GROUP"]="-274219827"
        data["REDIS_HOST"]="localhost"
        data["REDIS_PORT"]="6379"
        data["MAIN_DB"] = "historico"
        data["WEEKLY_DB"] = "weekly"
        data["GROUPS"]=["-245994808","-274219827","528527409"]

    data["ADMIN"]=[528527409]
    data["EXCEPT_MANAGER"]=528527409

    data["MULTIPLIER"]=0.3
    
    return data.get(key)