import logging
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse, HTMLResponse
from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto
import uvicorn

app = FastAPI()
# This will be your STRING_SESSION client
client: TelegramClient = None 

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
        <source src="/stream/{chat_id}/{msg_id}" type="video/mp4">
    </video>
</body>
</html>
"""

@app.get("/watch/{chat_id}/{msg_id}")
async def player(chat_id: int, msg_id: int):
    return HTMLResponse(content=PLAYER_TEMPLATE.format(chat_id=chat_id, msg_id=msg_id))

@app.get("/stream/{chat_id}/{msg_id}")
async def stream_video(request: Request, chat_id: int, msg_id: int):
    try:
        # 1. Fetch the message using Telethon's superior peer resolution
        entity = await client.get_input_entity(chat_id)
        msg = await client.get_messages(entity, ids=msg_id)
        
        if not msg or not msg.media:
            return Response("Media not found", status_code=404)

        file_size = msg.file.size
        
        # 2. The Streamer Generator
        async def file_generator():
            # Telethon's iter_download is built for streaming
            async for chunk in client.iter_download(msg.media, chunk_size=1024*512):
                yield chunk

        # 3. Standard HTTP Range Support
        return StreamingResponse(
            file_generator(),
            media_type=msg.file.mime_type,
            headers={
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes",
            }
        )
    except Exception as e:
        logging.error(f"Telethon Stream Error: {e}")
        return Response(f"Stream Error: {e}", status_code=500)