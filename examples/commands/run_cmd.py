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
import time

from absl import app

from tlaunch import lp_ssh

from test_gpu import get_gpus

class Command:
  def __init__(self,host,client):
    self.host = host
    self.client = client

  def run(self):
    while True:
      try:
        gpu_status = get_gpus()
        self.client.send_info({self.host:gpu_status})
        for g_s in gpu_status:
          print(g_s)
        time.sleep(5)
      except:
        break
    lp_ssh.stop()

class Displayer:
  def __init__(self,hosts,client):
    self.hosts = hosts
    self.client = client

  def run(self):
    while True:
      gpu_status = self.client.get_info()
      for host in gpu_status:
        print('Host {}:'.format(host))
        for g_s in gpu_status[host]:
          print(g_s)
    lp_ssh.stop()


def make_program():
  program = lp_ssh.Program('ssh_cmd')
  server_host = 'host1'
  server = lp_ssh.TransmitNode().to_host(server_host)
  client = program.add_node(server, label=server_host)
  hosts = ['host2','host3','host4']
  for host in hosts:
      ssh_node  = lp_ssh.SSHNode(Command,host,client).to_host(host)
      program.add_node(ssh_node, label=host+'_cmd')
  dis_node = lp_ssh.SSHNode(Displayer,hosts,client).to_host(server_host)
  program.add_node(dis_node, label=server_host)

  lp_ssh.launch(program, terminal='ssh_tmux_session')


def main(_):
  make_program()

if __name__ == '__main__':
  app.run(main)
