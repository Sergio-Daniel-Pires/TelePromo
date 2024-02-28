import os

import dotenv

dotenv.load_dotenv(override=False)

BOT_OWNER_CHAT_ID = os.environ["BOT_OWNER_CHAT_ID"]
MONGO_CONN_STR = os.environ["MONGO_CONN_STR"]
NGROK_URL = os.environ.get("NGROK_URL", None)
NGROK_AUTH = os.environ.get("NGROK_AUTH", None)
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
REDIS_URL = os.environ["REDIS_URL"]
