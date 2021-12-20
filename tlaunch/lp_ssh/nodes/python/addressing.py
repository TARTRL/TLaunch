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

"""Addressing for PyNodes."""

import getpass
import os
import typing
from typing import Any, List, Optional

from absl import flags
from absl import logging
from tlaunch.lp_ssh import address as lp_address


FLAGS = flags.FLAGS

def bind_addresses_local(addresses: List[lp_address.Address]):
  """Binds addresses for the local launch."""

  for address in addresses:
    address.bind(lp_address.AddressBuilder())

def bind_addresses_host(addresses: List[lp_address.Address]):
  """Binds addresses for the local launch."""

  for address in addresses:
    address.bind(lp_address.HostAddressBuilder(address.host))
