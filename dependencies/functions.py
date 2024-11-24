from fastapi import HTTPException
import asyncio
import requests
from typing import Optional
import re


def legacy_download(url):
    response = requests.get(url, stream=True)
    file_size = int(response.headers.get("content-length", 0))
    path = "stream.mp4"
    downloaded_so_far = 0

    with open(path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024):
            file.write(chunk)
            downloaded_so_far += len(chunk)
            progress = (downloaded_so_far / file_size) * 100
            print(
                f"Downloaded {downloaded_so_far} of {file_size} bytes ({progress:.2f}%)",
                end="\r",
            )
    print("\nDownload complete!")
    return True


def parse_range_header(range_header: Optional[str], file_size: int) -> tuple[int, int]:
    if range_header is None:
        return 0, file_size - 1

    match = re.match(r"bytes=(\d+)-(\d*)", range_header)
    if not match:
        return 0, file_size - 1

    start = int(match.group(1))
    end = int(match.group(2)) if match.group(2) else file_size - 1

    return start, min(end, file_size - 1)


async def stream_video(url: str, start_byte: int = 0, end_byte: Optional[int] = None):
    headers = {}
    if start_byte > 0 or end_byte is not None:
        headers["Range"] = f'bytes={start_byte}-{end_byte if end_byte else ""}'

    try:
        response = requests.get(url, stream=True, headers=headers)
        response.raise_for_status()

        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                yield chunk
                await asyncio.sleep(0.001)
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Video streaming error: {str(e)}")
