#!/bin/bash
tlaunchrun --lpjob_name mnist --image docker.4pd.io/tlaunch/reverb:cv --gpu 4 --gpu_memory 10000 \
        --gpu_cores 100 --set_save_path torchrun --nnodes 2 --nproc_per_node 4 \
	train.py --save-model
