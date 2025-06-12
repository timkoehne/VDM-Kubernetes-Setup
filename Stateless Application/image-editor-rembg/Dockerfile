FROM python:3.11-slim AS base

WORKDIR /app

# Install rembg and FastAPI dependencies
RUN pip install --no-cache-dir rembg[cli] fastapi uvicorn python-multipart onnxruntime
RUN rembg d u2net

COPY main.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
