#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2022 The TARTRL Authors.
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

from typing import Any, Callable, Optional, Sequence

from absl import logging

import portpicker

import reverb

from tlaunch.lp_ssh import address as lp_address

from tlaunch.lp_ssh.launch import worker_manager

# from tlaunch.lp_ssh import context
# from tlaunch.lp_ssh.nodes.python import node as python
from tlaunch.lp_ssh.nodes import ssh_node
from tmarl.transmit.rl_tables import rl_tables


# from tmarl import transmit
from tmarl.transmit import client
from tmarl.transmit import launch_server
from tlaunch.lp_ssh.nodes import base
from tlaunch.lp_ssh.address import get_port_from_address

PriorityTablesFactory = Callable[[], Sequence[reverb.Table]]
CheckpointerFactory = Callable[[], reverb.checkpointers.CheckpointerBase]

TRANSMIT_PORT_NAME = 'transmit'
import subprocess


class TransmitHandle(base.Handle):
    """Handle of the TransmitNode.

    When dereferenced a transmit-Client is returned. This client should primarily be used for insert operations on the
    actors.
    """

    def __init__(self, address: lp_address.Address):
        self._address = address

    def dereference(self):
        address = self._address.resolve()
        if isinstance(address,str):
            host = address.split(':')[0]
            client_port = address.split(':')[1]
        else:
            host = address.split(':')[0]
            host_port = address['port']
            client_port = get_port_from_address(address)
        print("data server address:",address)

        # 反向代理，但是程序结束后不会自动断开，需要实现自动断开的功能
        reverse_proxy = False
        if host == '127.0.0.1' or host == 'localhost':
            reverse_proxy=False

        if reverse_proxy:

            try:
                local_port = portpicker.pick_unused_port()
                server_address = 'localhost:{}'.format(local_port)
                exe_list = ['ssh','-p', host_port, '-NL', '{}:localhost:{}'.format(local_port, client_port), host, '&']

                subprocess.Popen(exe_list)
                print("Use reverse proxy:{}".format(" ".join(exe_list)))

            except subprocess.CalledProcessError as e:
                print(e.output.decode())
                raise e  # If `tmux new-session` failed for some other reason.

            logging.info('Transmit client connecting to: %s', address)
            logging.info('Transmit client using local address: {}'.format(server_address))
        else:
            server_address = '{}:{}'.format(host,client_port)
            logging.info('Transmit client connecting to server: %s', server_address)

        return client.Client(server_address)


class TransmitNode(ssh_node.SSHNode):
    """Represents a Transmit Server in a Launchpad program."""

    def __init__(self,
                 priority_tables_fn: Optional[PriorityTablesFactory] = lambda: [],
                 checkpoint_ctor: Optional[CheckpointerFactory] = None):
        super().__init__(self.run)
        self._priority_tables_fn = priority_tables_fn
        self._checkpoint_ctor = checkpoint_ctor
        self._address = lp_address.HostAddress(TRANSMIT_PORT_NAME)

        self.allocate_address(self._address)

    def to_host(self, host):
        super(TransmitNode, self).to_host(host)
        self._address.to_host(host)
        return self

    def create_handle(self):
        return self._track_handle(TransmitHandle(self._address))

    def run(self):
        priority_tables = self._priority_tables_fn()


        priority_tables.append(reverb.Table(name='info',
                                            sampler=reverb.selectors.Lifo(),
                                            remover=reverb.selectors.Fifo(),
                                            max_size=1,
                                            rate_limiter=reverb.rate_limiters.MinSize(1)
                                            ))

        if self._checkpoint_ctor is None:
            checkpointer = None
        else:
            checkpointer = self._checkpoint_ctor()

        self._server = launch_server.LaunchServer(
            tables=priority_tables,
            port=lp_address.get_port_from_address(self._address.resolve()),
            checkpointer=checkpointer)
        worker_manager.wait_for_stop()

    @property
    def reverb_address(self) -> lp_address.Address:
        return self._address


class RLTransmitNode(TransmitNode):
    def __init__(self, argv,actor_num,
                 checkpoint_ctor: Optional[CheckpointerFactory] = None):
        self.actor_num = actor_num
        self.argv = argv
        super().__init__(self.rl_tables, checkpoint_ctor)

    def rl_tables(self):
        from tmarl.configs.config import get_config
        parser = get_config()
        all_args = parser.parse_known_args(self.argv)[0]
        all_args.actor_num = self.actor_num
        return rl_tables(all_args=all_args)

