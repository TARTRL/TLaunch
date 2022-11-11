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

"""Module containing all Launchpad flags."""

# from absl import flags
# from launchpad import context
# FLAGS = flags.FLAGS

from absl import flags
from . import context
FLAGS = flags.FLAGS

try:
    LP_TERMINATION_NOTICE_SECS = flags.DEFINE_integer(
        'lp_termination_notice_secs', 10,
        'Send termination notice to all nodes that many seconds before hard '
        'termination. Set to 0 to trigger hard termination righ away (skip '
        'termination notice), set to negative value to disable hard termination.')
except:
    pass




