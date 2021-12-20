from typing import Dict, List, Optional

from kubernetes import client

from tlaunch.lp_k8s.resource import Resource
from tlaunch.lp_k8s.util import map_opt

DEFAULT_PORT = 8001
DEFAULT_NAME = 'launchpad'
REVERB_IMAGE = 'reg.real-ai.cn/launchpad/reverb'
DEFAULT_COMMAND = ['python3', '-u', '-mlaunchpad_kubernetes.process_entry']


class Container:
  def __init__(self,
               image: Optional[str] = None,
               command: Optional[List[str]] = None,
               flags: List[str] = [],
               resources: Optional[Resource] = None,
               env: Optional[Dict[str, str]] = None):
    self.job_name = DEFAULT_NAME
    self.image = image or REVERB_IMAGE
    self.command = command or DEFAULT_COMMAND + flags
    self.resources = resources
    self.env = env

  def build(self) -> client.V1Container:
    return client.V1Container(
        name=self.job_name,
        image=self.image,
        command=self.command,
        ports=[
            client.V1ContainerPort(name='launchpad',
                                   container_port=DEFAULT_PORT)
        ],
        resources=map_opt(
            self.resources,
            lambda x: client.V1ResourceRequirements(limits=x.limits,
                                                    requests=x.requests)),
        env=map_opt(
            self.env,
            lambda e: [client.V1EnvVar(name=k, value=v)
                       for k, v in e.items()]))

  def set_job_name(self, job_name: str) -> 'Container':
    self.job_name = job_name
    return self


class Config:
  def __init__(self, container: Optional[Container] = None, **kwargs):
    self.container = container or Container()
    self.kwargs = kwargs

  def build(self) -> client.V1PodSpec:
    return client.V1PodSpec(**self.kwargs, containers=[self.container.build()])

  def set_job_name(self, job_name: str) -> 'Config':
    self.container.set_job_name(job_name)
    return self


class DefaultReverbConfig(Config):
  def __init__(self) -> None:
    self.container = Container(image=REVERB_IMAGE)
