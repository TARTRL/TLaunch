#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2021 The TARTRL Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""""""
import os
import logging

import subprocess

import atexit
import psutil

from launchpad.launch.worker_manager import ThreadWorker
from tlaunch.lp_ssh.launch.worker_manager import WorkerManager

class ServerProcess:
  def __init__(self,server,pid):
    self.server = server
    self.pid = pid

  def is_alive(self):
    command = ['ssh',self.server,'python -c "import psutil;psutil.Process({})"'.format(self.pid)]
    try:
      subprocess.check_output(
        command,
        stderr=subprocess.STDOUT)

    except subprocess.CalledProcessError as e:
      logging.info('{}:{} is not alive'.format(self.server,self.pid))
      return False
    else:
      logging.info('{}:{} is alive'.format(self.server, self.pid))
      return True

class SSHWorkerManager(WorkerManager):
  def register_existing_ssh_process(self, name: str, server: str, pid: int):
    self._workers_count[name] += 1
    self._active_workers[name].append(ServerProcess(server,pid))

  def _check_workers(self):
    """Checks status of running workers, terminate runtime in case of errors."""
    has_workers = False
    for label in self._active_workers:
      still_active = []
      for worker in self._active_workers[label]:
        active = True
        if isinstance(worker, ThreadWorker):
          if not worker.thread.is_alive():
            worker.thread.join()
            if not self._stop_counter:
              try:
                worker.future.result()
              except Exception as e:
                if not self._first_failure and not self._stop_counter:
                  self._first_failure = e
            active = False
        elif isinstance(worker, subprocess.Popen):
          try:
            res = worker.wait(0)
            active = False
            if res and not self._first_failure and not self._stop_counter:
              self._first_failure = RuntimeError('One of the workers failed.')
          except subprocess.TimeoutExpired:
            pass
        elif isinstance(worker, ServerProcess):
          if not worker.is_alive():
            active = False
        else:
          try:
            # We can't obtain return code of external process, so clean
            # termination is assumed.
            res = worker.wait(0)
            active = False
          except psutil.TimeoutExpired:
            pass
        if active:
          has_workers = True
          still_active.append(worker)
      self._active_workers[label] = still_active
    if has_workers and self._first_failure and not self._stop_counter:
      self._stop()
    elif not has_workers:
      self._disable_alarm()

def launch_with_ssh_tmux_session(commands_to_launch,
                                 session_name_prefix=None):
  """Launch multiple CommandToLaunch tuples in a new ssh tmux session."""

  session_name_prefix = session_name_prefix or 'ssh_launch'

  return _launch_with_multiplex_ssh_session(commands_to_launch,
                                            session_name_prefix,
                                            'tmux')


def _launch_with_multiplex_ssh_session(commands_to_launch, session_name_prefix, multiplexer):
  """Launch multiple CommandToLaunch tuples in a new multiplex session.

    Args:
      commands_to_launch: An iterable of `CommandToLaunch` namedtuples.
      session_name_prefix: Leading part of the name given to the new tmux session.
        If there is no existing session with this name, it will be used as-is,
        however if another session exists the name will be uniquified by appending
        an incrementing counter.
      multiplexer : tmux or byobu
  """
  # Make a new session with the unmodified name, if this fails add a suffix to
  # the name and retry.
  session_name_host_dict = {}
  ssh_execute = {}
  launch_dir = os.getcwd()

  for command_to_launch in commands_to_launch:
    session_name_host_dict[command_to_launch.host] = session_name_prefix
    ssh_execute[command_to_launch.host] = ['ssh',command_to_launch.host]

  for host in session_name_host_dict:
    suffix_index = 0

    session_name = session_name_host_dict[command_to_launch.host]


    while True:
      try:
        subprocess.check_output(
          ssh_execute[host] + [multiplexer, 'new-session', '-d', '-s', session_name,'-c',launch_dir],
          stderr=subprocess.STDOUT)

      except subprocess.CalledProcessError as e:
        if 'duplicate session' in e.output.decode():
          logging.info('%r session %r already exists, trying to uniquify...',
                       multiplexer, session_name)
          session_name = '{}_{}'.format(session_name_prefix, suffix_index)
          suffix_index += 1
        else:
          raise e  # If `tmux new-session` failed for some other reason.
      else:
        break
    session_name_host_dict[command_to_launch.host] = session_name

  for command_to_launch in commands_to_launch:
    # Apply command-specific overrides to environment variables.
    env_as_list = [
      f'{k}={v}' for k, v in command_to_launch.env_overrides.items()]

    # When the program is done, echo the command so it can be copy-pasted, and
    # then drop into a shell.

    command_str = subprocess.list2cmdline(env_as_list +
                                          command_to_launch.command_as_list)
    inner_command = f'{command_str}; echo "{command_str}"; exec $SHELL; '

    window_name = command_to_launch.title

    command = ssh_execute[command_to_launch.host] + [
      multiplexer,
      'new-window',
      '-t',
      session_name,
      '-n',
      window_name,
      '-c', launch_dir,
      inner_command,
    ]
    # Make the process block until it has completed.
    subprocess.Popen(command)

  print(
    f'Opened new {multiplexer} session called `{session_name}`. '
    f'If you are already in a tmux session, use `Ctrl+B W` as a '
    f'convenient way to switch to the new session. '
    f'Otherwise run \n\n  {multiplexer} a -t "{session_name}"\n\nTo change '
    f'the name of the tmux sessions use the `--tmux_session_name` flag. You '
    f'can terminate all the processes and the {multiplexer} session by '
    f'pressing Ctrl-C here.\n')

  def get_session_processes(host):
    # p = subprocess.run(ssh_execute[host] + [
    #   multiplexer, 'list-panes', '-t', session_name, '-s', '-F',
    #   '"#{pane_pid}"'], stdout=subprocess.PIPE, check=True)
    p = subprocess.run(ssh_execute[host] + [
      multiplexer+' list-panes -t '+session_name+' -s -F "#{pane_pid}"'], stdout=subprocess.PIPE, check=True)

    return [int(pid) for pid in p.stdout.replace(b'"', b'').strip().split()]

  manager = SSHWorkerManager()
  atexit.register(manager.wait)

  for host in ssh_execute:
    for pid in get_session_processes(host):
      manager.register_existing_ssh_process('ssh', host, pid)

  # # kill session
  # kill_command = ssh_execute_str+" tmux kill-session -t "+ session_name
  # kill_command = kill_command.split(' ')
  # try:
  #     subprocess.check_output(kill_command,stderr=subprocess.STDOUT)
  # except subprocess.CalledProcessError as e:
  #     logging.info('kill {} failed!'.format(session_name))
  # else:
  #     logging.info('kill {} success!'.format(session_name))
