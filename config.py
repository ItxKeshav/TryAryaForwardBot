from os import environ

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    # -------- TELEGRAM --------
    API_ID = int(environ.get("API_ID", 0))
    API_HASH = environ.get("API_HASH", "")
    BOT_TOKEN = environ.get("BOT_TOKEN", "")
    BOT_SESSION = environ.get("BOT_SESSION", "bot")

    # -------- DATABASE --------
    DATABASE_URI = (
        environ.get("DATABASE_URI") or
        environ.get("DATABASE") or
        ""
    )

    DATABASE_NAME = environ.get("DATABASE_NAME", "arya")

    # -------- OWNER (FIXED) --------
    OWNER_IDS = [
        int(i) for i in environ.get("OWNER_IDS", "").replace(",", " ").split()
        if i.isdigit()
    ]

    BOT_OWNER_ID = OWNER_IDS


class temp(object):
    lock = {}
    CANCEL = {}
    PAUSE = {}
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []
