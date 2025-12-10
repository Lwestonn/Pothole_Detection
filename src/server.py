from pathlib import Path
import io

import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from ultralytics import YOLO


# Locate project root and resources
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "best.pt"
WEB_DIR = PROJECT_ROOT / "web"

app = FastAPI(title="Pothole YOLO Server")

# Mount static files (JS, CSS) at /static
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


# Load YOLO model once at startup
if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found at {MODEL_PATH}")

model = YOLO(str(MODEL_PATH))


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def index():
    """Serve the main HTML page."""
    index_file = WEB_DIR / "index.html"
    if not index_file.exists():
        return JSONResponse(
            status_code=500,
            content={"error": f"index.html not found in {WEB_DIR}"},
        )
    return FileResponse(index_file)


@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    """
    Receive an image file, run YOLO, return annotated JPEG.
    This is called repeatedly by the browser to simulate live video.
    """
    image_bytes = await file.read()

    # Decode image bytes to OpenCV BGR image
    nparr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        return JSONResponse(status_code=400, content={"error": "Invalid image data"})

    # Run YOLO
    results = model(frame, verbose=False)
    annotated = results[0].plot()  # BGR image with boxes and labels

    # Encode to JPEG
    success, encoded_image = cv2.imencode(".jpg", annotated)
    if not success:
        return JSONResponse(status_code=500, content={"error": "Failed to encode image"})

    # Stream back to browser
    return StreamingResponse(
        io.BytesIO(encoded_image.tobytes()),
        media_type="image/jpeg",
    )


if __name__ == "__main__":
    # For direct running: python src/server.py
    import uvicorn

    uvicorn.run(
        "src.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
