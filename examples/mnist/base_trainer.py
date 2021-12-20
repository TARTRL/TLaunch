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

import argparse
import torchvision
import torchvision.transforms as transforms
import torch
import torch.nn as nn
import torch.distributed as dist
import time

from tlaunch import lp_ssh

import base_runner

class ConvNet(nn.Module):
    def __init__(self, num_classes=10):
      super(ConvNet, self).__init__()
      self.layer1 = nn.Sequential(
        nn.Conv2d(1, 16, kernel_size=5, stride=1, padding=2),
        nn.BatchNorm2d(16),
        nn.ReLU(),
        nn.MaxPool2d(kernel_size=2, stride=2))
      self.layer2 = nn.Sequential(
        nn.Conv2d(16, 32, kernel_size=5, stride=1, padding=2),
        nn.BatchNorm2d(32),
        nn.ReLU(),
        nn.MaxPool2d(kernel_size=2, stride=2))
      self.fc = nn.Linear(7 * 7 * 32, num_classes)

    def forward(self, x):
        out = self.layer1(x)
        out = self.layer2(out)
        out = out.reshape(out.size(0), -1)
        out = self.fc(out)
        return out

class MultiGPUTrainer(base_runner.Runner):
  def __init__(self,argv,host_index):
    super().__init__(argv)
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--nodes', default=1,
                        type=int, metavar='N')
    parser.add_argument('-g', '--gpus', default=1, type=int,
                        help='number of gpus per node')
    parser.add_argument('-g_i', '--gpu_index', default=0, type=int,
                        help='gpu index on current node')
    parser.add_argument('-nr', '--nr', default=0, type=int,
                        help='ranking index of current node')
    parser.add_argument('--epochs', default=10, type=int,
                        metavar='N',
                        help='number of total epochs to run')
    parser.add_argument('--share_file', default='/tmp/your_share_file', type=str,
                        help='shared file for the NCCL communication')
    parser.add_argument('--data', default='./data', type=str,
                        help='mnist data directory')
    args = parser.parse_known_args(argv)[0]
    #########################################################
    args.world_size = args.gpus * args.nodes  #
    args.nr = host_index
    self.args = args
    #########################################################


  def run(self):
    self.train(self.args)
    lp_ssh.stop()

  def train(self, args):
    ############################################################
    rank = args.nr * args.gpus + args.gpu_index

    print('global rank:',rank,'world size:', args.world_size)
    dist.init_process_group(
      backend='nccl',
      init_method=f"file://{args.share_file}",
      world_size=args.world_size,
      rank=rank
    )
    print('Distributed init done!')
    ############################################################

    torch.manual_seed(0)
    model = ConvNet()
    torch.cuda.set_device(args.gpu_index)
    model.cuda(args.gpu_index)
    batch_size = 100
    # define loss function (criterion) and optimizer
    criterion = nn.CrossEntropyLoss().cuda(args.gpu_index)
    optimizer = torch.optim.SGD(model.parameters(), 1e-4)

    ###############################################################
    # Wrap the model
    # import pdb;pdb.set_trace()
    model = nn.parallel.DistributedDataParallel(model,
                                                device_ids=[args.gpu_index])
    ###############################################################

    # Data loading code
    train_dataset = torchvision.datasets.MNIST(
      root=args.data,
      train=True,
      transform=transforms.ToTensor(),
      download=True
    )
    ################################################################
    train_sampler = torch.utils.data.distributed.DistributedSampler(
      train_dataset,
      num_replicas=args.world_size,
      rank=rank
    )

    ################################################################

    train_loader = torch.utils.data.DataLoader(
      dataset=train_dataset,
      batch_size=batch_size,
      ##############################
      shuffle=False,  #
      ##############################
      num_workers=0,
      pin_memory=True,
      #############################
      sampler=train_sampler)  #
    #############################

    start = time.time()
    total_step = len(train_loader)
    for epoch in range(args.epochs):

      train_sampler.set_epoch(epoch)
      for i, (images, labels) in enumerate(train_loader):
        images = images.cuda(non_blocking=True)
        labels = labels.cuda(non_blocking=True)
        # Forward pass
        outputs = model(images)
        loss = criterion(outputs, labels)

        # Backward and optimize
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        if (i + 1) % 100 == 0 and args.gpu_index == 0:
          print('Epoch [{}/{}], Step [{}/{}], Loss: {:.4f}'.format(
            epoch + 1,
            args.epochs,
            i + 1,
            total_step,
            loss.item())
          )
    if args.gpu_index == 0:
      print("Training complete in: {}s".format(time.time() - start))


