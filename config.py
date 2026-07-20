from os import getenv
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.API_ID = int(getenv("API_ID", 0))
        self.API_HASH = getenv("API_HASH")

        self.BOT_TOKEN = getenv("BOT_TOKEN")
        self.MONGO_URL = getenv("MONGO_URL")

        self.LOGGER_ID = int(getenv("LOGGER_ID", 0))
        self.OWNER_ID = int(getenv("OWNER_ID", 0))

        self.DURATION_LIMIT = int(getenv("DURATION_LIMIT", 600)) * 60
        self.QUEUE_LIMIT = int(getenv("QUEUE_LIMIT", 20))
        self.PLAYLIST_LIMIT = int(getenv("PLAYLIST_LIMIT", 20))

        self.SESSION1 = getenv("SESSION", None)
        self.SESSION2 = getenv("SESSION2", None)
        self.SESSION3 = getenv("SESSION3", None)

        self.SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/siya_infoo")
        self.SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/+amMz8_Sg7hhhMWQ1")

        self.LANG_CODE = getenv("LANG_CODE", "en")
        self.AUTO_LEAVE: bool = getenv("AUTO_LEAVE", "False").lower() == "true"
        self.AUTO_END: bool = getenv("AUTO_END", "False").lower() == "true"
        self.THUMB_GEN: bool = getenv("THUMB_GEN", "True").lower() == "true"
        self.VIDEO_PLAY: bool = getenv("VIDEO_PLAY", "True").lower() == "true"

        self.COOKIES_URL = [
            url for url in getenv("COOKIES_URL", "https://batbin.me/meioses").split(" ")
            if url and "batbin.me" in url
        ]

        self.DEFAULT_THUMB = getenv(
            "DEFAULT_THUMB",
            "https://files.catbox.moe/zxpua2.jpg"
        )
        self.PING_IMG = getenv("PING_IMG", "https://files.catbox.moe/f30bc5.jpg")
        self.START_IMG = getenv("START_IMG", "https://graph.org/file/d60d88144ce47ef57c052-80854bf4f8597bdb2a.jpg")
        self.START_ANIMATION = getenv("START_ANIMATION", "https://graph.org/file/5ca52379458b6d82b4ad7-8dd6ca46e4e59102d2.mp4")

        self.API_KEY = getenv("API_KEY", "3b8bd8_XSx6ZLvxdiSIUGDrI7_lvB1kS6LMisF2")
        # @FallenApiBot send cmd /apikey

        self.API_URL = getenv("API_URL", "https://api.onegrab.fun")

    def check(self):
        missing = [
            var
            for var in ["API_ID", "API_HASH", "BOT_TOKEN", "MONGO_URL", "LOGGER_ID", "OWNER_ID", "SESSION1"]
            if not getattr(self, var)
        ]
        if missing:
            raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")
