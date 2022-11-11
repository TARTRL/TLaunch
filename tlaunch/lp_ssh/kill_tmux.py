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

import subprocess
def kill_tmux_on_host(host_origin,session_name_prefix,kill_all):
    multiplexer = "tmux"

    if ":" in host_origin:
        host = host_origin.split(":")[0]
        port = host_origin.split(":")[1]
    else:
        host = host_origin
        port  = "22"

    if kill_all:
        try:
            print("kill all sessions on {}:{}".format(host, port))
            if host == "localhost":
                exec_command_list = [multiplexer, 'kill-server']
            else:
                exec_command_list = ['ssh', '-p', port, host] + [multiplexer, 'kill-server']
            subprocess.check_output(exec_command_list)

        except:
            pass
    else:
        try:

            if host == "localhost":

                exec_command_list = [multiplexer, 'ls']

            else:
                exec_command_list = ['ssh', '-p', port, host] + [multiplexer, 'ls']

            output = subprocess.check_output(exec_command_list,
                                    stderr=subprocess.STDOUT)

            session_names = []
            for line in output.decode().split('\n'):

                if ":" in line:
                    session_names.append(line.split(":")[0])
            # print(session_names)

            for name in session_names:
                if name.startswith(session_name_prefix):
                    print("kill {} on {}:{}".format(name, host,port))
                    if host == "localhost":
                        exec_command_list = [multiplexer, 'kill-session', '-t', name]
                    else:
                        exec_command_list = ['ssh', '-p', port, host] + [multiplexer, 'kill-session', '-t', name]
                    print("\t"+" ".join(exec_command_list))
                    subprocess.check_output(exec_command_list)
        except:
            pass

def kill_tmux(host_list, session_name_prefix,kill_all=False):
    for host in host_list:
        kill_tmux_on_host(host,session_name_prefix,kill_all)

