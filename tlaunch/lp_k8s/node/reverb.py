import launchpad as lp
import reverb

from . import common


class ReverbNode(lp.ReverbNode):
  """Inherits `ReverbNode` from launchpad and remove `worker_manager` from it."""
  def run(self):
    priority_tables = self._priority_tables_fn()
    if self._checkpoint_ctor is None:
      checkpointer = None
    else:
      checkpointer = self._checkpoint_ctor()

    self._server = reverb.Server(tables=priority_tables,
                                 port=lp.get_port_from_address(
                                     self._address.resolve()),
                                 checkpointer=checkpointer)
    common.wait_for_stop()
