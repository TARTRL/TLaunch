# Lint as: python3
# Copyright 2020 DeepMind Technologies Limited. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Entry of a PythonNode worker."""


import contextlib
import json
import os
import sys

import traceback

from absl import app
from absl import flags
from absl import logging
import cloudpickle
from tlaunch.lp_ssh.launch import worker_manager
import six


FLAGS = flags.FLAGS

flags.DEFINE_integer(
    'lp_task_id', None, 'a list index deciding which '
    'worker to run. given a list of workers (obtained from the'
    ' data_file)')
flags.DEFINE_string('data_file', '',
                    'Pickle file location with entry points for all nodes')
flags.DEFINE_string(
    'lp_job_name', '',
    'The name of the job, used to access the correct pickle file resource when '
    'using the new launch API')
flags.DEFINE_string(
    'init_file', '', 'Pickle file location containing initialization module '
    'executed for each node prior to an entry point')
flags.DEFINE_string('flags_to_populate', '{}', '')

_FLAG_TYPE_MAPPING = {
    str: flags.DEFINE_string,
    six.text_type: flags.DEFINE_string,
    float: flags.DEFINE_float,
    int: flags.DEFINE_integer,
    bool: flags.DEFINE_boolean,
    list: flags.DEFINE_list,
}


def _populate_flags():
  """Populate flags that cannot be passed directly to this script."""
  FLAGS(sys.argv, known_only=True)

  flags_to_populate = json.loads(FLAGS.flags_to_populate)
  for name, value in flags_to_populate.items():
    value_type = type(value)
    if value_type in _FLAG_TYPE_MAPPING:
      flag_ctr = _FLAG_TYPE_MAPPING[value_type]
      logging.info('Defining flag %s with default value %s', name, value)
      flag_ctr(
          name,
          value,
          'This flag has been auto-generated.',
          allow_override=True)

  # JAX doesn't use absl flags and so we need to forward absl flags to JAX
  # explicitly. Here's a heuristic to detect JAX flags and forward them.
  for arg in sys.argv:
    if arg.startswith('--jax_'):
      try:
        # pytype:disable=import-error
        import jax
        # pytype:enable=import-error
        jax.config.parse_flags_with_absl()
        break
      except ImportError:
        pass


def _get_task_id():
  """Returns current task's id."""
  if FLAGS.lp_task_id is None:
    # Running under Vertex AI...
    cluster_spec = os.environ.get('CLUSTER_SPEC', None)
    return json.loads(cluster_spec).get('task').get('index')

  return FLAGS.lp_task_id


def main(_):
  # Allow for importing modules from the current directory.
  sys.path.append(os.getcwd())
  data_file = FLAGS.data_file
  init_file = FLAGS.init_file

  if os.environ.get('TF_CONFIG', None):
    # For GCP runtime log to STDOUT so that logs are not reported as errors.
    logging.get_absl_handler().python_handler.stream = sys.stdout

  if init_file:
    init_function = cloudpickle.load(open(init_file, 'rb'))
    init_function()
  f = open(data_file, 'rb')
  functions = cloudpickle.load(f)
  task_id = _get_task_id()

  # Worker manager is used here to handle termination signals and provide
  # preemption support.
  worker_manager.WorkerManager(
      register_in_thread=True)

  with contextlib.suppress():  # no-op context manager
    try:
      functions[task_id]()
  
    except Exception as e:
          traceback.print_exc()
          # 或者得到堆栈字符串信息
          # info = traceback.format_exc()
          # s = sys.exc_info()
          # print("Error '%s' happened on line %d" % (s[1], s[2].tb_lineno))
          answer = input("Some thing is wrong, stop all[yes or no]?:")
          if answer == 'yes':
              pass

import torch

if __name__ == '__main__':
  torch.multiprocessing.set_start_method('spawn')     # 多进程中使用cuda
  _populate_flags()
  app.run(main)
