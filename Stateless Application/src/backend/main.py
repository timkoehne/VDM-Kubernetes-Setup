from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse
import httpx

app = FastAPI()

WORKER_URLS = {
    "grayscale": "http://image-editor-bw:8000/process",
    "remove-bg": "http://image-editor-rembg:8000/process",
}
@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    operation: str = Query(..., description="Image operation: grayscale or remove-bg")
):
    if operation not in WORKER_URLS:
        raise HTTPException(status_code=400, detail="Unsupported operation")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image file")

    contents = await file.read()
    worker_url = WORKER_URLS[operation]

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                worker_url,
                files={"file": ("image.png", contents, file.content_type)},
                timeout=30
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Worker request failed: {e}")

    return StreamingResponse(
        response.aiter_bytes(),
        media_type=response.headers.get("content-type", "image/png")
    )
