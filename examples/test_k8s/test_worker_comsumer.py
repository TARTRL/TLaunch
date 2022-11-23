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

import sys
from absl import app
import logging
import time

import launchpad as lp
from tlaunch import lp_k8s
from tlaunch.lp_k8s.util import get_namespace


class Worker:
    def work(self, context):
        log = logging.getLogger()
        log.setLevel(logging.DEBUG)
        log.info('I got called, wohoo...')
        time.sleep(5)
        log.info('I am waking up')
        return context


class Consumer:
    def __init__(self, producers):
        self._producers = producers

    def run(self):
        log = logging.getLogger()
        log.setLevel(logging.DEBUG)
        log.info('calling workers')
        futures = [producer.futures.work(context)
                   for context, producer in enumerate(self._producers)]
        results = [future.result() for future in futures]
        log.info('Results: %s', results)
        # lp_k8s.stop()


def make_program(num_producers):
    program = lp.Program('consumer_producers')
    with program.group('producer'):
        producers = [
            program.add_node(lp_k8s.CourierNode(Worker)) for _ in range(num_producers)
        ]
    node = lp_k8s.CourierNode(
        Consumer,
        producers=producers)
    program.add_node(node, label='consumer')
    return program


def main(_):
    ns = get_namespace()
    program = make_program(num_producers=1)
    lp_k8s.launch(program, namespace=ns)


if __name__ == '__main__':
    app.run(main)
