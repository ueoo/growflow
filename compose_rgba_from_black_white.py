#!/usr/bin/env python3
"""
Compose RGBA test renders from paired black/white background renders.

Expected inputs (relative to result_dir):
  - full_eval/test_masked/<camera>/<frame>.png   # black background
  - full_eval/test_white/<camera>/<frame>.png    # white background

Outputs:
  - full_eval/test_rgba/<camera>/<frame>.png
"""

import argparse
import os
from pathlib import Path

import imageio.v2 as imageio
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", required=True, help="Scene result directory.")
    parser.add_argument(
        "--black-subdir",
        default="full_eval/test_masked",
        help="Relative path to black-background renders.",
    )
    parser.add_argument(
        "--white-subdir",
        default="full_eval/test_white",
        help="Relative path to white-background renders.",
    )
    parser.add_argument(
        "--rgba-subdir",
        default="full_eval/test_rgba",
        help="Relative path where RGBA renders are written.",
    )
    parser.add_argument(
        "--eps",
        type=float,
        default=1e-6,
        help="Small epsilon to avoid divide-by-zero when alpha is near zero.",
    )
    return parser.parse_args()


def to_float01(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        img = np.repeat(img[..., None], 3, axis=-1)
    if img.shape[-1] == 4:
        img = img[..., :3]
    return img.astype(np.float32) / 255.0


def compose_rgba(black_rgb: np.ndarray, white_rgb: np.ndarray, eps: float) -> np.ndarray:
    # C_black = alpha * F
    # C_white = alpha * F + (1 - alpha)
    # => alpha = 1 - (C_white - C_black)
    alpha_rgb = 1.0 - (white_rgb - black_rgb)
    alpha = np.clip(alpha_rgb.mean(axis=-1), 0.0, 1.0)
    alpha_safe = np.maximum(alpha, eps)

    # Recover foreground color from premultiplied black composite.
    fg = np.clip(black_rgb / alpha_safe[..., None], 0.0, 1.0)
    fg[alpha <= eps] = 0.0

    rgba = np.dstack([fg, alpha[..., None]])
    return (rgba * 255.0 + 0.5).astype(np.uint8)


def main() -> None:
    args = parse_args()
    result_dir = Path(args.result_dir)
    black_root = result_dir / args.black_subdir
    white_root = result_dir / args.white_subdir
    rgba_root = result_dir / args.rgba_subdir

    if not black_root.exists():
        raise FileNotFoundError(f"Black render folder not found: {black_root}")
    if not white_root.exists():
        raise FileNotFoundError(f"White render folder not found: {white_root}")

    black_files = sorted(black_root.rglob("*.png"))
    if not black_files:
        raise RuntimeError(f"No PNG files found in: {black_root}")

    written = 0
    for black_path in black_files:
        rel = black_path.relative_to(black_root)
        white_path = white_root / rel
        out_path = rgba_root / rel

        if not white_path.exists():
            raise FileNotFoundError(f"Missing white render pair for: {rel}")

        black_img = to_float01(imageio.imread(black_path))
        white_img = to_float01(imageio.imread(white_path))

        if black_img.shape != white_img.shape:
            raise ValueError(
                f"Shape mismatch for {rel}: black {black_img.shape}, white {white_img.shape}"
            )

        rgba_img = compose_rgba(black_img, white_img, args.eps)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        imageio.imwrite(out_path, rgba_img)
        written += 1

    print(f"[done] wrote {written} RGBA PNG files to: {rgba_root}")


if __name__ == "__main__":
    main()
