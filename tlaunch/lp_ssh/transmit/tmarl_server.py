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
import reverb

class Server:
    def __init__(self,all_args):
        self.all_args = all_args
        self.server = self.launch_server(self.all_args)

    def launch_server(self, all_args):
        running_programs = ["server", "server_learner", "whole"]
        if not all_args.program_type in running_programs:
            return None
        # launch server
        port = int(all_args.server_address.split(':')[1])
        print('Launch server at port:{}'.format(port))
        if all_args.distributed_type == "sync":
            # data_rate_limiter = reverb.rate_limiters.Queue(all_args.actor_num)
            # weight_rate_limiter = reverb.rate_limiters.MinSize(1)
            # weight_max_times_sampled = all_args.actor_num
            # data_max_size = all_args.actor_num

            tables = [reverb.Table(
                name='sync_signal',
                sampler=reverb.selectors.Uniform(),
                remover=reverb.selectors.Fifo(),
                max_size=all_args.actor_num,
                rate_limiter=reverb.rate_limiters.Queue(all_args.actor_num),
                max_times_sampled=1),
                reverb.Table(
                    name='id',
                    sampler=reverb.selectors.Uniform(),
                    remover=reverb.selectors.Fifo(),
                    max_size=all_args.actor_num,
                    rate_limiter=reverb.rate_limiters.Queue(all_args.actor_num),
                    max_times_sampled=1)]

            for i in range(all_args.actor_num):
                tables.append(reverb.Table(  # Replay buffer storing weight.
                    name='weight_{}'.format(i),
                    sampler=reverb.selectors.Uniform(),
                    remover=reverb.selectors.Fifo(),
                    max_size=1,
                    rate_limiter=reverb.rate_limiters.Queue(1)))
                tables.append(reverb.Table(  # Replay buffer storing experience.
                    name='replay_buffer_{}'.format(i),
                    sampler=reverb.selectors.Uniform(),
                    remover=reverb.selectors.Fifo(),
                    max_size=1,
                    rate_limiter=reverb.rate_limiters.Queue(1)))
        else:
            # async type is reminded for future
            raise NotImplemented

        server = reverb.Server(
            tables=tables,
            port=port
        )
        if all_args.program_type == "server":
            server.wait()
            exit()
        else:
            return server

    def stop(self):
        if self.server:
            self.server.stop()
