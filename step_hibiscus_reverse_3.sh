{
python main_blender_rose.py default \
    --data_dir /scr/yuegao/grow_flow_datasets/Hibiscusmore_010008_reverse_s001_t080 \
    --static-ckpt /scr/yuegao/grow_flow_results/Hibiscusmore_010008_reverse_s001_t080/ckpts/gaussian_ckpt_29999_t0.pt \
    --full_trajectory_path /scr/yuegao/grow_flow_results/Hibiscusmore_010008_reverse_s001_t080/fixed_pc_traj_9/full_traj_2400.npy \
    --rtol 1e-5 \
    --atol 1e-6


exit 0
}
