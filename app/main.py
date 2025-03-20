from fastapi import FastAPI, Response, Request
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import BinaryIO
import asyncio
from fastapi.concurrency import run_in_threadpool
from fastapi import BackgroundTasks

load_dotenv()
app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SOURCE_DIR = os.getenv("SOURCE_DIR")
# Giới hạn số lượng request đồng thời
MAX_CONCURRENT_STREAMS = 100
# Semaphore để giới hạn số lượng request đồng thời
stream_semaphore = asyncio.Semaphore(MAX_CONCURRENT_STREAMS)

def iterfile(file_object: BinaryIO, chunk_size: int, start: int, end: int) -> bytes:
    """Đọc file theo từng chunk nhỏ để streaming"""
    file_object.seek(start)
    bytes_remaining = end - start + 1
    while bytes_remaining > 0:
        chunk_size_to_read = min(chunk_size, bytes_remaining)
        data = file_object.read(chunk_size_to_read)
        if not data:
            break
        bytes_remaining -= len(data)
        yield data

@app.get("/stream/{filename:path}")
async def stream_video(filename: str, request: Request):
    async with stream_semaphore:
        file_path = os.path.join(SOURCE_DIR, filename)
        if not os.path.exists(file_path):
            return Response("File not found", status_code=404)

        range_header = request.headers.get("range", None)
        file_size = os.path.getsize(file_path)

        if not range_header:
            # Nếu không có range header, trả về 1MB đầu tiên
            start = 0
            end = min(1024 * 1024, file_size - 1)
        else:
            start, end = range_header.replace("bytes=", "").split("-")
            start = int(start) if start else 0
            end = int(end) if end else file_size - 1
            end = min(end, file_size - 1)

        # Giới hạn kích thước chunk để tránh sử dụng quá nhiều bộ nhớ
        chunk_size = 1024 * 1024  # 1MB
        content_length = end - start + 1

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Type": "video/mp4",
            "Content-Disposition": "inline",
        }

        try:
            file_obj = open(file_path, "rb")
            background_tasks = BackgroundTasks()
            background_tasks.add_task(file_obj.close)

            # Sử dụng response streaming để tránh tải toàn bộ file vào memory
            return StreamingResponse(
                await run_in_threadpool(
                    lambda: iterfile(file_obj, chunk_size, start, end)
                ),
                status_code=206,
                headers=headers,
                media_type="video/mp4",
                background=background_tasks
            )
        except Exception as e:
            return Response(f"Error: {str(e)}", status_code=500)