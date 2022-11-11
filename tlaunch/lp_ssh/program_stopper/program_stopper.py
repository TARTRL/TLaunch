# Lint as: python3
# Copyright 2020 DeepMind Technologies Limited. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Stops a Launchpad program."""

import os
import signal
from typing import Union

from absl import logging

from tlaunch.lp_ssh import context
import subprocess

def make_program_stopper(launch_type: Union[str, context.LaunchType]):
  """Returns a callable that stops the Launchpad program.

  Args:
    launch_type: launch_type with which the program stopper is used.

  Returns:
    A callable. When called, it stops the running program.
  """
  launch_type = context.LaunchType(launch_type)

  if launch_type in [
      context.LaunchType.LOCAL_MULTI_PROCESSING,
      context.LaunchType.LOCAL_MULTI_THREADING,
      context.LaunchType.TEST_MULTI_PROCESSING,
      context.LaunchType.TEST_MULTI_THREADING
  ]:
    launcher_process_id = os.getpid()

    def ask_launcher_for_termination(mark_as_completed=False):
      del mark_as_completed
      try:
        os.kill(launcher_process_id, signal.SIGTERM)
      except:
        print('can\'t kill {}'.format(launcher_process_id))

    return ask_launcher_for_termination

  if launch_type == context.LaunchType.SSH_MULTI_PROCESSING:
    def ask_launcher_for_termination(mark_as_completed=False):
      del mark_as_completed
      # kill session
      show_name_commad = "tmux display-message -p '#S'"
      show_name_commad = show_name_commad.split(' ')
      session_name = subprocess.check_output(show_name_commad, stderr=subprocess.STDOUT).decode(
        encoding='utf-8').strip().strip('\'')

      kill_command = "tmux kill-session -t " + session_name
      kill_command = kill_command.split(' ')
      print(kill_command)
      try:
        subprocess.check_output(kill_command, stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as e:
        logging.info('kill {} failed!'.format(session_name))
      else:
        logging.info('kill {} success!'.format(session_name))

    return ask_launcher_for_termination

  raise NotImplementedError(f'{launch_type} is not yet supported.')
