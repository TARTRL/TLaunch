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

class Consumer:
  def __init__(self,host,client):
    self.host = host
    self.client = client

  def run(self):
    while True:
      try:
        rec_info = self.client.get_info()
        print('{} receives {}'.format(self.host,rec_info))
      except:
        break
    lp_ssh.stop()


def make_star_type():
  program = lp_ssh.Program('star_type')
  server_host = 'host1'
  server = lp_ssh.TransmitNode().to_host(server_host)
  client = program.add_node(server, label=server_host)
  consumer_node = lp_ssh.SSHNode(Consumer, server_host, client).to_host(server_host)
  program.add_node(consumer_node, label=server_host)

  hosts = ['hots2','host3','host4','host5']
  for host in hosts:
      ssh_node  = lp_ssh.SSHNode(Worker,host,client).to_host(host)
      program.add_node(ssh_node, label=host)

  lp_ssh.launch(program, terminal='ssh_tmux_session')

def main(_):
  make_star_type()

if __name__ == '__main__':
  app.run(main)
