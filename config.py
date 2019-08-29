from enviroment import ENTORNO

def get(key):
    data = {}

    if ENTORNO == "desa":
        data["WKHTMLTOIMAGE_PATH"]='D:\wkhtmltopdf\bin\wkhtmltoimage.exe'
        data["PLAYERS_COLLECTION"]="jugadores_desa"
        data["LEAGUES_COLLECTION"]="ligas_desa"
        data["WEEKLY"]="week_desa"
        data["HALL_OF_FAME"]="hof_desa"
    else:
        data["WKHTMLTOIMAGE_PATH"]='/usr/local/bin/wkhtmltoimage'
        data["PLAYERS_COLLECTION"]="jugadores"
        data["LEAGUES_COLLECTION"]="ligas"
        data["WEEKLY"]="week"
        data["HALL_OF_FAME"]="hof"

    data["GROUPS"]=[]

    data["ADMIN"]=[528527409]
    data["EXCEPT_MANAGER"]=528527409

    data["MULTIPLIER"]=0.3
    
    return data.get(key)