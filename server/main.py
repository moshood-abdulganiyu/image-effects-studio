import base64
import sys
from pathlib import Path

import cv2
import numpy as np

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# allow "from src.effects import ..." when running from repo root or from server/
sys.path.append(str(Path(__file__).resolve().parent.parent))

from server.schemas import EffectType, PredictResponse
from src.effects import cartoonify, grayscale, oil_painting, pencil_sketch, pixel_art

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

EFFECT_FUNCTIONS = {
    EffectType.cartoonify: cartoonify,
    EffectType.grayscale: grayscale,
    EffectType.pencil_sketch: pencil_sketch,
    EffectType.oil_painting: oil_painting,
    EffectType.pixel_art: pixel_art,
}

app = FastAPI(
    title="Image Effects Studio API",
    description="Upload an image, apply one of five OpenCV effects on demand.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://moshood-abdulganiyu-image-effects-studio-frontend.static.hf.space",
        "http://localhost:8080",  # adjust to whatever port you use for local frontend testing
    ],
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "ok", "effects": [e.value for e in EffectType]}


@app.post("/predict", response_model=PredictResponse)
async def predict(
    image: UploadFile = File(...),
    effect: EffectType = Form(...),
):
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"unsupported content type: {image.content_type}. "
            f"allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )

    raw_bytes = await image.read()
    if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"file exceeds {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB limit",
        )
    if len(raw_bytes) == 0:
        raise HTTPException(status_code=400, detail="uploaded file is empty")

    np_buffer = np.frombuffer(raw_bytes, dtype=np.uint8)
    img = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(
            status_code=400,
            detail="could not decode image, file may be corrupt or not a valid image",
        )

    effect_fn = EFFECT_FUNCTIONS[effect]
    try:
        result = effect_fn(img)
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"effect processing failed: {exc}"
        ) from exc

    ok, encoded = cv2.imencode(".png", result)
    if not ok:
        raise HTTPException(status_code=500, detail="failed to encode result image")

    image_base64 = base64.b64encode(encoded.tobytes()).decode("utf-8")
    return PredictResponse(effect=effect.value, image_base64=image_base64, format="png")