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

package v1alpha1

import (
	v1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// EDIT THIS FILE!  THIS IS SCAFFOLDING FOR YOU TO OWN!
// NOTE: json tags are required.  Any new fields you add must have json tags for the fields to be serialized.

// LpJobSpec defines the desired state of LpJob
type LpJobSpec struct {
	// INSERT ADDITIONAL SPEC FIELDS - desired state of cluster
	// Important: Run "make" to regenerate code after modifying this file

	// Whether to enable gang scheduling. Defaults to False.
	EnableGangScheduling bool `json:"enableGangScheduling,omitempty"`

	// Roles are nodes grouped by labels in a launchpad program. It is
	// used for per group configuration.
	Roles map[string]Role `json:"roles,omitempty"`

	// This defines the method of syncing source files.
	Source *SyncSource `json:"source,omitempty"`
}

// Role defines a group in launchpad program.
type Role struct {
	// Replicas is the desired number of replicas of the given template.
	// Defaults to 1.
	Replicas *int32 `json:"replicas,omitempty"`

	// Template is the object that describes the pod that
	// will be created for this replica.
	Template v1.PodTemplateSpec `json:"template,omitempty"`

	// Executable is the binary program sent to each pod for execution.
	Executable []byte `json:"executable,omitempty"`
}

type SyncSource struct {
	Git   *GitSource   `json:"git,omitempty"`
	Minio *MinioSource `json:"minio,omitempty"`
}

type GitSource struct {
	// Git url to sync from.
	Url string `json:"url,omitempty"`

	// Git username.
	// Could be empty if accessing a public repository.
	Username string `json:"username,omitempty"`

	// Git password
	// Could be empty if accessing a public repository.
	// TODO: store this in a secret
	Password string `json:"password,omitempty"`
}

type MinioSource struct {
	Endpoint string `json:"endpoint,omitempty"`

	Bucket string `json:"bucket,omitempty"`

	Path string `json:"path,omitempty"`

	// Minio access key.
	AccessKey string `json:"accessKey,omitempty"`

	// Minio secret key.
	// TODO: use a secret for this.
	SecretKey string `json:"secretKey,omitempty"`
}

// LpJobStatus defines the observed state of LpJob
type LpJobStatus struct {
	StartTime *metav1.Time `json:"startTime,omitempty"`

	CompletionTime *metav1.Time `json:"completionTime,omitempty"`

	LastReconcileTime *metav1.Time `json:"lastReconcileTime,omitempty"`

	RoleStatuses map[string]RoleStatus `json:"roleStatuses"`
}

type RoleStatus struct {
	Running   int32 `json:"running,omitempty"`
	Completed int32 `json:"completed,omitempty"`
	Failed    int32 `json:"failed,omitempty"`
}

//+kubebuilder:object:root=true
//+kubebuilder:subresource:status

// LpJob is the Schema for the lpjobs API
type LpJob struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   LpJobSpec   `json:"spec,omitempty"`
	Status LpJobStatus `json:"status,omitempty"`
}

//+kubebuilder:object:root=true

// LpJobList contains a list of LpJob
type LpJobList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []LpJob `json:"items"`
}

func init() {
	SchemeBuilder.Register(&LpJob{}, &LpJobList{})
}
