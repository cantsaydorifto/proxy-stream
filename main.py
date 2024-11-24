from fastapi import FastAPI, Request
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import requests
from dependencies.functions import parse_range_header, stream_video
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# origins = ["*"]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["GET"],
#     allow_headers=["Range"],
# )


@app.get("/")
def home():
    return {"message": "Hello World!"}


@app.get("/stream/{video_url:path}")
async def stream_data(video_url: str, request: Request):
    try:
        head_response = requests.head(video_url)
        file_size = int(head_response.headers.get("content-length", 0))
        range_header = request.headers.get("Range")
        start_byte, end_byte = parse_range_header(range_header, file_size)
        print(
            "range_header:  ",
            str(start_byte) + " " + str(end_byte) + "  total: " + str(file_size),
        )
        content_length = end_byte - start_byte + 1

        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes {start_byte}-{end_byte}/{file_size}",
            "Content-Disposition": "inline; filename=video_stream.mp4",
        }

        status_code = 206 if start_byte > 0 else 200

        return StreamingResponse(
            stream_video(video_url, start_byte, end_byte),
            headers=headers,
            status_code=status_code,
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error accessing video: {str(e)}")
