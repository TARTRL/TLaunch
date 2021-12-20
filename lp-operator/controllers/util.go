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
	"fmt"
	launchpadv1alpha1 "lp-operator/api/v1alpha1"
	"strings"

	v1 "k8s.io/api/core/v1"
)

func replicaCount(lpJob *launchpadv1alpha1.LpJob) int32 {
	var count int32
	for _, role := range lpJob.Spec.Roles {
		count += *role.Replicas
	}
	return count
}

func podHostName(roleName string, id int) string {
	return fmt.Sprintf("%s-%d", roleName, id)
}

func podName(jobName string, roleName string, id int) string {
	return fmt.Sprintf("%s-%s-%d", jobName, roleName, id)
}

func getRoleName(podName string) string {
	i := strings.LastIndex(podName, "-")
	return podName[:i]
}

func genGitSyncEnv(git *launchpadv1alpha1.GitSource) []v1.EnvVar {
	envs := []v1.EnvVar{}
	if git.Username != "" {
		envs = append(envs, v1.EnvVar{Name: "GIT_SYNC_USERNAME", Value: git.Username})
	}
	if git.Password != "" {
		envs = append(envs, v1.EnvVar{Name: "GIT_SYNC_PASSWORD", Value: git.Password})
	}
	envs = append(envs, v1.EnvVar{Name: "GIT_SYNC_REPO", Value: git.Url},
		v1.EnvVar{Name: "GIT_SYNC_ONE_TIME", Value: "true"})
	return envs
}

func buildMcCommand(minio *launchpadv1alpha1.MinioSource) []string {
	command := []string{"sh", "-c"}
	mcAlias := fmt.Sprintf("mc alias set minio http://%s/ %s %s", minio.Endpoint, minio.AccessKey, minio.SecretKey)

	i := strings.LastIndex(minio.Path, "/")
	fileName := minio.Path[i+1:]
	mcCp := fmt.Sprintf("mc cp minio/%s/%s ./%s", minio.Bucket, minio.Path, fileName)
	untar := fmt.Sprintf("tar xvf %s", fileName)
	command = append(command, strings.Join([]string{mcAlias, mcCp, untar}, " && "))
	return command
}
