from typing import Any, Mapping, Optional

from tlaunch.lp_ssh import context
from launchpad import program as lp_program
from launchpad.launch.run_locally import run_locally


def launch(program: lp_program.Program,
           local_resources: Optional[Mapping[str, Any]] = None,
           terminal: str = 'gnome-terminal'):
  """Launches a program using multiple processes."""
  # Set up the launch context (launch type & launch config) for all nodes
  local_resources = local_resources or {}
  for label, nodes in program.groups.items():
    launch_config = local_resources.get(label, None)
    for node in nodes:
      node._initialize_context(
        context.LaunchType.LOCAL_MULTI_PROCESSING,
        launch_config=launch_config)

  # Notify the input handles
  for label, nodes in program.groups.items():
    for node in nodes:
      for handle in node._input_handles:
        handle.connect(node, label)

  # Bind addresses
  for node in program.get_all_nodes():
    node.bind_addresses()

  commands = []
  for label, nodes in program.groups.items():
    # to_executables() is a static method, so we can call it from any of the
    # nodes in this group.

    # pytype: disable=wrong-arg-count
    commands.extend(nodes[0].to_executables(nodes, label,
                                            nodes[0]._launch_context))

    # pytype: enable=wrong-arg-count
  return run_locally.run_commands_locally(commands, terminal)
