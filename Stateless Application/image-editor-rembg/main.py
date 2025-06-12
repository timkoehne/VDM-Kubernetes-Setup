from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response

from rembg import remove, new_session

app = FastAPI()

@app.post("/process")
async def process(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="File required")

    try:
        input_data = await file.read()
        session = new_session("u2net")
        output_data = remove(input_data, session)  # background removal
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image")

    return Response(content=output_data, media_type="image/png")
