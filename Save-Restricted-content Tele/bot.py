import logging
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
    bot.run()

#t.me/razzeshhere
