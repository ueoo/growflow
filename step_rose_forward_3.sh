{
python main_blender_rose.py default \
    --data_dir /scr/yuegao/grow_flow_datasets/Rosemore_050016_forward_s090_t179 \
    --static-ckpt /scr/yuegao/grow_flow_results/Rosemore_050016_forward_s090_t179/ckpts/gaussian_ckpt_29999_t0.pt \
    --full_trajectory_path /scr/yuegao/grow_flow_results/Rosemore_050016_forward_s090_t179/fixed_pc_traj_10/full_traj_2700.npy \
    --rtol 1e-5 \
    --atol 1e-6


exit 0
}
