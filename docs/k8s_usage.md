## Kubernetes Usage
After running the operator in the kubernetes cluster, you should be able to use
`lp_k8s` to deploy some launchpad program. Below is a very simple
example, modified from the `consumer_producer` example on Deepmind launchpad's
[github main page](https://github.com/deepmind/launchpad#implement-example-nodes).

``` python
from absl import app
import logging
import time
import launchpad as lp
import tlaunch.lp_k8s as lp_k8s

class Producer:
  def work(self, context):
    logging.info('I got called, wohoo...')
    time.sleep(30)
    logging.info('I am waking up')
    return context

class Consumer:
  def __init__(self, producers):
    self._producers = producers

  def run(self):
    logging.info('calling workers')
    futures = [producer.futures.work(context)
               for context, producer in enumerate(self._producers)]
    results = [future.result() for future in futures]
    logging.info('Results: %s', results)
    lp_k8s.stop()

def make_program(num_producers):
  program = lp.Program('consumer_producers')
  with program.group('producer'):
    producers = [
        program.add_node(lp.CourierNode(Producer)) for _ in range(num_producers)
    ]
  node = lp.CourierNode(
      Consumer,
      producers=producers)
  program.add_node(node, label='consumer')
  return program

def main(_):
  program = make_program(num_producers=3)
  lp_k8s.launch(program)

if __name__ == '__main__':
  app.run(main)
```

As you can see here, you only need very little modification to your existing
code to launch the program on kubernetes cluster.

`lp_k8s` only provides two functions, that is, `launch` and
`stop`. 

`launch` will create a `LpJob` custom resource on kubernetes, and the
operator will handle the rest, such as creating the pod to run the node
functions and creating the service for communication between pods.

`stop` will send a stop signal to the operator, then the operator would clean
up the `LpJob`.

Basically if you know how to write launchpad program, this is almost exactly the
same.
