# Installation Guide
First, let's clone this repository. Then `cd` into the repository, and execute:
``` sh
pip install -r requirements.txt
pip install .
```
## [Optional] Kubernetes Support

If you want to use TLaunch with Kubernetes:
1. `go` installed on host machine to run `kustomize`. 
2. A running kubernetes cluster. 
3. [Volcano scheduler](https://github.com/volcano-sh/volcano) installed to
   enable gang scheduling. [This](https://volcano.sh/en/docs/installation/) will
   tell you how to install volcano for your kubernetes cluster.

### Install and run `lp-operator` on your kubernetes cluster

``` sh
cd lp-operator
make deploy
```

Then `lp-operator` should be running in namespace `lp-operator-system`. You can
use `kubectl get all -n lp-operator-system` to check the status of the running
operator.

## [Optional] Kubernetes Usage

Check [here](./k8s_usage.md) for more information.

## [Optional] TPods Usage
Check [here](./tpods.md) for more information.

