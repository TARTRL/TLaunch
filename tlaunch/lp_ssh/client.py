import base64

import logging
import string
from itertools import chain
from typing import Dict, List, Optional

import cloudpickle

from launchpad.nodes.python.node import PyNode
from launchpad.launch.run_locally import run_locally



def create_ssh_job(program,terminal: str = 'gnome-terminal'):
  commands = []
  for label, nodes in program.groups.items():
    # to_executables() is a static method, so we can call it from any of the
    # nodes in this group.
    # pytype: disable=wrong-arg-count
    commands.extend(nodes[0].to_executables(nodes, label,
                                            nodes[0].launch_context))
    # pytype: enable=wrong-arg-count
  return run_locally.run_commands_locally(commands, terminal)




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
