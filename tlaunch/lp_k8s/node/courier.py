import launchpad as lp
from launchpad import address as lp_address
from launchpad.nodes.courier import courier_utils

from . import common


class CourierNode(lp.CourierNode):
  """Inherits `CourierNode` from launchpad and remove `worker_manager` from it."""
  def run(self) -> None:
    instance = self._construct_instance()  # pytype:disable=wrong-arg-types
    self._server = courier_utils.make_courier_server(
        instance,
        port=lp_address.get_port_from_address(self._address.resolve()),
        **self._courier_kwargs)
    if hasattr(instance, 'set_courier_server'):
      # Transfer the ownership of the server to the instance, so that the user
      # can decide when to start and stop the courier server.
      instance.set_courier_server(self._server)
      if hasattr(instance, 'run') and self._should_run:
        instance.run()
    else:
      # Start the server after instantiation and serve forever
      self._server.Start()
      if hasattr(instance, 'run') and self._should_run:
        # If a run() method is provided, stop the server at the end of run().
        instance.run()
      else:
        common.wait_for_stop()
      self._server.Stop()
      self._server.Join()
