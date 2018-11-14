import sys

data={}
data["prod"] = """WKHTMLTOIMAGE_PATH='/usr/local/bin/wkhtmltoimage'
GROUPS=[-245994808,-123890638,528527409,-274219827,371817843]
ADMIN=[528527409,371817843]
PLAYERS_COLLECTION="jugadores"
LEAGUES_COLLECTION="ligas"
WEEKLY="week"
HALL_OF_FAME="hof"
"""
data["desa"] = r"""WKHTMLTOIMAGE_PATH=r"D:\wkhtmltopdf\bin\wkhtmltoimage.exe"
GROUPS=[-245994808,-123890638,528527409,-274219827,371817843]
ADMIN=[528527409,371817843]
PLAYERS_COLLECTION="jugadores_desa"
LEAGUES_COLLECTION="ligas_desa"
WEEKLY="week_desa"
HALL_OF_FAME="hof_desa"
"""

arg = sys.argv
try:
    if arg[1].lower() == "prod":
        data = data["prod"]
    else:
        data = data["desa"]
except:
    data = data["desa"]

with open("botConfig.py","w",encoding="UTF-8") as _file:
    _file.write(data)
