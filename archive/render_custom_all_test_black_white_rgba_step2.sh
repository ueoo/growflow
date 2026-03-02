#!/usr/bin/env bash
{
set -euo pipefail

# Render all test images for custom datasets on black + white backgrounds
# from step2 outputs (static ckpt + cached trajectory), then compose RGBA.

DATA_ROOT="/scr/yuegao/grow_flow_datasets"
RESULT_ROOT="/scr/yuegao/grow_flow_results"

DATASETS=(
  # "Dahliamorefix_020033_reverse_s010_t100"
  # "Daisymorefix_020044_forward_s020_t080"
  # "Lilymore_020098_forward_s010_t100"
  # "Lilymore_020016_reverse_s020_t100"
  # "Rosemore_050016_forward_s090_t179"
  "Rosemore_050047_reverse_s080_t179"
)

for dataset in "${DATASETS[@]}"; do
  data_dir="${DATA_ROOT}/${dataset}"
  traj_pattern="${RESULT_ROOT}/${dataset}"/*/fixed_pc_traj_*/full_traj_*.npy
  latest_traj="$(ls -1t ${traj_pattern} 2>/dev/null | head -n 1 || true)"

  if [[ -z "${latest_traj}" ]]; then
    echo "[skip] no step2 trajectory found for ${dataset}"
    continue
  fi

  # latest_traj: <result_dir>/fixed_pc_traj_x/full_traj_y.npy
  result_dir="$(dirname "$(dirname "${latest_traj}")")"
  static_ckpt="${result_dir}/ckpts/gaussian_ckpt_29999_t0.pt"
  if [[ ! -f "${static_ckpt}" ]]; then
    # Fallback if static stage stopped at a different step count.
    static_ckpt="$(ls -1t "${result_dir}"/ckpts/gaussian_ckpt_*_t0.pt 2>/dev/null | head -n 1 || true)"
  fi
  if [[ ! -f "${static_ckpt}" ]]; then
    echo "[skip] missing static checkpoint for ${dataset}: ${static_ckpt}"
    continue
  fi

  echo "============================================================"
  echo "[dataset] ${dataset}"
  echo "[static_ckpt] ${static_ckpt}"
  echo "[full_trajectory] ${latest_traj}"
  echo "[result_dir] ${result_dir}"

  echo "[1/3] render black background test images (step2 trajectory)"
  python3 full_render_from_trajectory.py \
    --data_dir "${data_dir}" \
    --static-ckpt "${static_ckpt}" \
    --full_trajectory_path "${latest_traj}" \
    --result-dir "${result_dir}" \
    --bkgd-color 0 0 0

  echo "[2/3] render white background test images (step2 trajectory)"
  python3 full_render_from_trajectory.py \
    --data_dir "${data_dir}" \
    --static-ckpt "${static_ckpt}" \
    --full_trajectory_path "${latest_traj}" \
    --result-dir "${result_dir}" \
    --bkgd-color 1 1 1

  echo "[3/3] compose RGBA test images"
  python3 compose_rgba_from_black_white.py \
    --result-dir "${result_dir}" \
    --black-subdir "full_eval/test_masked" \
    --white-subdir "full_eval/test_white" \
    --rgba-subdir "full_eval/test_rgba"
done

echo "============================================================"
echo "[done] black + white + rgba renders completed."

exit 0
}
