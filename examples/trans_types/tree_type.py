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
  def __init__(self,host,client):
    self.host = host
    self.client = client

  def run(self):
    while True:
      try:
        self.client.send_info({self.host:1})
        time.sleep(5)
      except:
        break
    lp_ssh.stop()

class MiddelConsumer:
  def __init__(self,host,middle_clients,root_client):
    self.host = host
    self.leaf_clients = middle_clients
    self.root_client = root_client

  def run(self):
    while True:
      try:
        for middle_client in self.middle_clients:
          rec_info = middle_client.get_info()
          print('{} receives {}'.format(self.host,rec_info))
          self.root_client.send_info(rec_info)
      except:
        break
    lp_ssh.stop()

class RootConsumer:
  def __init__(self,host,client):
    self.host = host
    self.client = client

  def run(self):
    while True:
      try:
        rec_info = self.client.get_info()
        print('Root consumer receives {}'.format(rec_info))
      except:
        break
    lp_ssh.stop()


def make_tree_type():
  program = lp_ssh.Program('tree_type')
  root_host = 'host1'
  root_server = lp_ssh.TransmitNode().to_host(root_host)
  root_client = program.add_node(root_server, label=root_host)

  root_consumer_node = lp_ssh.SSHNode(RootConsumer, root_host, root_client).to_host(root_host)
  program.add_node(root_consumer_node, label=root_host)


  middel_hosts = ['host2','host3']
  middle_clients = []
  for middle_host in middel_hosts:
    middle_server = lp_ssh.TransmitNode().to_host(middle_host)
    middle_clients.append(program.add_node(middle_server, label=middle_host))

  for middle_host in middel_hosts:
    middle_consumer_node = lp_ssh.SSHNode(MiddelConsumer, middle_host, middle_clients,root_client).to_host(middle_host)
    program.add_node(middle_consumer_node, label=middle_host)

  leaf_hosts = {'host2':['host4','host5'],'host3':['host6','host7']}

  for middle_host_id,middle_host in enumerate(middel_hosts):
    for leaf_host in leaf_hosts[middle_host]:
      ssh_node  = lp_ssh.SSHNode(Worker,leaf_host,middle_clients[middle_host_id]).to_host(leaf_host)
      program.add_node(ssh_node, label=leaf_host)

  lp_ssh.launch(program, terminal='ssh_tmux_session')

def main(_):
  make_tree_type()

if __name__ == '__main__':
  app.run(main)
