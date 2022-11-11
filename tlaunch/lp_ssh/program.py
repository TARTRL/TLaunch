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

"""A Launchpad program."""
import argparse
import contextlib
import itertools

from typing import Any, Dict, List, Optional

from .nodes import base

HandleType = Any

class Program(object):
  """A Launchpad program."""

  def __init__(self, name: str,all_args:argparse.Namespace):
    self._name = name
    self._groups = {}  # type: Dict[str, List[base.Node]]
    # Group to add nodes to. Used by group()
    self._current_group = None  # type: str
    self.all_args = all_args

  def add_node(self,
               node: base.Node,
               label: Optional[str] = None) -> HandleType:
    """Adds node to the program."""

    if self._current_group:
      if label and label != self._current_group:
        raise ValueError('The given label does not match the current group: '
                         f'{label} vs {self._current_group}.')
      label = self._current_group
    else:
      if not label:
        raise ValueError('Label should not be empty.')
    if label not in self._groups:
      self._groups[label] = [node]
    else:
      self._groups[label].append(node)
    return node.create_handle()

  @contextlib.contextmanager
  def group(self, label: str):
    """Creates a group for a collection of homogeneous nodes."""
    if not label:
      raise ValueError('Label should not be empty.')
    if self._current_group:
      raise ValueError('group() cannot be nested.')
    try:
      self._current_group = label
      yield
    finally:
      # Try/finally is to make sure that the current_group is correctly
      # reset even if an exception occurs.
      self._current_group = None


  def get_all_nodes(self) -> List[base.Node]:
    return list(itertools.chain(*self._groups.values()))

  @property
  def name(self) -> str:
    return self._name

  @property
  def groups(self) -> Dict[str, List[base.Node]]:
    return self._groups



def make_program(*nodes: base.Node, name: str = 'launchpad'):
  """A shortcut to create a program from a list of nodes.

  This simplifies the syntax. For example you can do a one-liner launch:

      lp.launch(lp.make_program(lp.PyNode(lambda: ...)))

  Args:
    *nodes: Nodes to run.
    name: An optional name of the program.

  Returns:
    A lp.Program object
  """
  program = Program(name)
  for node in nodes:
    program.add_node(node)
  return program
