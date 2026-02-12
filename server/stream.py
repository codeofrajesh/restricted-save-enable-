import math
import logging
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse, HTMLResponse
from pyrogram import Client
from typing import BinaryIO, Union
from pyrogram.utils import get_peer_type

# Initialize the Web Server
app = FastAPI()
client: Client = None  # Will be injected from bot.py

# --- HTML Player Template ---
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
        Your browser does not support the video tag.
    </video>
</body>
</html>
"""

class TGFileStream:
    def __init__(self, client: Client, chat_id: int, msg_id: int, total_size: int):
        self.client = client
        self.chat_id = chat_id
        self.msg_id = msg_id
        self.total_size = total_size
        self.current_offset = 0

    async def read(self, chunk_size: int) -> bytes:
        # Fetch chunk from Telegram
        try:
            chunk = await self.client.get_file_offset(
                self.chat_id, self.msg_id, offset=self.current_offset, limit=chunk_size
            )
            self.current_offset += len(chunk)
            return chunk
        except Exception as e:
            logging.error(f"Stream Error: {e}")
            return b""

    def seek(self, offset: int):
        self.current_offset = offset

# --- The Range Handler (Crucial for Seeking) ---
async def range_streamer(request: Request, file_stream: TGFileStream, total_size: int):
    range_header = request.headers.get("range")
    
    if not range_header:
        # No seeking requested, stream from 0
        file_stream.seek(0)
        return StreamingResponse(
            iter_file(file_stream, 1024*1024), 
            media_type="video/mp4",
            headers={"Content-Length": str(total_size), "Accept-Ranges": "bytes"}
        )

    # Parse Range: "bytes=1000-"
    start, end = range_header.replace("bytes=", "").split("-")
    start = int(start)
    end = int(end) if end else total_size - 1
    chunk_size = (end - start) + 1

    file_stream.seek(start)
    
    return StreamingResponse(
        iter_file(file_stream, 1024*512, limit=chunk_size), # 512KB chunks
        status_code=206,
        media_type="video/mp4",
        headers={
            "Content-Range": f"bytes {start}-{end}/{total_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
        },
    )

async def iter_file(stream, chunk_size, limit=None):
    bytes_read = 0
    while True:
        if limit and bytes_read >= limit: break
        
        # Adjust request size if close to limit
        to_read = chunk_size
        if limit and (bytes_read + chunk_size) > limit:
            to_read = limit - bytes_read
            
        data = await stream.read(to_read)
        if not data: break
        
        yield data
        bytes_read += len(data)

# --- Routes ---
@app.get("/watch/{chat_id}/{msg_id}")
async def player(chat_id: int, msg_id: int):
    return HTMLResponse(content=PLAYER_TEMPLATE.format(chat_id=chat_id, msg_id=msg_id))

@app.get("/stream/{chat_id}/{msg_id}")
async def stream_video(request: Request, chat_id: Union[int, str], msg_id: int):
    # 1. Convert to Int (Mechanical Standard)
    try:
        if isinstance(chat_id, str) and chat_id.startswith("-100"):
            chat_id = int(chat_id)
        elif isinstance(chat_id, str):
            chat_id = int(chat_id)
    except: pass # It's a username

    try:
        # 2. THE LEGENDARY FIX: Use get_messages on the ID directly
        # But we wrap it in a 'try' to catch the resolution error
        try:
            msg = await client.get_messages(chat_id, msg_id)
        except (KeyError, Exception):
            # If Pyrogram says "ID not found", we force it to see the chat
            # By sending a tiny ping to the ID
            await client.get_chat(chat_id)
            msg = await client.get_messages(chat_id, msg_id)

        if not msg or not msg.video:
            return Response("Video not found", status_code=404)
        
        file_size = msg.video.file_size
        stream = TGFileStream(client, chat_id, msg_id, file_size)
        return await range_streamer(request, stream, file_size)

    except Exception as e:
        # If still failing, it's a permission issue or DC mismatch
        logging.error(f"🎬 Cinema Error: {e}")
        return Response(f"Security Error: {e}", status_code=500)
    
async def get_file_offset(self, chat_id, message_id, offset, limit):
    """
    This is a custom patch for Pyrogram to allow streaming specific 
    byte ranges (offset and limit) from Telegram.
    """
    # Use the stream_media generator to fetch only the requested chunk
    async for chunk in self.stream_media(message_id, limit=limit, offset=offset):
        return chunk 
    return b""    
    
Client.get_file_offset = get_file_offset