# How to Use TPods
``TPod`` is a virtual user development environment for ``TLaunch`` for distributed scenarios. After the administrator creates a user with a console(he can customize the assigned system resources,including CPU, GPU, Memory, and Storage), a `pod` named '` tpod-console' ` with the ``TLaunch`` framework will be created in the user's namespace. 
## Login to TPod using SSH
The user can directly log in to the machine through SSH to access the cluster to quickly enter the development process.
## The storage structure of TPod
In ``TPod``, we will create your personal folder in the ``/TData`` directory, which will be synced with the remote via the mounted filesystem. The following content is pre-created in ``/TData``:

  - ```code```:Used to store training code
    - ```setup.sh```: Used to specify installation method for environment
  - ```data```:Used to store the data required for training
  - ```cache```:Used to store the cache data
  - ```models```:Used to store models
## Create LpJob
You can create an lpjob as you would in an external environment, but note that the lpjob's namespace must be in your personal namespace.

More information on creating LpJobs in k8s cluster are [here](./quick-start.md).
## Manage LpJob 
When the task is created, we can call the ``kubectl`` command to view the task status and logs. Several commonly used commands include:
  - ```kubectl get lpjobs```
  
  - ```kubectl get pods```

  - ```kubectl logs ${pod name}```

  - ```kubectl describe pods ${pod name}```

  - ```kubectl delete lpjobs ${lpjob name}```