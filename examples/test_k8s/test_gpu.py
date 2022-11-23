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
import logging
import subprocess
import xmltodict
from xml.parsers import expat
import launchpad as lp
from tlaunch import lp_k8s
from tlaunch.lp_k8s import Config, Container, Resource
from tlaunch.lp_k8s.util import get_namespace

def install(name):
    subprocess.call(['pip', 'install', name])

def get_gpu_status(gpu):
    gpu_id = gpu['minor_number']
    product_name = gpu['product_name']
    memory_total = int(gpu['fb_memory_usage']['total'].split(' ')[0])
    memory_used = int(gpu['fb_memory_usage']['used'].split(' ')[0])
    memory_free = int(gpu['fb_memory_usage']['free'].split(' ')[0])

    return 'GPU:{}\t{}Mb/{}Mb\t{}'.format(gpu_id, memory_used, memory_total, product_name)

def get_gpus():
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    cmd = 'nvidia-smi -x -q'
    output = subprocess.getoutput(cmd)

    json = xmltodict.parse(output, expat=expat)
    gpus = json['nvidia_smi_log']['gpu']

    gpu_status = []
    if type(gpus) is list:
        for gpu in gpus:
            gpu_status.append(get_gpu_status(gpu))
    elif type(gpus) is dict:
        gpu_status.append(get_gpu_status(gpus))

    return {'localhost': gpu_status}


class GPUTest:
    def __init__(self):
        pass

    def run(self):
        gpu_status = get_gpus()
        for host in gpu_status:
            logging.getLogger().warning('Host {}:'.format(host))
            for g_s in gpu_status[host]:
                logging.getLogger().warning(g_s)

        # lp_k8s.stop()


def make_program():
    program = lp.Program('test_gpu')
    node = lp_k8s.CourierNode(
        GPUTest)
    program.add_node(node, label='tester')
    return program


def main(argv):
    ns = get_namespace()
    program = make_program()
    command = ['bash', '-c' , 'export LIBCUDA_LOG_LEVEL=0; pip install xmltodict; python3 -u -mtlaunch.lp_k8s.process_entry']
    config = Config(namespace=ns,
                    container=Container(namespace=ns,
                                        command=command,
                                        flags=argv,
                                        resources=Resource(nvidia_gpu=2,
                                                           nvidia_gpu_memory=4000,
                                                           nvidia_gpu_cores=100)))

    lp_k8s.launch(program,
                  namespace=ns,
                  group_config={'tester': config})


if __name__ == '__main__':
    from absl import flags

    FLAGS = flags.FLAGS
    FLAGS([""])
    main(sys.argv[1:])
