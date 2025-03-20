from fastapi import FastAPI, Response, Request
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

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

SOURCE_DIR = os.getenv("STORAGE_PATH")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1))  # Default 1MB

@app.get("/stream/{filename:path}")
async def stream_video(filename: str, request: Request):
    file_path = os.path.join(SOURCE_DIR, filename)
    if not os.path.exists(file_path):
        return Response("File not found", status_code=404)

    range_header = request.headers.get("range", None)
    file_size = os.path.getsize(file_path)

    if not range_header:
        return Response("Requires Range header", status_code=400)

    start, end = range_header.replace("bytes=", "").split("-")
    start = int(start) if start else 0
    end = int(end) if end else file_size - 1
    end = min(end, file_size - 1)

    content_length = end - start + 1

    def iter_video():
        with open(file_path, "rb") as f:
            f.seek(start)
            remaining = content_length
            while remaining > 0:
                chunk = f.read(min(CHUNK_SIZE, remaining))
                if not chunk:
                    break
                yield chunk
                remaining -= len(chunk)

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": "video/mp4",
        "Access-Control-Allow-Origin": "*",  # Add CORS header directly
    }

    return StreamingResponse(iter_video(), status_code=206, headers=headers)