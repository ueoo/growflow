#!/usr/bin/env python3
"""
Render all test images from step2 trajectory outputs.

This renderer uses:
  - static checkpoint (`gaussian_ckpt_*.pt`)
  - cached trajectory (`fixed_pc_traj_*/full_traj_*.npy`)

No dynamic neural ODE checkpoint is required.
"""

import os

import imageio.v2 as imageio
import numpy as np
import torch
import tyro

from configs.blender_config_rose import Config
from helpers.gsplat_utils import get_raster_params_blender
from runner import Runner


def display_config(cfg):
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="Trajectory Render Settings")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")

    for key, value in sorted(vars(cfg).items()):
        table.add_row(key, str(value))
    console.print("\n")
    console.print(table)
    console.print("\n")


@torch.no_grad()
def main(cfg: Config):
    display_config(cfg)
    assert cfg.static_ckpt is not None, "please specify static_ckpt"
    assert cfg.full_trajectory_path != "", "please specify full_trajectory_path"

    print(f"Loading static checkpoint: {cfg.static_ckpt[0]}")
    print(f"Loading trajectory: {cfg.full_trajectory_path}")

    runner = Runner(cfg)

    ckpt = torch.load(cfg.static_ckpt[0], map_location=runner.device, weights_only=False)
    for k in runner.gaussians.splats.keys():
        runner.gaussians.splats[k].data = ckpt["splats"][k]
    step = int(ckpt["step"])

    full_traj = np.load(cfg.full_trajectory_path, allow_pickle=True).astype(np.float32)
    pred_param = torch.from_numpy(full_traj).to(device=runner.device, dtype=torch.float32)

    full_eval_path = os.path.join(cfg.result_dir, "full_eval")
    if cfg.bkgd_color == [1, 1, 1]:
        test_eval_path = os.path.join(full_eval_path, "test_white")
    else:
        test_eval_path = os.path.join(full_eval_path, "test_masked")
    os.makedirs(test_eval_path, exist_ok=True)

    raster_params = get_raster_params_blender(
        cfg, runner.gaussians.splats, runner.testset, runner.gaussians.deformed_params_dict
    )

    num_test_timesteps = runner.testset.num_timesteps()
    if pred_param.shape[0] != num_test_timesteps:
        # Keep rendering robust when cached trajectory length differs from test split length.
        num_shared = min(pred_param.shape[0], num_test_timesteps)
        print(
            f"[warn] trajectory timesteps ({pred_param.shape[0]}) != test timesteps ({num_test_timesteps}); "
            f"rendering first {num_shared} timesteps"
        )
        pred_param = pred_param[:num_shared]
        num_test_timesteps = num_shared

    int_t = list(range(num_test_timesteps))
    c2ws, _, _, _, _ = runner.testset.__getitems__(int_t)
    raster_params["viewmats"] = c2ws.to(runner.device)

    out_img, _ = runner.gaussians.rasterize_with_dynamic_params_batched(
        pred_param, raster_params, activate_params=True
    )
    eval_colors = torch.clamp(out_img, 0.0, 1.0)
    if cfg.is_reverse:
        eval_colors = torch.flip(eval_colors, dims=[1])

    all_test_camera_ids = list(runner.testset[0]["image_id"])
    for i, cam_id in enumerate(all_test_camera_ids):
        cam_test_path = f"{test_eval_path}/{cam_id}"
        os.makedirs(cam_test_path, exist_ok=True)
        pred_images = eval_colors[i]  # (T, H, W, 3)

        for j, frame in enumerate(pred_images):
            pred_image = (frame * 255).cpu().numpy().astype(np.uint8)
            imageio.imwrite(f"{cam_test_path}/{j:05d}.png", pred_image)

    image_height, image_width = eval_colors.shape[-2], eval_colors.shape[-3]
    all_test_frames = eval_colors.contiguous().view(-1, image_height, image_width, 3)
    all_test_frames = (all_test_frames * 255).cpu().numpy().astype(np.uint8)
    imageio.mimwrite(
        f"{test_eval_path}/all_test_step{step}_video.mp4",
        all_test_frames,
        fps=num_test_timesteps / cfg.video_duration,
    )
    print(f"[done] wrote renders to: {test_eval_path}")


if __name__ == "__main__":
    cfg = tyro.cli(Config)
    cfg.adjust_steps(cfg.steps_scaler)
    main(cfg)
