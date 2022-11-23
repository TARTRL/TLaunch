# How to Run Distributed Job
``TLaunch`` provides a binary program ``tlaunchrun`` to help users start distributed job with the following functionalities:
- Create a distributed job in the cluster.
- According to the parameters set by the user,generate dag map and allocate gpu resources.
- Support multiple distributed launch modes.
In ``TLaunch``, a distributed job are named ``lpjob``.
## TLaunchrun Arguments
You can use ``tlaunchrun --help`` to view the details of ``tlauncherun``.
- ``lpjob_name`` - The name of this job.
- ``namespace`` - The namespace of this job.
- ``image`` - The docker image of every pods.
- ``image_pull_policy``  - The imagePullPolicy for a container and the tag of the image affect when the kubelet attempts to pull (download) the specified image.
	- ``Always`` 
		every time the cluster launches a container, the cluster queries the container image registry to resolve the name to an image digest. If the cluster has a container image with that exact digest cached locally, the cluster uses its cached image; otherwise, the cluster pulls the image with the resolved digest, and uses that image to launch the container. 
	 - ``IfNotPresent``
		 the image is pulled only if it is not already present locally.
	 - ``Never``
		 the cluster does not try fetching the image. If the image is somehow already present locally, the cluster attempts to start the container; otherwise, startup fails. 
- ``gpu`` - The number of gpu per pods.
- ``gpu_memory`` - The memory size of each gpu.
- ``gpu_cores`` - The maximum available cores of each gpu.
- ``set_save_path`` - Whether to automatically set a path to save the model, if use this option, TLaunch will generate a folder in TData/model and add a argument --save_path for all trainer pods, which is pointing to this folder.
- ``set_checkpoint_path`` - Whether to automatically set a path to save the checkpoint file, if use this option, TLaunch will generate a file named last.tar.gz in TData/model and add a argument --checkpoint_path for all trainer pods, which is pointing to this file. This parameter is usually used to store checkpoint and elastic deployment.
- launch method 
	The launch of distributed job, currently includes ``basic``,``torchrun``,``deepspeed``.
### Basic Launch
``basic`` launch means that users use user-defined methods to transfer the model and data of distributed job, TLaunch will provide some argument that may be used to help users complete it as easily as possible.
- ``num_trainer`` - The number of trainer, TLaunch will create pods equal to it.
- ``set_share_file`` - Whether to automatically set a cache file for transferring distributed shared information, if use this option, TLaunch will generate pointing to this file.

[examples](https://github.com/TARTRL/TLaunch/blob/main/examples/basic) gives some examples of use basic launcher to run a distributed job in TLaunch.
### Torchrun Launch
``torchrun`` is a distributed job launcher provided by pytorch.It is mentioned in the official documents of pytorch that `torchrun` provides a superset of the functionality as `torch.distributed.launch` with the following additional functionalities:
1. Worker failures are handled gracefully by restarting all workers.
2.  Worker `RANK` and `WORLD_SIZE` are assigned automatically.
3.  Number of nodes is allowed to change between minimum and maximum sizes (elasticity).

[examples](https://github.com/TARTRL/TLaunch/blob/main/examples/torchrun) gives some examples of use torchrun launcher to run a distributed job in TLaunch.
### Deepspeed Launch
``deepspeed`` is a lightweight wrapper on PyTorch. It contains many distributed training techniques, such as distributed training, mixed precision, gradient accumulation, and checkpoints so that you can focus on your model development. 

[examples](https://github.com/TARTRL/TLaunch/blob/main/examples/deepspeed) gives some examples of use deepspeed launcher to run a distributed job in TLaunch.


