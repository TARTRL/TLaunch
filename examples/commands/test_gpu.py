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
import subprocess
import xmltodict

def get_gpus():
  cmd = 'nvidia-smi -x -q'
  output = subprocess.getoutput(cmd)

  json = xmltodict.parse(output)
  gpus = json['nvidia_smi_log']['gpu']

  gpu_status = []
  for gpu in gpus:
    gpu_id = gpu['minor_number']
    product_name = gpu['product_name']
    memory_total = int(gpu['fb_memory_usage']['total'].split(' ')[0])
    memory_used = int(gpu['fb_memory_usage']['used'].split(' ')[0])
    memory_free = int(gpu['fb_memory_usage']['free'].split(' ')[0])

    gpu_status.append('GPU:{}\t{}Mb/{}Mb\t{}'.format(gpu_id, memory_used, memory_total, product_name))

  return gpu_status

if __name__ == '__main__':
  get_gpus()
