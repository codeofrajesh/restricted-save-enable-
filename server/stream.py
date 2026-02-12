import math
import logging
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse, HTMLResponse
from pyrogram import Client
from typing import BinaryIO, Union

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
        body { margin: 0; background: #000; display: flex; justify-content: center; align-items: center; height: 100vh; }
        video { width: 100%; max-width: 1000px; max-height: 100vh; outline: none; }
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
async def stream_video(request: Request, chat_id: int, msg_id: int):
    # 1. Get Metadata
    msg = await client.get_messages(chat_id, msg_id)
    if not msg.video: return Response("Not a video", status_code=400)
    
    file_size = msg.video.file_size
    
    # 2. Initialize Streamer
    stream = TGFileStream(client, chat_id, msg_id, file_size)
    
    # 3. Hand over to Range Handler
    return await range_streamer(request, stream, file_size)

# --- Helper to extend Pyrogram Client ---
# Pyrogram doesn't have a public 'get_file_offset' helper, so we add a patch
async def get_file_offset(self, chat_id, message_id, offset, limit):
    # This uses the internal session to fetch specific bytes
    # Note: Simplification for 'get_file' - usually needs 'FileLocation'
    # We will use the download_media generator trick for simplicity in V1
    
    # 🛑 MECHANICAL UPGRADE: 
    # Standard Pyrogram `download_media` supports in-memory binary objects.
    # But for True Random Access, we need a dedicated method.
    # For now, we use the standard generator but discard bytes until offset.
    # (Note: For true production efficiency, you'd use raw MTProto calls here).
    
    async for chunk in self.stream_media(message_id, limit=limit, offset=offset):
        return chunk # Just return the first chunk found
    return b""

Client.get_file_offset = get_file_offset