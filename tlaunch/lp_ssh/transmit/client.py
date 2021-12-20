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
from typing import Dict

import numpy as np
import torch
import reverb

from dill import dumps, loads

class Client(reverb.Client):
    def insert_weight(self, model_weight, priorities: Dict[str, float]):
        model_values = []
        episode = -1
        for model_key in model_weight:
            if model_key == 'episode':
                episode = model_weight['episode']
                continue

            keys = model_weight[model_key].keys()
            for key in keys:
                model_values.append(model_weight[model_key][key].cpu())

        model_values.append(episode)

        self.insert(data=model_values, priorities=priorities)


    def sample_weight(self,model_keys,target_episode, table: str):
        weight_episode = target_episode - 1
        while weight_episode < target_episode:
            new_values = list(self.sample(table=table, num_samples=1))[0][0].data
            weight_episode = new_values[-1]

        new_model_weight = {}
        for i, key in enumerate(model_keys):
            current_keys = key.split('@')
            model_key, sub_key = current_keys[0], current_keys[1]
            if model_key in new_model_weight:
                new_model_weight[model_key][sub_key] = torch.tensor(new_values[i])
            else:
                new_model_weight[model_key] = {sub_key: torch.tensor(new_values[i])}
        return new_model_weight


    def send_info(self,info):
      data = dumps(info)
      self.insert(data=data, priorities={'info':1})

    def get_info(self):
      feteched_data = np.array(list(self.sample(table='info', num_samples=1))[0][0].data[0], dtype=bytes)
      return loads(feteched_data)
