"""
Five image effects, tuned and locked in notebooks/effects_dev.ipynb.

Each function is pure: takes a numpy.ndarray (BGR, as read by cv2.imread)
and returns a numpy.ndarray (BGR). No I/O, no framework code - the notebook
and the API layer both call these directly.
"""
import cv2
import numpy as np


def grayscale(img: np.ndarray, clip_limit: float = 2.0, tile: int = 8) -> np.ndarray:
    """CLAHE-boosted grayscale. Plain grayscale crushes detail in dark
    regions (dark skin, dark clothing) against a bright background; CLAHE
    recovers it by equalizing contrast locally instead of globally.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile, tile))
    gray = clahe.apply(gray)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def pencil_sketch(
    img: np.ndarray,
    sigma_s: float = 40,
    sigma_r: float = 0.15,
    shade_factor: float = 0.02,
    pre_blur: int = 3,
) -> np.ndarray:
    """Graphite-sketch effect via cv2.pencilSketch. A small pre-blur is
    applied first to stop real photo sensor noise from being drawn as
    speckled texture.
    """
    if pre_blur:
        img = cv2.GaussianBlur(img, (pre_blur, pre_blur), 0)
    gray_sketch, _color_sketch = cv2.pencilSketch(
        img, sigma_s=sigma_s, sigma_r=sigma_r, shade_factor=shade_factor
    )
    return cv2.cvtColor(gray_sketch, cv2.COLOR_GRAY2BGR)


def cartoonify(
    img: np.ndarray,
    d: int = 9,
    sigma_color: float = 75,
    sigma_space: float = 75,
    bilateral_iters: int = 2,
    block_size: int = 9,
    C: int = 4,
    median_blur: int = 9,
) -> np.ndarray:
    """Flat-color regions (repeated bilateral filtering) combined with a
    black edge mask (adaptive threshold on a heavily median-blurred
    grayscale). The median blur is what keeps noise from real photos out
    of the edge mask.
    """
    color = img.copy()
    for _ in range(bilateral_iters):
        color = cv2.bilateralFilter(color, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.medianBlur(gray, median_blur)
    edges = cv2.adaptiveThreshold(
        gray_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,
        blockSize=block_size, C=C,
    )
    edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    return cv2.bitwise_and(color, edges_bgr)


def oil_painting(img: np.ndarray, size: int = 7, dyn_ratio: int = 1) -> np.ndarray:
    """Oil-painting effect via cv2.xphoto.oilPainting. Requires
    opencv-contrib-python, not plain opencv-python. Slowest of the 5
    effects - scales with image size, so large uploads may need
    client-side resizing first.
    """
    return cv2.xphoto.oilPainting(img, size, dyn_ratio)


def pixel_art(img: np.ndarray, block_size: int = 8, k_colors: int = 16) -> np.ndarray:
    """Downscale with INTER_AREA (averages blocks - correct for shrinking),
    optionally quantize colors with k-means for a limited retro palette,
    then upscale back with INTER_NEAREST to keep hard pixel-block edges.
    """
    h, w = img.shape[:2]
    small = cv2.resize(
        img, (max(1, w // block_size), max(1, h // block_size)), interpolation=cv2.INTER_AREA
    )

    if k_colors:
        data = small.reshape(-1, 3).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.5)
        _, labels, centers = cv2.kmeans(data, k_colors, None, criteria, 5, cv2.KMEANS_RANDOM_CENTERS)
        centers = centers.astype(np.uint8)
        small = centers[labels.flatten()].reshape(small.shape)

    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)