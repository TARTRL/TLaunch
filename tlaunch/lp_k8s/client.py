import base64
from tlaunch.lp_k8s.util import map_opt
import logging
import string
from itertools import chain
from typing import Dict, List, Optional

import cloudpickle
from kubernetes import client, config
from launchpad.nodes.python.node import PyNode

from tlaunch.lp_k8s import addressing
from tlaunch.lp_k8s.config import Config
from tlaunch.lp_k8s.source import Source


def create_lp_job(node_groups: Dict[str, List[PyNode]],
                  job_name: Optional[str] = None,
                  sync_source: Optional[Source] = None,
                  namespace: Optional[str] = None,
                  kube_config: Optional[str] = None,
                  group_config: Optional[Dict[str, Config]] = None):
  job_name = validate_name(job_name)
  namespace = namespace or 'default'
  group_config = group_config or {}

  try:
    config.load_incluster_config()
  except Exception:
    config.load_kube_config(kube_config)

  for label, nodes in node_groups.items():
    for i, node in enumerate(nodes):
      # Run my own address binding strategy here.
      # Try to bind all rpc server to the same port on container with different dns domain.
      addressing.bind_address_kubernetes(node.addresses, job_name, label, i)

  api = client.CustomObjectsApi()
  roles = {
      label: {
          'replicas':
          len(nodes),
          'template':
          client.V1PodTemplateSpec(
              metadata=client.V1ObjectMeta(labels={'app': job_name}),
              spec=group_config.get(label,
                                    Config()).set_job_name(job_name).build(),
          ),
          # REVIEW: sending exec over yaml or volume
          'executable':
          serialize(nodes)
      }
      for label, nodes in node_groups.items()
  }
  lp_job = {
      'apiVersion': 'realai.cn/v1alpha1',
      'kind': 'LpJob',
      'metadata': client.V1ObjectMeta(name=job_name),
      'spec': {
          'roles': roles,
          'source': map_opt(sync_source, lambda s: s.as_dict()) or None
      },
  }

  api.create_namespaced_custom_object(group='realai.cn',
                                      version='v1alpha1',
                                      namespace=namespace,
                                      plural='lpjobs',
                                      body=lp_job)
  logging.info(
      f'An lpjob named "{job_name}" has been created in namespace "{namespace}".'
  )


def serialize(nodes: List[PyNode]):
  data = cloudpickle.dumps([node.function for node in nodes])
  return base64.b64encode(data).decode()


def validate_name(name) -> str:
  if name is not None:
    name = name.lower().replace('_', '-')
    flag, new_name = is_valid_subdomain_filter(name)
    if not flag:
      logging.warn(
          f'"{name}" is not a valid subdomain name. '
          'A lowercase RFC 1123 subdomain must consist of lower case alphanumeric characters, '
          '\'-\' or \'.\', and must start and end with an alphanumeric character.'
      )
      logging.info(f'Stripping name to "{new_name}"')
      assert new_name is not None
      return new_name
    return name
  return name or 'launchpad'


def is_valid_subdomain_filter(domain):
  nums = map(str, range(0, 10))
  alphanumeric = set(chain(nums, string.ascii_lowercase))
  if domain[0] not in alphanumeric or domain[-1] not in alphanumeric:
    return False, None
  alphanumeric.update(['-', '.'])
  flag = all(ch in alphanumeric for ch in domain)
  new_domain = None
  if not flag:
    new_domain = str(filter(lambda ch: ch not in alphanumeric, domain))
  return flag, new_domain
