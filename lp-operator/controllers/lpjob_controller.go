/*
Copyright 2021.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package controllers

import (
	"context"
	"time"

	"github.com/go-logr/logr"
	corev1 "k8s.io/api/core/v1"
	v1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	"k8s.io/apimachinery/pkg/runtime"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/manager"

	launchpadv1alpha1 "lp-operator/api/v1alpha1"

	"volcano.sh/apis/pkg/apis/scheduling/v1beta1"

	volcanoclient "volcano.sh/apis/pkg/client/clientset/versioned"
)

const (
	serviceOwnerKey = ".metadata.controller"
	podOwnerKey     = ".metadata.controller"
	lpStopExitCode  = 25

	gitSyncImage = "registry.cn-zhangjiakou.aliyuncs.com/kube-ai/git-sync:v3.1.1"
	mcImage      = "reg.real-ai.cn/launchpad/mc:latest"
	pipImage     = "reg.real-ai.cn/launchpad/pip-install:latest"
)

var (
	apiGroupVersion = launchpadv1alpha1.GroupVersion.String()
)

// LpJobReconciler reconciles a LpJob object
type LpJobReconciler struct {
	client.Client
	volcanoClientSet volcanoclient.Interface
	Scheme           *runtime.Scheme
	Logger           logr.Logger
}

//+kubebuilder:rbac:groups=realai.cn,resources=lpjobs,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=realai.cn,resources=lpjobs/status,verbs=get;update;patch
//+kubebuilder:rbac:groups=realai.cn,resources=lpjobs/finalizers,verbs=update
//+kubebuilder:rbac:groups=core,resources=pods,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=core,resources=services,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=core,resources=configmaps,verbs=get;list;watch;create;update;patch;delete

func NewReconciler(mgr manager.Manager) *LpJobReconciler {
	cfg := mgr.GetConfig()
	volcanoClientSet := volcanoclient.NewForConfigOrDie(cfg)

	r := &LpJobReconciler{
		Client:           mgr.GetClient(),
		Scheme:           mgr.GetScheme(),
		volcanoClientSet: volcanoClientSet,
	}

	return r
}

// Reconcile is part of the main kubernetes reconciliation loop which aims to
// move the current state of the cluster closer to the desired state.
// TODO(user): Modify the Reconcile function to compare the state specified by
// the LpJob object against the actual cluster state, and then
// perform operations to make the cluster state reflect the state specified by
// the user.
//
// For more details, check Reconcile and its Result here:
// - https://pkg.go.dev/sigs.k8s.io/controller-runtime@v0.9.2/pkg/reconcile
func (r *LpJobReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	// setup logger
	r.Logger = log.FromContext(ctx).WithValues("lpjob", req.NamespacedName)

	lpJob := &launchpadv1alpha1.LpJob{}
	if err := r.Get(ctx, req.NamespacedName, lpJob); err != nil {
		r.Logger.Error(err, "Unable to get LPJob")
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}
	if lpJob.Status.CompletionTime != nil {
		// don't care if it is already finished
		return ctrl.Result{}, nil
	}

	if lpJob.Status.StartTime == nil {
		lpJob.Status.StartTime = &metav1.Time{Time: time.Now()}
	}
	lpJob.Status.LastReconcileTime = &metav1.Time{Time: time.Now()}

	r.Logger.Info("Sync configmap")
	if err := r.syncConfigMap(lpJob, ctx, req); err != nil {
		r.Logger.Error(err, "Failed to sync configmap")
		return ctrl.Result{}, err
	}

	r.Logger.Info("Sync service")
	if err := r.syncService(lpJob, ctx, req); err != nil {
		r.Logger.Error(err, "Failed to sync service")
		return ctrl.Result{}, err
	}

	if lpJob.Spec.EnableGangScheduling {
		r.Logger.Info("Sync podgroup")
		if err := r.syncPodGroup(lpJob, ctx, req); err != nil {
			r.Logger.Error(err, "Failed to sync podgroup")
			return ctrl.Result{}, err
		}
	}

	r.Logger.Info("Sync pods")
	if err := r.syncPods(lpJob, ctx, req); err != nil {
		r.Logger.Error(err, "Failed to sync pods")
		return ctrl.Result{}, err
	}
	if err := r.Status().Update(ctx, lpJob); err != nil {
		r.Logger.Error(err, "Failed to update lpJob status")
		return ctrl.Result{}, err
	}

	r.Logger.Info("Finish one episode")
	return ctrl.Result{}, nil
}

func (r *LpJobReconciler) createPod(lpJob *launchpadv1alpha1.LpJob, ctx context.Context, req ctrl.Request, roleName string, id int) error {
	role := lpJob.Spec.Roles[roleName]
	podTemplate := role.Template.DeepCopy()

	if podTemplate.Annotations == nil {
		podTemplate.Annotations = map[string]string{}
	}
	podTemplate.Annotations["sidecar.istio.io/inject"] = "false"
	if lpJob.Spec.EnableGangScheduling {
		// let all groups start together
		podTemplate.Annotations["scheduling.k8s.io/group-name"] = lpJob.Name
		podTemplate.Annotations["volcano.sh/task-spec"] = roleName
		podTemplate.Spec.SchedulerName = "volcano"
	}

	podTemplate.Name = podName(lpJob.Name, roleName, id)

	podTemplate.Spec.Hostname = podHostName(roleName, id)
	podTemplate.Spec.Subdomain = lpJob.Name
	podTemplate.Spec.RestartPolicy = "Never"
	if podTemplate.Spec.Volumes == nil {
		podTemplate.Spec.Volumes = []v1.Volume{}
	}
	// attach to configmap
	podTemplate.Spec.Volumes = append(podTemplate.Spec.Volumes, v1.Volume{
		Name: "config",
		VolumeSource: v1.VolumeSource{
			ConfigMap: &v1.ConfigMapVolumeSource{
				LocalObjectReference: v1.LocalObjectReference{Name: lpJob.Name},
			},
		},
	})
	for i := range podTemplate.Spec.Containers {
		container := &podTemplate.Spec.Containers[i]
		container.VolumeMounts = append(container.VolumeMounts, v1.VolumeMount{
			Name:      "config",
			MountPath: "/etc/config",
		})
	}

	if source := lpJob.Spec.Source; source != nil {
		if source.Git != nil {
			// using git source
			podTemplate.Spec.InitContainers = append(podTemplate.Spec.InitContainers, v1.Container{
				Name:  "init-git",
				Image: gitSyncImage,
				Env:   genGitSyncEnv(source.Git),
				VolumeMounts: []v1.VolumeMount{
					{Name: "source", MountPath: "/tmp/git"},
				},
			})
		}
		if source.Minio != nil {
			// using minio source
			podTemplate.Spec.InitContainers = append(podTemplate.Spec.InitContainers, v1.Container{
				Name:    "init-minio",
				Image:   mcImage,
				Command: buildMcCommand(source.Minio),
				VolumeMounts: []v1.VolumeMount{
					{Name: "source", MountPath: "/build"},
				},
			})
		}
		// container to download pip packages
		podTemplate.Spec.InitContainers = append(podTemplate.Spec.InitContainers, v1.Container{
			Name:  "init-pip",
			Image: pipImage,
			Env:   []v1.EnvVar{{Name: "SOURCE_DIR", Value: "/source"}},
			VolumeMounts: []v1.VolumeMount{
				{Name: "source", MountPath: "/source"},
				{Name: "pip-packages", MountPath: "/root/.local/lib/python3.9/site-packages"},
			},
		})

		podTemplate.Spec.Volumes = append(podTemplate.Spec.Volumes, v1.Volume{
			Name:         "source",
			VolumeSource: v1.VolumeSource{EmptyDir: nil},
		}, v1.Volume{
			Name:         "pip-packages",
			VolumeSource: v1.VolumeSource{EmptyDir: nil},
		})

		for i := range podTemplate.Spec.Containers {
			container := &podTemplate.Spec.Containers[i]
			container.VolumeMounts = append(container.VolumeMounts, v1.VolumeMount{
				Name:      "source",
				MountPath: "/workdir",
			}, v1.VolumeMount{
				Name:      "pip-packages",
				MountPath: "/root/.local/lib/python3.9/site-packages",
			})
		}

	}

	pod := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Name:        podTemplate.Name,
			Namespace:   req.Namespace,
			Labels:      map[string]string{"app": lpJob.Name},
			Annotations: podTemplate.Annotations,
		},
		Spec: podTemplate.Spec,
	}

	if err := ctrl.SetControllerReference(lpJob, pod, r.Scheme); err != nil {
		return err
	}
	return r.Create(ctx, pod)
}

func (r *LpJobReconciler) syncPods(lpJob *launchpadv1alpha1.LpJob, ctx context.Context, req ctrl.Request) error {
	pods := corev1.PodList{}
	if err := r.List(ctx, &pods, client.InNamespace(req.Namespace), client.MatchingFields{podOwnerKey: req.Name}); err != nil {
		r.Logger.Error(err, "Unable to list child pods")
		return err
	}

	podNames := make(map[string]corev1.PodStatus)
	for _, pod := range pods.Items {
		podNames[pod.Name] = pod.Status
		if pod.Status.Phase == corev1.PodFailed && len(pod.Status.ContainerStatuses) > 0 {
			state := pod.Status.ContainerStatuses[0].State
			if state.Terminated != nil && state.Terminated.ExitCode == lpStopExitCode {
				// pod called `lp.stop()`, delete lpJob
				// TODO: graceful termination, instead of killing lpJob brutally
				if lpJob.Status.CompletionTime == nil {
					lpJob.Status.CompletionTime = &metav1.Time{Time: time.Now()}
				}

				r.markJobComplete(lpJob, ctx, pods.Items)
				return nil
			}
		}
	}

	r.Logger.Info("Current pod status", "podCount", len(pods.Items))
	if lpJob.Status.RoleStatuses == nil {
		lpJob.Status.RoleStatuses = make(map[string]launchpadv1alpha1.RoleStatus)
	}
	for name, role := range lpJob.Spec.Roles {
		roleStatus := launchpadv1alpha1.RoleStatus{}
		for i := 0; i < int(*role.Replicas); i++ {
			podStatus, ok := podNames[podName(lpJob.Name, name, i)]
			if !ok {
				// need to create the pod
				if err := r.createPod(lpJob, ctx, req, name, i); err != nil {
					r.Logger.Error(err, "Failed to create pod", "podName", podName(lpJob.Name, name, i))
					return err
				}
			} else {
				switch podStatus.Phase {
				case corev1.PodRunning:
					roleStatus.Running++
				case corev1.PodSucceeded:
					roleStatus.Completed++
				case corev1.PodFailed:
					roleStatus.Failed++
				}
			}
		}
		lpJob.Status.RoleStatuses[name] = roleStatus
	}

	return nil
}

// Mark lpjob as complete
func (r *LpJobReconciler) markJobComplete(lpJob *launchpadv1alpha1.LpJob, ctx context.Context, pods []corev1.Pod) {
	// make a final collect of the pod info
	if lpJob.Status.RoleStatuses == nil {
		lpJob.Status.RoleStatuses = make(map[string]launchpadv1alpha1.RoleStatus)
	}
	for name, _ := range lpJob.Spec.Roles {
		lpJob.Status.RoleStatuses[name] = launchpadv1alpha1.RoleStatus{}
	}
	for _, pod := range pods {
		roleName := getRoleName(pod.Name)
		roleStatus := lpJob.Status.RoleStatuses[roleName]
		if len(pod.Status.ContainerStatuses) > 0 {
			containerStatus := pod.Status.ContainerStatuses[0]
			terminated := containerStatus.State.Terminated
			if terminated != nil {
				// this pod is either errored out or completed or exited with a magic exit code
				if terminated.ExitCode == 0 || terminated.ExitCode == lpStopExitCode {
					roleStatus.Completed++
				} else {
					roleStatus.Failed++
				}
			} else {
				// still running, clean this up
				if err := r.Delete(ctx, &pod); err != nil {
					r.Logger.Error(err, "Failed to clean up running pod")
					roleStatus.Failed++
				} else {
					roleStatus.Completed++
				}
			}
		}
		lpJob.Status.RoleStatuses[roleName] = roleStatus
	}
}

func (r *LpJobReconciler) syncConfigMap(lpJob *launchpadv1alpha1.LpJob, ctx context.Context, req ctrl.Request) error {
	configMap := &corev1.ConfigMap{}
	if err := r.Get(ctx, req.NamespacedName, configMap); err == nil {
		return nil
	}

	// Create configmap
	dataMap := make(map[string][]byte)
	for name, role := range lpJob.Spec.Roles {
		dataMap[name] = role.Executable
	}
	configMap = &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{Name: lpJob.Name, Namespace: req.Namespace},
		BinaryData: dataMap,
	}
	if err := ctrl.SetControllerReference(lpJob, configMap, r.Scheme); err != nil {
		return err
	}
	return r.Create(ctx, configMap)
}

func (r *LpJobReconciler) syncPodGroup(lpJob *launchpadv1alpha1.LpJob, ctx context.Context, req ctrl.Request) error {
	// try to find existing podgroup
	podGroup := &v1beta1.PodGroup{}
	if err := r.Get(ctx, req.NamespacedName, podGroup); err == nil {
		return nil
	}

	podGroup = &v1beta1.PodGroup{
		TypeMeta: metav1.TypeMeta{
			APIVersion: "v1beta1",
			Kind:       "PodGroup",
		},
		ObjectMeta: metav1.ObjectMeta{
			Name:        lpJob.Name,
			Namespace:   lpJob.Namespace,
			Annotations: lpJob.Annotations,
		},
		Spec: v1beta1.PodGroupSpec{
			MinMember:         replicaCount(lpJob),
			Queue:             "",
			PriorityClassName: "",
		},
	}
	if err := ctrl.SetControllerReference(lpJob, podGroup, r.Scheme); err != nil {
		return err
	}
	return r.Create(ctx, podGroup)
}

func (r *LpJobReconciler) syncService(lpJob *launchpadv1alpha1.LpJob, ctx context.Context, req ctrl.Request) error {
	service := &corev1.Service{}
	if err := r.Get(ctx, req.NamespacedName, service); err == nil {
		return nil
	}

	service = &corev1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name:      lpJob.Name,
			Namespace: req.Namespace,
			Labels: map[string]string{
				"app": lpJob.Name,
			},
		},
		Spec: corev1.ServiceSpec{
			Ports: []corev1.ServicePort{
				{Port: 8001, Name: lpJob.Name},
			},
			Selector: map[string]string{
				"app": lpJob.Name,
			},
			ClusterIP: "None",
		},
	}
	if err := ctrl.SetControllerReference(lpJob, service, r.Scheme); err != nil {
		return err
	}
	return r.Create(ctx, service)
}

// SetupWithManager sets up the controller with the Manager.
func (r *LpJobReconciler) SetupWithManager(mgr ctrl.Manager) error {
	if err := mgr.GetFieldIndexer().IndexField(context.Background(), &corev1.Pod{}, podOwnerKey, func(obj client.Object) []string {
		pod := obj.(*corev1.Pod)
		owner := metav1.GetControllerOf(pod)
		if owner == nil {
			return nil
		}
		if owner.APIVersion != apiGroupVersion || owner.Kind != "LpJob" {
			return nil
		}

		return []string{owner.Name}
	}); err != nil {
		return err
	}
	if err := mgr.GetFieldIndexer().IndexField(context.Background(), &corev1.Service{}, serviceOwnerKey, func(obj client.Object) []string {
		service := obj.(*corev1.Service)
		owner := metav1.GetControllerOf(service)
		if owner == nil {
			return nil
		}
		if owner.APIVersion != apiGroupVersion || owner.Kind != "LpJob" {
			return nil
		}

		return []string{owner.Name}
	}); err != nil {
		return err
	}

	return ctrl.NewControllerManagedBy(mgr).
		For(&launchpadv1alpha1.LpJob{}).
		Owns(&corev1.Pod{}).
		Owns(&corev1.Service{}).
		Complete(r)
}
