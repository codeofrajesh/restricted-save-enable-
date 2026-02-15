import logging
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse, HTMLResponse
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetMessagesRequest
import uvicorn

# Import your database and API keys
from database.db import db
from config import API_ID, API_HASH

app = FastAPI()

PLAYER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cinema Mode</title>
    <style>
        body {{ margin: 0; background: #000; display: flex; justify-content: center; align-items: center; height: 100vh; }}
        video {{ width: 100%; max-width: 1000px; max-height: 100vh; outline: none; }}
    </style>
</head>
<body>
    <video controls autoplay playsinline>
        <source src="/stream/{user_id}/{chat_id}/{msg_id}" type="video/mp4">
    </video>
</body>
</html>
"""

# 1. Added user_id to the route
@app.get("/watch/{user_id}/{chat_id}/{msg_id}")
async def player(user_id: int, chat_id: int, msg_id: int):
    return HTMLResponse(content=PLAYER_TEMPLATE.format(user_id=user_id, chat_id=chat_id, msg_id=msg_id))

# 2. Added user_id to the streaming route
@app.get("/stream/{user_id}/{chat_id}/{msg_id}")
async def stream_video(request: Request, user_id: int, chat_id: int, msg_id: int):
    try:
        # 3. Fetch the specific user's session from MongoDB
        user_session_string = await db.get_session(user_id)
        if not user_session_string:
            return Response("User session not found. Please /login first.", status_code=401)

        # 4. Spin up a temporary Telethon client in RAM using their string
        client = TelegramClient(StringSession(user_session_string), API_ID, API_HASH)
        await client.connect()

        try:
            try:
                entity = await client.get_entity(chat_id)
            except Exception:
                # Fallback to iter_dialogs if entity isn't cached
                async for dialog in client.iter_dialogs():
                    if dialog.id == chat_id:
                        entity = dialog.entity
                        break

            # Fetch the restricted message using the USER'S account
            msg_result = await client(GetMessagesRequest(peer=entity, id=[msg_id]))
            msg = msg_result.messages[0]
            
            if not msg or not msg.media:
                await client.disconnect()
                return Response("Media not found", status_code=404)

            file_size = msg.file.size
            
            async def file_generator():
                try:
                    async for chunk in client.iter_download(msg.media, chunk_size=1024*1024):
                        yield chunk
                finally:
                    # Always securely disconnect the RAM client when the video stops buffering
                    await client.disconnect()

            return StreamingResponse(
                file_generator(),
                media_type=msg.file.mime_type,
                headers={
                    "Content-Length": str(file_size),
                    "Accept-Ranges": "bytes",
                }
            )
        except Exception as inner_e:
            await client.disconnect()
            raise inner_e

    except Exception as e:
        logging.error(f"🎬 Stream Error: {e}")
        return Response(f"Internal Error: {e}", status_code=500)