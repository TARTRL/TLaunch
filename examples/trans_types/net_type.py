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

class Worker:
  def __init__(self,host,clients):
    self.host = host
    self.clients = clients

  def run(self):
    while True:
      try:
        for client in self.clients:
          client.send_info({self.host:1})
        time.sleep(5)
      except:
        break
    lp_ssh.stop()


class Consumer:
  def __init__(self,host,clients):
    self.host = host
    self.clients = clients

  def run(self):
    while True:
      try:
        for client in self.clients:
          rec_info = client.get_info()
          print('{} receives {}'.format(self.host,rec_info))
      except:
        break
    lp_ssh.stop()


def make_net_type():
  program = lp_ssh.Program('net_type')
  hosts = ['host1', 'host2', 'host3', 'host4', 'host5']
  clients = []

  for host in hosts:
    server = lp_ssh.TransmitNode().to_host(host)
    clients.append(program.add_node(server, label=host))

  for host in hosts:
    consumer_node = lp_ssh.SSHNode(Consumer, host, clients).to_host(host)
    program.add_node(consumer_node, label=host)

    ssh_node = lp_ssh.SSHNode(Worker, host, clients).to_host(host)
    program.add_node(ssh_node, label=host)

  lp_ssh.launch(program, terminal='ssh_tmux_session')

def main(_):
  make_net_type()

if __name__ == '__main__':
  app.run(main)
