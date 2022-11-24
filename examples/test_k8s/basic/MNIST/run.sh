#!/bin/bash
tlaunchrun --lpjob_name mnist --image docker.4pd.io/tlaunch/reverb:cv --gpu 1 --gpu_memory 10000 \
        --gpu_cores 100 --set_save_path basic --num_trainer 2 --set_share_file \
	train.py --save-model
