from launchpad.address import AbstractAddressBuilder


class KubernetesAddressBuilder(AbstractAddressBuilder):
  """ Creates a `{STATEFUL_SET_NAME}-{POD_ID}.{SERVICE_NAME}` address.

  The process runs in a container, so use a fixed port.
  """
  def __init__(self, lp_job_name: str, group_name: str, id: int) -> None:
    self._address = f'{group_name}-{id}.{lp_job_name}:8001'

  def build(self) -> str:
    return self._address
