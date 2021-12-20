import os
import sys
import logging

from typing import Any, Dict, Optional, Sequence, Union, cast,Text
from absl import flags

from launchpad import program as lp_program
from launchpad.launch.run_locally.run_locally import _LOCAL_LAUNCHER_MAP, SEPARATE_TERMINAL_MODES, TERMINALS_FOR_X
from launchpad.launch.run_locally.run_locally import SEPARATE_TERMINAL_XTERM,SEPARATE_TERMINAL_GNOME_TERMINAL_WINDOWS
from launchpad.launch.run_locally.run_locally import SEPARATE_TERMINAL_TMUX_SESSION,SEPARATE_TERMINAL_CURRENT_TERMINAL

from launchpad.launch.run_locally import feature_testing

from tlaunch.lp_ssh import context
from .run_ssh.launch_ssh_tmux import launch_with_ssh_tmux_session

FLAGS = flags.FLAGS

SEPARATE_SSH_TERMINAL_TMUX_SESSION = 'ssh_tmux_session'
_LOCAL_LAUNCHER_MAP.update({SEPARATE_SSH_TERMINAL_TMUX_SESSION:launch_with_ssh_tmux_session})
SEPARATE_TERMINAL_MODES = SEPARATE_TERMINAL_MODES+(SEPARATE_SSH_TERMINAL_TMUX_SESSION,)

def _get_terminal(given_terminal: Optional[Text]):
  """Returns the terminal for local launch based on X & command availability.

  By order of priority it will:
  - use the provided `given_terminal`
  - default to the shell environment variable `LAUNCHPAD_LAUNCH_LOCAL_TERMINAL`
    if set
  - or select the first supported option in: Gnome, Tmux, Xterm and current
    terminal.

  Args:
    given_terminal: The terminal identifier to use or `None`.

  Returns:
    One of the legal terminal modes (a string in SEPARATE_TERMINAL_MODES) based
    on the priority described above.
  """

  if (given_terminal is not None and
      given_terminal not in SEPARATE_TERMINAL_MODES):
    raise ValueError('`terminal` got a mode that it does not '
                     'understand %r. Please choose from %r.' %
                     (given_terminal, SEPARATE_TERMINAL_MODES))
  terminal = given_terminal or os.environ.get('LAUNCHPAD_LAUNCH_LOCAL_TERMINAL',
                                              None)
  # Set terminal to None, if the chosen terminal cannot be used because we are
  # running without X.
  if not feature_testing.has_x() and terminal in TERMINALS_FOR_X:
    logging.info('Not using %s to launch, since DISPLAY is not set.', terminal)
    terminal = None

  if terminal is None:
    if feature_testing.has_gnome_terminal():
      terminal = SEPARATE_TERMINAL_GNOME_TERMINAL_WINDOWS
    elif feature_testing.has_tmux():
      terminal = SEPARATE_TERMINAL_TMUX_SESSION
    elif feature_testing.has_xterm():
      terminal = SEPARATE_TERMINAL_XTERM

    # Examine the type of terminal and explain why it is chosen.
    if terminal is None:
      logging.info('Launching in the same console since we cannot find '
                   'gnome-terminal, tmux, or xterm.')
      terminal = SEPARATE_TERMINAL_CURRENT_TERMINAL
    else:
      logging.info(
          'Launching with %s because the `terminal` launch option '
          'is not explicitly specified. To remember your preference '
          '(assuming tmux_session is the preferred option), either: \n'
          '1. Pass the `terminal` launch option (e.g., '
          '`lp.launch(program, terminal="tmux_session")`).\n'
          '2. Set the following in your bashrc to remember your '
          'preference:\n'
          '    export LAUNCHPAD_LAUNCH_LOCAL_TERMINAL=tmux_session', terminal)

  return terminal

def launch(
    programs: Union[lp_program.Program, Sequence[lp_program.Program],],
    local_resources: Optional[Dict[str, Any]] = None,
    terminal: str = 'gnome-terminal'
) -> Any:

  if not FLAGS.is_parsed():
    FLAGS(sys.argv, known_only=True)


  if not isinstance(programs, Sequence):
    programs = cast(Sequence[lp_program.Program], [programs])

  program = programs[0]

  # return launch_local_multiprocessed.launch(program, local_resources, terminal)

  local_resources = local_resources or {}
  for label, nodes in program.groups.items():

    launch_config = local_resources.get(label, None)

    for node in nodes:
      if terminal in ['tmux_session','current_terminal']:
        node._initialize_context(
          context.LaunchType.LOCAL_MULTI_PROCESSING,
          launch_config=launch_config)
      if terminal == 'ssh_tmux_session':
        node._initialize_context(
          context.LaunchType.SSH_MULTI_PROCESSING,
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

  for command in commands:
    if not os.access(command.command_as_list[0], os.X_OK):
      raise ValueError("Unable to execute '%s'" % command.command_as_list[0])
  return _LOCAL_LAUNCHER_MAP[_get_terminal(terminal)](commands)



