import sys

from tlaunch import lp_ssh

from base_trainer import MultiGPUTrainer

def main(argv):
  program = lp_ssh.Program('mnist_distributed')
  for host_index, host in enumerate(['host1','host2','host3','host4']):
    ssh_node = lp_ssh.SSHNode(MultiGPUTrainer, argv, host_index).to_host(host)
    program.add_node(ssh_node, label=host + '_MultiGPUTrainer')
  lp_ssh.launch(program, terminal='ssh_tmux_session')

if __name__ == '__main__':
  from absl import flags
  FLAGS = flags.FLAGS
  FLAGS([""])
  main(sys.argv[1:])


