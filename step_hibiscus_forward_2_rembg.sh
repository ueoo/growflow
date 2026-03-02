{
python remove_black_bg_rembg.py \
    --input-dir /scr/yuegao/grow_flow_results/Hibiscusmore_010054_forward_s020_t080/fixed_pc_traj_7/test_r_3_it0_frames/out \
    --output-dir /scr/yuegao/grow_flow_results/Hibiscusmore_010054_forward_s020_t080/fixed_pc_traj_7/test_r_3_it0_frames/out_rgba \
    --gt-dir /scr/yuegao/grow_flow_results/Hibiscusmore_010054_forward_s020_t080/fixed_pc_traj_7/test_r_3_it0_frames/gt \
    --recursive \
    --glob "*.png" \
    --black-threshold 2 \
    --gt-black-threshold 2 \
    --overwrite

exit 0
}
