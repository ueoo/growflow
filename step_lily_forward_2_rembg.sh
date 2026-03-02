{
python remove_black_bg_rembg.py \
    --input-dir /scr/yuegao/grow_flow_results/Lilymore_020098_forward_s010_t100/fixed_pc_traj_10/test_r_10_it0_frames/out \
    --output-dir /scr/yuegao/grow_flow_results/Lilymore_020098_forward_s010_t100/fixed_pc_traj_10/test_r_10_it0_frames/out_rgba \
    --gt-dir /scr/yuegao/grow_flow_results/Lilymore_020098_forward_s010_t100/fixed_pc_traj_10/test_r_10_it0_frames/gt \
    --recursive \
    --glob "*.png" \
    --black-threshold 2 \
    --gt-black-threshold 2 \
    --overwrite

exit 0
}
