#!/usr/bin/env python3
"""
Simple black background removal by thresholding RGB values.

Pixels with R,G,B <= black-threshold become fully transparent.
No rembg model is used.
"""

from __future__ import annotations

import argparse

from pathlib import Path

from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch-remove black background by threshold and save transparent PNGs."
    )
    parser.add_argument("--input-dir", required=True, help="Folder containing input images.")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Folder for output transparent PNGs (mirrors input structure).",
    )
    parser.add_argument(
        "--glob",
        default="*.png",
        help='File glob under input dir (default: "*.png").',
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search input files recursively.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files.",
    )
    parser.add_argument(
        "--black-threshold",
        type=int,
        default=8,
        help=("Pixels with R,G,B <= threshold are set to alpha=0. " "Use 0 for strict pure-black removal only."),
    )
    # Backward-compatible args from the earlier rembg-based version.
    parser.add_argument(
        "--skip-cleanup",
        action="store_true",
        help="Deprecated compatibility flag; ignored.",
    )
    parser.add_argument(
        "--model",
        default="unused",
        help="Deprecated compatibility option; ignored.",
    )
    parser.add_argument(
        "--alpha-threshold",
        type=int,
        default=0,
        help="Deprecated compatibility option; ignored.",
    )
    parser.add_argument(
        "--mask-dir",
        default="",
        help=(
            "Optional GT mask root folder. If set, mask files are matched by relative path "
            "from input-dir and applied to output alpha."
        ),
    )
    parser.add_argument(
        "--mask-glob",
        default="",
        help=(
            "Optional alternate suffix/pattern for masks when mask extension differs. "
            "Example: '.jpg' or '.png'. Empty means use input relative path as-is."
        ),
    )
    parser.add_argument(
        "--mask-threshold",
        type=int,
        default=127,
        help="Mask binarization threshold in [0,255]. Pixels > threshold are foreground.",
    )
    parser.add_argument(
        "--gt-dir",
        default="",
        help=(
            "Optional GT RGB root folder (same relative structure as input-dir). "
            "If set, foreground mask is derived from GT by removing black pixels."
        ),
    )
    parser.add_argument(
        "--gt-black-threshold",
        type=int,
        default=8,
        help=(
            "Black threshold used to derive binary foreground mask from GT RGB. "
            "Pixels with R,G,B <= threshold are treated as background."
        ),
    )
    return parser.parse_args()


def remove_black_pixels(img: Image.Image, black_threshold: int) -> Image.Image:
    rgba = img.convert("RGBA")
    data = bytearray(rgba.tobytes())

    for i in range(0, len(data), 4):
        r, g, b = data[i], data[i + 1], data[i + 2]
        if r <= black_threshold and g <= black_threshold and b <= black_threshold:
            data[i + 3] = 0

    return Image.frombytes("RGBA", rgba.size, bytes(data))


def apply_gt_mask(rgba: Image.Image, mask_img: Image.Image, mask_threshold: int) -> Image.Image:
    out = rgba.convert("RGBA")
    alpha = out.getchannel("A")
    mask_gray = mask_img.convert("L").resize(out.size, Image.NEAREST)

    alpha_data = bytearray(alpha.tobytes())
    mask_data = mask_gray.tobytes()

    for i in range(len(alpha_data)):
        if mask_data[i] <= mask_threshold:
            alpha_data[i] = 0

    out.putalpha(Image.frombytes("L", out.size, bytes(alpha_data)))
    return out


def apply_gt_rgb_black_mask(rgba: Image.Image, gt_img: Image.Image, gt_black_threshold: int) -> Image.Image:
    out = rgba.convert("RGBA")
    alpha = bytearray(out.getchannel("A").tobytes())
    gt_rgb = gt_img.convert("RGB").resize(out.size, Image.NEAREST)
    gt_data = gt_rgb.tobytes()

    for i in range(len(alpha)):
        j = i * 3
        r, g, b = gt_data[j], gt_data[j + 1], gt_data[j + 2]
        if r <= gt_black_threshold and g <= gt_black_threshold and b <= gt_black_threshold:
            alpha[i] = 0

    out.putalpha(Image.frombytes("L", out.size, bytes(alpha)))
    return out


def resolve_mask_path(src_path: Path, input_dir: Path, mask_dir: Path, mask_glob: str) -> Path:
    rel = src_path.relative_to(input_dir)
    if not mask_glob:
        return mask_dir / rel

    if mask_glob.startswith("."):
        return (mask_dir / rel).with_suffix(mask_glob)

    # If a non-suffix pattern is given, keep simple behavior and treat it as suffix.
    return (mask_dir / rel).with_suffix(mask_glob)


def iter_input_files(input_dir: Path, pattern: str, recursive: bool) -> list[Path]:
    files = input_dir.rglob(pattern) if recursive else input_dir.glob(pattern)
    return sorted([p for p in files if p.is_file()])


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input folder not found: {input_dir}")
    mask_dir = Path(args.mask_dir) if args.mask_dir else None
    if mask_dir is not None and not mask_dir.exists():
        raise FileNotFoundError(f"Mask folder not found: {mask_dir}")
    gt_dir = Path(args.gt_dir) if args.gt_dir else None
    if gt_dir is not None and not gt_dir.exists():
        raise FileNotFoundError(f"GT folder not found: {gt_dir}")
    if mask_dir is not None and gt_dir is not None:
        raise ValueError("Use either --mask-dir or --gt-dir, not both.")

    image_paths = iter_input_files(input_dir, args.glob, args.recursive)
    if not image_paths:
        raise RuntimeError(f'No files matched pattern "{args.glob}" under {input_dir}')

    written = 0
    skipped = 0
    missing_masks = 0

    threshold = max(0, min(255, args.black_threshold))
    mask_threshold = max(0, min(255, args.mask_threshold))
    gt_black_threshold = max(0, min(255, args.gt_black_threshold))
    for src_path in image_paths:
        rel = src_path.relative_to(input_dir)
        out_path = (output_dir / rel).with_suffix(".png")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if out_path.exists() and not args.overwrite:
            skipped += 1
            continue

        with Image.open(src_path) as src:
            out_rgba = remove_black_pixels(src, threshold)
            if mask_dir is not None:
                mask_path = resolve_mask_path(src_path, input_dir, mask_dir, args.mask_glob)
                if not mask_path.exists():
                    missing_masks += 1
                    raise FileNotFoundError(f"Missing GT mask for {rel}: {mask_path}")
                with Image.open(mask_path) as mask_img:
                    out_rgba = apply_gt_mask(out_rgba, mask_img, mask_threshold)
            if gt_dir is not None:
                gt_path = resolve_mask_path(src_path, input_dir, gt_dir, args.mask_glob)
                if not gt_path.exists():
                    missing_masks += 1
                    raise FileNotFoundError(f"Missing GT frame for {rel}: {gt_path}")
                with Image.open(gt_path) as gt_img:
                    out_rgba = apply_gt_rgb_black_mask(out_rgba, gt_img, gt_black_threshold)
            out_rgba.save(out_path, format="PNG")
            written += 1

    print(
        f"[done] processed={len(image_paths)} wrote={written} skipped={skipped} "
        f"threshold={threshold} mask_dir={mask_dir if mask_dir else 'none'} "
        f"gt_dir={gt_dir if gt_dir else 'none'} gt_black_threshold={gt_black_threshold} "
        f"missing_masks={missing_masks} output={output_dir}"
    )


if __name__ == "__main__":
    main()
