import logging
import uvicorn
from threading import Thread
from server.stream import app, client as server_client
logging.basicConfig(level=logging.INFO)
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, STRING_SESSION, LOGIN_SYSTEM

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
        print('Bot is Online Now \n powered by @razzeshhe')

    async def stop(self, *args):

        await super().stop()
        print('Bot Stopped Bye')

if __name__ == "__main__":
    bot = Bot()

    # --- 🎬 CINEMA MODE SERVER STARTUP ---
    # We import the module here to inject the client
    import server.stream 
    
    # Logic: If you provided a String Session (Owner Account), use it.
    # If not, use the Bot itself (limited to public/bot chats).
    if RazzeshUser and RazzeshUser.is_connected():
        print("🛠️ System: Injecting Telethon User into Stream Server...")
        server.stream.client = RazzeshUser
    else:
        print("⚠️ WARNING: User Account not found. Streaming may fail for private channels.")
        #server.stream.client = bot
         
    # Define the server starter
    def start_web_server():
        # Host 0.0.0.0 makes it accessible via your VPS Public IP
        uvicorn.run(server.stream.app, host="0.0.0.0", port=8000)
        
    # Run Uvicorn in a background thread so it doesn't block the bot
    Thread(target=start_web_server, daemon=True).start()
    print("✅ Cinema Server Running on Port 8000")
    # -------------------------------------

    bot.run()

#t.me/razzeshhere
