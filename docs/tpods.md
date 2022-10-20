## TPods
### 1.使用SSH登录TPod
```TPod```是一款面向分布式场景，为```TLaunch```准备的用户及资源管理工具。当管理员使用```TPod```创建用户后，可以自定义的为其指定分配的系统资源（包括CPU、GPU、Memory、Storage），并为该用户创建一个已经预装好```TLaunch```框架的```TPod```开发机，用户可以直接通过SSH登录该机器访问集群，以快速进入开发流程。
#### TPod的存储结构
在```TPod```中，我们会在```/TData```目录下创建你的个人文件夹，该文件夹会通过挂载的文件系统与远端同步。```/TData```内会预先创建以下内容：

  - ```code```:用于存放训练代码
    - ```setup.sh```:用于指定训练环境及代码的安装方法
  - ```data```:用于存放训练所需的数据
  - ```cache```:用于存放分布式计算过程中产生的缓存文件
  - ```models```:用于存放模型数据
### 2.存放算法代码并指定安装方法
在多数分布式场景中，少量的代码往往会经常改动。若每次改动代码都重新构建镜像，会浪费大量的时间。因此，我们可以将这部分代码存放在```/TData/code```文件夹中。在训练中，每当一个```pods```被创建时，都将先按照```code```文件夹中的```setup.sh```脚本更新环境
### 3.调用TLaunch创建任务
Check [here](./k8s_usage.md) for more information.
### 4.管理任务
当任务创建完成后，我们可以调用```kubectl```来查看任务状态及日志，其中常用的几条指令包括：
  - 查看正在运行中的任务：```kubectl get lpjobs```
  - 查看正在运行中的pods:```kubectl get pods```
  - 查看pod节点日志:```kubectl logs ${pod name}```
  - 查看pod节点详细信息:```kubectl describe pods ${pod name}```
  - 删除任务:```kubectl delete lpjobs ${lpjob name}```