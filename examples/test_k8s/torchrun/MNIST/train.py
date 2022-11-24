from __future__ import print_function
import argparse
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
from torch.optim.lr_scheduler import StepLR
import torch.distributed as dist


def init_distributed_mode(args):
    if 'LOCAL_RANK' not in os.environ:
        args.distributed = False
        return
    dist_backend = getattr(args, 'dist_backend', 'nccl')
    dist_url = getattr(args, 'dist_url', 'env://')
    args.local_rank = int(os.environ['LOCAL_RANK'])
    args.distributed = True
    dist.init_process_group(backend=dist_backend,
                            init_method=dist_url)
    args.world_size = dist.get_world_size()
    args.rank = dist.get_rank()
    print(f"| distributed init (rank {args.rank}): url: {dist_url}, local rank: {args.local_rank}, world size:{args.world_size}", flush=True)

    if torch.cuda.is_available():
        if args.distributed:
            device = 'cuda:%d' % args.local_rank
        else:
            device = 'cuda:0'
    else:
        device = 'cpu'
    args.device = torch.device(device)
    torch.cuda.set_device(args.device)
    


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.dropout1 = nn.Dropout(0.25)
        self.dropout2 = nn.Dropout(0.5)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = F.relu(x)
        x = F.max_pool2d(x, 2)
        x = self.dropout1(x)
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout2(x)
        x = self.fc2(x)
        output = F.log_softmax(x, dim=1)
        return output


def train(args, model, device, train_loader, optimizer, epoch):
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(data)
        loss = F.nll_loss(output, target)
        loss.backward()
        optimizer.step()
        if dist.get_rank() == 0:
            if batch_idx % args.log_interval == 0:
                print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                    epoch, dist.get_world_size() * batch_idx * len(data), len(train_loader.dataset),
                    100. * batch_idx / len(train_loader), loss.item()))
                if args.dry_run:
                    break
        else:
           if batch_idx % args.log_interval == 0:
                print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                    epoch, batch_idx * len(data), len(train_loader.dataset),
                    100. * batch_idx / len(train_loader), loss.item()))
                if args.dry_run:
                    break 


def test(model, device, test_loader):
    model.eval()
    test_loss = 0
    correct = 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += F.nll_loss(output, target, reduction='sum').item()  # sum up batch loss
            pred = output.argmax(dim=1, keepdim=True)  # get the index of the max log-probability
            correct += pred.eq(target.view_as(pred)).sum().item()

    test_loss /= len(test_loader.dataset)

    print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
        test_loss, correct, len(test_loader.dataset),
        100. * correct / len(test_loader.dataset)))


def main():
    # Training settings
    parser = argparse.ArgumentParser(description='PyTorch MNIST Example')
    parser.add_argument('--batch-size', type=int, default=64, metavar='N',
                        help='input batch size for training (default: 64)')
    parser.add_argument('--test-batch-size', type=int, default=1000, metavar='N',
                        help='input batch size for testing (default: 1000)')
    parser.add_argument('--epochs', type=int, default=14, metavar='N',
                        help='number of epochs to train (default: 14)')
    parser.add_argument('--lr', type=float, default=1.0, metavar='LR',
                        help='learning rate (default: 1.0)')
    parser.add_argument('--gamma', type=float, default=0.7, metavar='M',
                        help='Learning rate step gamma (default: 0.7)')
    parser.add_argument('--no-cuda', action='store_true', default=False,
                        help='disables CUDA training')
    parser.add_argument('--no-mps', action='store_true', default=False,
                        help='disables macOS GPU training')
    parser.add_argument('--dry-run', action='store_true', default=False,
                        help='quickly check a single pass')
    parser.add_argument('--seed', type=int, default=1, metavar='S',
                        help='random seed (default: 1)')
    parser.add_argument('--log-interval', type=int, default=10, metavar='N',
                        help='how many batches to wait before logging training status')
    parser.add_argument('--save-model', action='store_true', default=False,
                        help='For Saving the current Model')
    parser.add_argument("--save_path", type=str, default="",
                        help="path used to save model")
    args = parser.parse_args()
    use_cuda = not args.no_cuda and torch.cuda.is_available()
    use_mps = not args.no_mps and torch.backends.mps.is_available()

    init_distributed_mode(args)

    torch.manual_seed(args.seed)

    if use_cuda:
        device = torch.device("cuda")
    elif use_mps:
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    train_kwargs = {'batch_size': args.batch_size}
    test_kwargs = {'batch_size': args.test_batch_size}
    if use_cuda:
        cuda_kwargs = {'num_workers': 1,
                       'pin_memory': True}
        train_kwargs.update(cuda_kwargs)
        test_kwargs.update(cuda_kwargs)

    transform=transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
        ])
    dataset1 = datasets.MNIST('/TData/data', train=True, download=True,
                       transform=transform)
    dataset2 = datasets.MNIST('/TData/data', train=False,
                       transform=transform)

    if args.distributed:
        train_sampler = torch.utils.data.distributed.DistributedSampler(dataset1, shuffle=True)
    else:
        train_sampler = torch.utils.data.RandomSampler(dataset1)
    test_sampler = torch.utils.data.SequentialSampler(dataset2)

    train_loader = torch.utils.data.DataLoader(dataset1, sampler = train_sampler, **train_kwargs)
    test_loader = torch.utils.data.DataLoader(dataset2, sampler = test_sampler, **test_kwargs)

    model = Net().to(device)
    model_without_ddp = model
    if args.distributed:
        model = torch.nn.parallel.DistributedDataParallel(model, device_ids=[args.device])
        model_without_ddp = model.module

    optimizer = optim.Adadelta(model.parameters(), lr=args.lr)

    scheduler = StepLR(optimizer, step_size=1, gamma=args.gamma)
    for epoch in range(1, args.epochs + 1):
        if args.distributed:
            train_sampler.set_epoch(epoch)
        train(args, model, device, train_loader, optimizer, epoch)
        if args.distributed:
            if dist.get_rank() == 0:
                test(model_without_ddp, device, test_loader)
        else:
            test(model, device, test_loader)
        scheduler.step()

    if args.save_model:
        if args.distributed:
            if dist.get_rank() == 0:
                # only save model on RANK0 process.
                print(f'Save the model to {os.path.join(args.save_path, "mnist_cnn.pt")}')
                torch.save(model.state_dict(), os.path.join(args.save_path, "mnist_cnn.pt"))
        else:
            print(f'Save the model to {os.path.join(args.save_path, "mnist_cnn.pt")}')
            torch.save(model.state_dict(), os.path.join(args.save_path, "mnist_cnn.pt"))


if __name__ == '__main__':
    main()
