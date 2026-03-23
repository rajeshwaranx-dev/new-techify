import re
import os
from os import environ, getenv
from Script import script

id_pattern = re.compile(r'^.\d+$')

def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default

SESSION = environ.get('SESSION', 'techifybots')
API_ID = int(environ.get('API_ID', '23361081'))
API_HASH = environ.get('API_HASH', '0605c5395b91ead763072251e20c3417')
BOT_TOKEN = environ.get('BOT_TOKEN', "8361529441:AAGfl604PFp9OHLKyL8kcTnQoBTCo8oXAIg")
USE_CAPTION_FILTER = bool(environ.get('USE_CAPTION_FILTER', False))
INDEX_CAPTION = bool(environ.get('INDEX_CAPTION', False))
COVER = bool(environ.get('COVER', False))
PICS = (environ.get('PICS', 'https://graph.org/file/dc8d94be0c5b2c9693e75-707e6fdfb7fc8d3e2c.jpg')).split()
MELCOW_PHOTO = environ.get("MELCOW_PHOTO", "https://i.ibb.co/2769f1rF/photo-2025-09-03-14-48-34-7548400762112442372.jpg")
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ.get('ADMINS', '1714147365 ').split()]
CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('CHANNELS', '-1002030715343').split()]
LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1002289263173'))
BIN_CHANNEL = int(environ.get('BIN_CHANNEL', '0'))
PREMIUM_LOGS = int(environ.get('PREMIUM_LOGS', '-1002737733323'))
DELETE_CHANNELS = [int(dch) if id_pattern.search(dch) else dch for dch in environ.get('DELETE_CHANNELS', '0').split()]
AUTH_CHANNELS = [int(ch) for ch in environ.get("AUTH_CHANNELS", "").split() if ch and id_pattern.match(ch)]
AUTH_REQ_CHANNELS = [int(ch) for ch in environ.get("AUTH_REQ_CHANNELS", "-1003518468917").split() if ch and id_pattern.match(ch)]
REQST_CHANNEL = int(ch) if (ch := environ.get("REQST_CHANNEL", "-1002497903505")) and id_pattern.search(ch) else None
SUPPORT_CHAT_ID = int(ch) if (ch := environ.get("SUPPORT_CHAT_ID", "-1002844979596")) and id_pattern.search(ch) else None

OWNER = int(os.environ.get("OWNER", "5371238852"))
CHANNEL_LINK = environ.get('CHANNEL_LINK', 'https://telegram.me/Master_xkid')
GROUP_LINK = environ.get('GROUP_LINK', 'https://telegram.me/Askmovieslink1')

DATABASE_URI = environ.get('DATABASE_URI', "mongodb+srv://Rajeshuri2:Rajeshx2@cluster0.sql2rpv.mongodb.net/?appName=Cluster0")
DATABASE_NAME = environ.get('DATABASE_NAME', "Rajeshuri2")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'RajeshLcu2')
MULTIPLE_DB = is_enabled(os.environ.get('MULTIPLE_DB', "True"), False)
DATABASE_URI2 = environ.get('DATABASE_URI2', "mongodb+srv://RajeshLcu2:Rajeshx@cluster0.0razpdy.mongodb.net/?appName=Cluster0")

UPDATE_NOTIFICATION = bool(environ.get('UPDATE_NOTIFICATION', False))
UPDATE_CHANNEL = int(environ.get('UPDATE_CHANNEL', '-1002197398349'))
IMAGE_FETCH = bool(environ.get('IMAGE_FETCH', True))
LINK_PREVIEW = bool(environ.get('LINK_PREVIEW', False))
ABOVE_PREVIEW = bool(environ.get('ABOVE_PREVIEW', False))
TMDB_API_KEY = environ.get('TMDB_API_KEY', '')
TMDB_POSTER = bool(environ.get('TMDB_POSTER', True))
LANDSCAPE_POSTER = bool(environ.get('LANDSCAPE_POSTER', True))

IS_VERIFY = is_enabled('IS_VERIFY', True)
LOG_API_CHANNEL = int(environ.get('LOG_API_CHANNEL', '-1002289263173'))
VERIFY_IMG = environ.get("VERIFY_IMG", "https://i.ibb.co/xqNtSMpS/photo-2025-09-18-15-24-38-7551450511015149572.jpg")
TUTORIAL = environ.get("TUTORIAL", "https://t.me/Tutorial01Ask")
TUTORIAL_2 = environ.get("TUTORIAL_2", "https://t.me/Tutorial01Ask")
TUTORIAL_3 = environ.get("TUTORIAL_3", "https://t.me/Tutorial01Ask")
SHORTENER_API = environ.get("SHORTENER_API", "a7ac9b3012c67d7491414cf272d82593c75f6cbb")
SHORTENER_WEBSITE = environ.get("SHORTENER_WEBSITE", "omegalinks.in")
SHORTENER_API2 = environ.get("SHORTENER_API2", "a7ac9b3012c67d7491414cf272d82593c75f6cbb")
SHORTENER_WEBSITE2 = environ.get("SHORTENER_WEBSITE2", "omegalinks.in")
SHORTENER_API3 = environ.get("SHORTENER_API3", "a7ac9b3012c67d7491414cf272d82593c75f6cbb")
SHORTENER_WEBSITE3 = environ.get("SHORTENER_WEBSITE3", "omegalinks.in")
TWO_VERIFY_GAP = int(environ.get('TWO_VERIFY_GAP', "1200"))
THREE_VERIFY_GAP = int(environ.get('THREE_VERIFY_GAP', "54000"))

FAST_MODE = is_enabled(environ.get('FAST_MODE', "False"), False)
MAX_BTN = is_enabled((environ.get('MAX_BTN', "True")), True)
MAX_BTNS = environ.get("MAX_BTNS", "5")
MSG_ALRT = environ.get('MSG_ALRT', '𝖲𝗁𝖺𝗋𝖾 & 𝖲𝗎𝗉𝗉𝗈𝗋𝗍 ♥️')
DELETE_TIME = int(environ.get("DELETE_TIME", "0"))
FILE_CAPTION = environ.get("FILE_CAPTION", f"{script.CAPTION}")
IMDB_TEMPLATE = environ.get("IMDB_TEMPLATE", f"{script.IMDB_TEMPLATE_TXT}")
MAX_LIST_ELM = int(environ.get("MAX_LIST_ELM") or 8) or None # Maximum number of elements in a list (default: 10, set 0 for no limit)
NO_RESULTS_MSG = bool(environ.get("NO_RESULTS_MSG", True))
P_TTI_SHOW_OFF = is_enabled((environ.get('P_TTI_SHOW_OFF', "False")), False)
IMDB = is_enabled((environ.get('IMDB', "False")), False)
TMDB_ON_SEARCH = is_enabled((environ.get('TMDB_ON_SEARCH', "False")), False)
AUTO_FILTER = is_enabled((environ.get('AUTO_FILTER', "True")), True)
AUTO_DELETE = is_enabled((environ.get('AUTO_DELETE', "True")), True)
LONG_IMDB_DESCRIPTION = is_enabled(environ.get("LONG_IMDB_DESCRIPTION", "False"), False)
SPELL_CHECK_REPLY = is_enabled(environ.get("SPELL_CHECK_REPLY", "True"), True)
MELCOW_NEW_USERS = is_enabled((environ.get('MELCOW_NEW_USERS', "False")), False)
PROTECT_CONTENT = is_enabled((environ.get('PROTECT_CONTENT', "False")), False)
PM_SEARCH = bool(environ.get('PM_SEARCH', True))
EMOJI_MODE = bool(environ.get('EMOJI_MODE', False))
BUTTON_MODE = is_enabled((environ.get('BUTTON_MODE', "False")), False)
STREAM_MODE = bool(environ.get('STREAM_MODE', False))
PREMIUM_STREAM_MODE = bool(environ.get('PREMIUM_STREAM_MODE', False))

LANGUAGES = {"ᴛᴀᴍɪʟ":"tam","ᴛᴇʟᴜɢᴜ":"tel","ᴇɴɢʟɪsʜ":"eng","ʜɪɴᴅɪ":"hin","ᴊᴀᴘᴀɴᴇsᴇ":"jap"}
QUALITIES = ["360P", "480P", "720P", "1080P", "2160p"]
SEASON_COUNT = 12
SEASONS = [f"S{str(i).zfill(2)}" for i in range(1, SEASON_COUNT + 1)]
REACTIONS = ["🤝", "😇", "🤗", "😍", "👍", "🎅", "😐", "🥰", "🤩", "😱", "🤣", "😘", "👏", "😛", "😈", "🎉", "⚡️", "🫡", "🤓", "😎", "🏆", "🔥", "🤭", "🌚", "🆒", "👻", "😁"]
STAR_PREMIUM_PLANS = {10: "7day", 20: "15day", 40: "1month", 55: "45day", 75: "60day"}
BAD_WORDS = {"PrivateMovieZ", "koothi", "themoviesboss", "1tamilmv", "tamilblasters", "1tamilblasters", "skymovieshd", "extraflix", "thevidiya", "moviesmod", "hdhub4u", "mkvcinemas", "sunni", "oombu", "www", "villa", "tg", "original", "punda",}

IS_FILE_LIMIT = bool(environ.get('IS_FILE_LIMIT', True)) 
FILES_LIMIT = int(environ.get("FILES_LIMIT", "48"))
QUALITY_LIMIT = bool(environ.get('QUALITY_LIMIT', False)) 
FREE_QUALITIES = ["360p", "480p"]

PORT = int(environ.get("PORT", "8036"))
NO_PORT = bool(environ.get('NO_PORT', False))
APP_NAME = None
if 'DYNO' in environ:
    ON_HEROKU = True
    APP_NAME = environ.get('APP_NAME')
else:
    ON_HEROKU = False
BIND_ADRESS = str(getenv('WEB_SERVER_BIND_ADDRESS', 'alyafilterbot.onrender.com'))
FQDN = str(getenv('FQDN', BIND_ADRESS)) if not ON_HEROKU or getenv('FQDN') else APP_NAME+'.herokuapp.com'
URL = "https://{}/".format(FQDN) if ON_HEROKU or NO_PORT else "https://{}/".format(FQDN, PORT)
SLEEP_THRESHOLD = int(environ.get('SLEEP_THRESHOLD', '60'))
MULTI_CLIENT = False
PING_INTERVAL = int(environ.get("PING_INTERVAL", "1200"))
if 'DYNO' in environ:
    ON_HEROKU = True
    APP_NAME = str(getenv('APP_NAME'))
else:
    ON_HEROKU = False
HAS_SSL = bool(getenv('HAS_SSL', True))
if HAS_SSL:
    URL = "https://{}/".format(FQDN)
else:
    URL = "http://{}/".format(FQDN)

if MULTIPLE_DB == False:
    DATABASE_URI = DATABASE_URI
    DATABASE_URI2 = DATABASE_URI
else:
    DATABASE_URI = DATABASE_URI
    DATABASE_URI2 = DATABASE_URI2

LOG_STR = "Current Customized Configurations are:-\n"
LOG_STR += ("IMDB Results are enabled, Bot will be showing imdb details for your queries.\n" if IMDB else "IMDB Results are disabled.\n")
LOG_STR += ("P_TTI_SHOW_OFF found, Users will be redirected to send /start to Bot PM instead of sending file directly.\n" if P_TTI_SHOW_OFF else "P_TTI_SHOW_OFF is disabled, files will be sent in PM instead of starting the bot.\n")
LOG_STR += ("BUTTON_MODE is found, filename and file size will be shown in a single button instead of two separate buttons.\n" if BUTTON_MODE else "BUTTON_MODE is disabled, filename and file size will be shown as different buttons.\n")
LOG_STR += (f"FILE_CAPTION enabled with value {FILE_CAPTION}, your files will be sent along with this customized caption.\n" if FILE_CAPTION else "No FILE_CAPTION Found, Default captions of file will be used.\n")
LOG_STR += ("Long IMDB storyline enabled." if LONG_IMDB_DESCRIPTION else "LONG_IMDB_DESCRIPTION is disabled, Plot will be shorter.\n")
LOG_STR += ("Spell Check Mode is enabled, bot will be suggesting related movies if movie name is misspelled.\n" if SPELL_CHECK_REPLY else "Spell Check Mode is disabled.\n")
