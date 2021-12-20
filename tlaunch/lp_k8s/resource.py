from typing import NamedTuple, Optional, Tuple, Union


class ResourceRange(NamedTuple):
  requests: Optional[str]
  limits: Optional[str]


R = Union[ResourceRange, Tuple[str, Optional[str]], str, None]


class Resource:
  def __init__(self,
               cpu: R = None,
               memory: R = None,
               nvidia_gpu: R = None) -> None:
    self.resources = {
        'cpu': cpu,
        'memory': memory,
        'nvidia.com/gpu': nvidia_gpu
    }
    self.requests = {
        k: v if isinstance(v, str) else v[0]
        for k, v in self.resources.items() if v is not None
    }
    self.limits = {
        k: v[1]
        for k, v in self.resources.items()
        if not isinstance(v, str) and v is not None and v[1] is not None
    }
