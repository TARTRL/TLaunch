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

from absl import app
import logging
import time

import launchpad as lp

from tlaunch import lp_k8s

class Worker:
  def work(self, context):
    logging.info('I got called, wohoo...')
    time.sleep(30)
    logging.info('I am waking up')
    return context

class Consumer:
  def __init__(self, producers):
    self._producers = producers

  def run(self):
    logging.info('calling workers')
    futures = [producer.futures.work(context)
               for context, producer in enumerate(self._producers)]
    results = [future.result() for future in futures]
    logging.info('Results: %s', results)
    lp_k8s.stop()

def make_program(num_producers):
  program = lp.Program('consumer_producers')
  with program.group('producer'):
    producers = [
        program.add_node(lp.CourierNode(Worker)) for _ in range(num_producers)
    ]
  node = lp.CourierNode(
      Consumer,
      producers=producers)
  program.add_node(node, label='consumer')
  return program

def main(_):
  program = make_program(num_producers=3)
  lp_k8s.launch(program)

if __name__ == '__main__':
  app.run(main)
