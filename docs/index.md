<div align="center">
<img width="300px" height="auto" src="./figures/tlaunch.png">
</div>

# TLaunch Handbook

[Deepmind launchpad](https://github.com/deepmind/launchpad) is a library that
helps writing distributed program in a simple way. But currently it only
supports (or has only open-sourced) launching programs on a single host, either
multi-threaded or multi-processed. This library provides a way of launching existing launchpad programs on multiple
nodes. Only some simple modification to your program is needed.

To learn how to create and manager your job on TLaunch, please follow our [User Manual](./manual/cluster-user/README.md).

To learn how to install and manage TLaunch in your cluster, please follow [Admin Manual](./manual/cluster-admin/README.md).

To view a general introduction of TLaunch, please refer to the [Github Readme](https://github.com/TARTRL/TLaunch/blob/main/README.md).

## Citing TLaunch

If you use TLaunch in your work, please cite us:

```bibtex
@article{tartrl2021tlaunch,
    title={TLaunch: Launch Programs on Multiple Hosts},
    author={Shiyu Huang, Sen Na, Shizhen Xu, Ting Chen, Jun Zhu, Zeming Liu},
    year={2021},
    howpublished={\url{https://github.com/TARTRL/TLaunch}},
}
```