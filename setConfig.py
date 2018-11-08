import sys

data={}
data["prod"] = """BOT_TOKEN = "795408066:AAFW3jRC4qhpgmq7DuzeGdX40X9FHSp5vJs"
WKHTMLTOIMAGE_PATH='/usr/local/bin/wkhtmltoimage'
GROUPS=[-245994808,-123890638,528527409,-274219827]
ADMIN=[528527409]
"""
data["desa"] = r"""BOT_TOKEN = "758840577:AAH1rWnutujxlAUyJjxKVXUcgMT8pZutz1U"
WKHTMLTOIMAGE_PATH='D:\wkhtmltopdf\bin\wkhtmltoimage.exe'
GROUPS=[-245994808,-123890638,528527409,-274219827]
ADMIN=[528527409]
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