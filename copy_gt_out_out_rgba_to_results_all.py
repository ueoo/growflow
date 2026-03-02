#!/usr/bin/env python3
"""
Copy gt/out/out_rgba frames from grow_flow_results to grow_flow_results_all.

Default source layout:
  /scr/yuegao/grow_flow_results/<scene>/.../test_r_*_it*_frames/{gt,out,out_rgba}/*.png

Default destination layout:
  /scr/yuegao/grow_flow_results_all/<scene>/{gt,out,out_rgba}/*.png
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


FRAME_TYPES = ("gt", "out", "out_rgba")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy gt/out/out_rgba frames into a unified results folder."
    )
    parser.add_argument(
        "--src-root",
        default="/scr/yuegao/grow_flow_results",
        help="Source root containing scene folders.",
    )
    parser.add_argument(
        "--dst-root",
        default="/scr/yuegao/grow_flow_results_all",
        help="Destination root to collect copied frames.",
    )
    parser.add_argument(
        "--glob",
        default="*.png",
        help='Frame glob to copy inside each split folder (default: "*.png").',
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite destination files if they already exist.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be copied without writing files.",
    )
    return parser.parse_args()


def is_frame_split_dir(path: Path) -> bool:
    parent = path.parent.name
    return path.name in FRAME_TYPES and parent.startswith("test_r_") and parent.endswith("_frames")


def iter_scene_dirs(src_root: Path) -> list[Path]:
    return sorted([p for p in src_root.iterdir() if p.is_dir()])


def copy_scene(scene_dir: Path, dst_root: Path, pattern: str, overwrite: bool, dry_run: bool) -> dict[str, int]:
    stats = {"copied": 0, "skipped": 0}
    scene_name = scene_dir.name
    dst_scene_root = dst_root / scene_name

    for split in FRAME_TYPES:
        split_dirs = [p for p in scene_dir.rglob(split) if p.is_dir() and is_frame_split_dir(p)]
        for split_dir in split_dirs:
            # Flatten destination: put all split frames directly under scene/<split>.
            dst_split_dir = dst_scene_root / split
            for src_file in split_dir.rglob(pattern):
                if not src_file.is_file():
                    continue
                dst_file = dst_split_dir / src_file.name
                if dst_file.exists() and not overwrite:
                    stats["skipped"] += 1
                    continue
                if not dry_run:
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dst_file)
                stats["copied"] += 1

    return stats


def main() -> None:
    args = parse_args()
    src_root = Path(args.src_root)
    dst_root = Path(args.dst_root)

    if not src_root.exists():
        raise FileNotFoundError(f"Source root not found: {src_root}")

    scene_dirs = iter_scene_dirs(src_root)
    if not scene_dirs:
        raise RuntimeError(f"No scene folders found under: {src_root}")

    total_copied = 0
    total_skipped = 0
    for scene_dir in scene_dirs:
        stats = copy_scene(
            scene_dir=scene_dir,
            dst_root=dst_root,
            pattern=args.glob,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
        )
        total_copied += stats["copied"]
        total_skipped += stats["skipped"]
        if stats["copied"] > 0 or stats["skipped"] > 0:
            print(f"[scene] {scene_dir.name}: copied={stats['copied']} skipped={stats['skipped']}")

    mode = "dry-run" if args.dry_run else "done"
    print(
        f"[{mode}] scenes={len(scene_dirs)} copied={total_copied} "
        f"skipped={total_skipped} dst_root={dst_root}"
    )


if __name__ == "__main__":
    main()
