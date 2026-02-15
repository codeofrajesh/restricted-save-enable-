import logging
import uvicorn
from threading import Thread
from pyrogram import Client

# Just import the app, we don't need the client anymore!
from server.stream import app 
from config import API_ID, API_HASH, BOT_TOKEN, STRING_SESSION, LOGIN_SYSTEM

logging.basicConfig(level=logging.INFO)

# --- GLOBAL OWNER CLIENT (For single-user mode fallback) ---
if STRING_SESSION is not None and LOGIN_SYSTEM == False:
    RazzeshUser = Client("Razzesh", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
    RazzeshUser.start()
else:
    RazzeshUser = None

class Bot(Client):
    def __init__(self):
        super().__init__(
            "RazzeshBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="main"),
            workers=150,
            sleep_threshold=5
        )

    async def start(self):
        await super().start()
        print('✅ Bot is Online Now \nPowered by @razzeshhere')

    async def stop(self, *args):
        await super().stop()
        print('🛑 Bot Stopped. Bye!')

if __name__ == "__main__":
    bot = Bot()

    # --- 🎬 CINEMA MODE SERVER STARTUP ---
    def start_web_server():
        # Host 0.0.0.0 makes it accessible via your AWS EC2 Public IP
        print("🛠️ System: Booting Dynamic Streaming Engine...")
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
        
    # Run Uvicorn in a background thread so it doesn't block Pyrogram
    Thread(target=start_web_server, daemon=True).start()
    print("✅ Cinema Server Running on Port 8000")
    # -------------------------------------

    # Boot the main Telegram bot
    bot.run()