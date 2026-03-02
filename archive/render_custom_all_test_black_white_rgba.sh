#!/usr/bin/env bash
{
set -euo pipefail

# Render all test images for custom datasets on black + white backgrounds,
# then compose transparent RGBA outputs from the paired renders.

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

NEURAL_ODE_CKPT="neural_ode_29999.pt"

for dataset in "${DATASETS[@]}"; do
  data_dir="${DATA_ROOT}/${dataset}"
  pattern="${RESULT_ROOT}/${dataset}"/*/ckpts/${NEURAL_ODE_CKPT}
  latest_ckpt="$(ls -1t ${pattern} 2>/dev/null | head -n 1 || true)"

  if [[ -z "${latest_ckpt}" ]]; then
    echo "[skip] no ${NEURAL_ODE_CKPT} found for ${dataset}"
    continue
  fi

  result_dir="${latest_ckpt%/ckpts/${NEURAL_ODE_CKPT}}"
  echo "============================================================"
  echo "[dataset] ${dataset}"
  echo "[ckpt] ${latest_ckpt}"
  echo "[result_dir] ${result_dir}"

  echo "[1/3] render black background test images"
  python3 full_render_rose.py \
    --data_dir "${data_dir}" \
    --dynamic-ckpt "${latest_ckpt}" \
    --result-dir "${result_dir}" \
    --bkgd-color 0 0 0

  echo "[2/3] render white background test images"
  python3 full_render_rose.py \
    --data_dir "${data_dir}" \
    --dynamic-ckpt "${latest_ckpt}" \
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
