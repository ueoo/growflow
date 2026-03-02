{
python main_blender_rose.py default \
    --data_dir /scr/yuegao/grow_flow_datasets/Lilymore_020098_forward_s010_t100 \
    --static-ckpt /scr/yuegao/grow_flow_results/Lilymore_020098_forward_s010_t100/ckpts/gaussian_ckpt_29999_t0.pt \
    --full_trajectory_path /scr/yuegao/grow_flow_results/Lilymore_020098_forward_s010_t100/fixed_pc_traj_10/full_traj_2700.npy \
    --rtol 1e-5 \
    --atol 1e-6


exit 0
}
