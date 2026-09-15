from enum import Enum

from pydantic import BaseModel


class EffectType(str, Enum):
    cartoonify = "cartoonify"
    grayscale = "grayscale"
    pencil_sketch = "pencil_sketch"
    oil_painting = "oil_painting"
    pixel_art = "pixel_art"


class PredictResponse(BaseModel):
    effect: str
    image_base64: str
    format: str = "png"