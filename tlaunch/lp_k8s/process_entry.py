"""
Entry of a PythonNode worker.
This is mostly copied from launchpad, but slimmer.
Note that this is only usable with my implementation of lp-operator.
"""

import builtins
import contextlib
import os
import sys
import platform

from types import ModuleType

import cloudpickle


class DummyModule(ModuleType):
  def __getattr__(self, key):
    return None

  __all__ = []


def tryimport(name, globals={}, locals={}, fromlist=[], level=0):
  try:
    return realimport(name, globals, locals, fromlist, level)
  except ImportError:
    print(f'Possibly missing import "{name}"')
    return DummyModule(name)


realimport, builtins.__import__ = builtins.__import__, tryimport

CONFIG_DIR = '/etc/config'
SOURCE_DIR = '/workdir'


def main():
  # Allow for importing modules from the current directory.
  node_name, _, lp_task_id = platform.node().rpartition('-')
  task_id = int(lp_task_id)

  if os.path.exists(SOURCE_DIR):
    for dirpath in os.listdir(SOURCE_DIR):
      path = os.path.join(SOURCE_DIR, dirpath)
      if os.path.islink(path):
        sys.path.append(path)

  functions = cloudpickle.load(open(os.path.join(CONFIG_DIR, node_name), 'rb'))

  with contextlib.suppress():  # no-op context manager
    functions[task_id]()


if __name__ == '__main__':
  main()
