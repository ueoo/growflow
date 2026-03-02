{
python remove_black_bg_rembg.py \
    --input-dir /scr/yuegao/grow_flow_results/Rosemore_050047_reverse_s080_t179/fixed_pc_traj_11/test_r_6_it0_frames/out \
    --output-dir /scr/yuegao/grow_flow_results/Rosemore_050047_reverse_s080_t179/fixed_pc_traj_11/test_r_6_it0_frames/out_rgba \
    --gt-dir /scr/yuegao/grow_flow_results/Rosemore_050047_reverse_s080_t179/fixed_pc_traj_11/test_r_6_it0_frames/gt \
    --recursive \
    --glob "*.png" \
    --black-threshold 2 \
    --gt-black-threshold 2 \
    --overwrite

exit 0
}
