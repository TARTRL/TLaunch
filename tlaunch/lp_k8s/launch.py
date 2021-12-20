from typing import Any, Dict, List, Optional, Sequence, Union, cast

import launchpad as lp
from launchpad.nodes.python.node import PyNode

from tlaunch.lp_k8s import client
from tlaunch.lp_k8s.config import Config
from tlaunch.lp_k8s.source import Source


def launch(programs: Union[lp.Program, Sequence[lp.Program]],
           source: Optional[Source] = None,
           namespace: Optional[str] = None,
           kube_config: Optional[str] = None,
           group_config: Optional[Dict[str, Config]] = None) -> Any:
  # Pretend to be launching with local multiprocess here.
  launch_type = lp.LaunchType.LOCAL_MULTI_PROCESSING

  if not isinstance(programs, Sequence):
    programs = cast(Sequence[lp.Program], [programs])

  # NOTE: original launchpad is launching only one single program here
  program = programs[0]

  launch_kubernetes(program, launch_type, source, namespace, kube_config,
                    group_config)


def launch_kubernetes(
    program: lp.Program,
    launch_type: lp.LaunchType = lp.LaunchType.LOCAL_MULTI_PROCESSING,
    source: Optional[Source] = None,
    namespace: Optional[str] = None,
    kube_config: Optional[str] = None,
    group_config: Optional[Dict[str, Config]] = None):
  for label, nodes in program.groups.items():
    for node in nodes:
      node._initialize_context(launch_type, launch_config=None)

  for label, nodes in program.groups.items():
    for node in nodes:
      for handle in node._input_handles:
        handle.connect(node, label)

  groups = cast(Dict[str, List[PyNode]], program.groups)

  client.create_lp_job(groups, program.name, source, namespace, kube_config,
                       group_config)
