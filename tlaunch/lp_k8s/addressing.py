from typing import List

import launchpad as lp

from tlaunch.lp_k8s.address import KubernetesAddressBuilder


def bind_address_kubernetes(addresses: List[lp.Address], lp_job_name: str,
                            group_name: str, id: int):
  """Bind addresses for kubernetes launch."""

  for address in addresses:
    address.bind(KubernetesAddressBuilder(lp_job_name, group_name, id))
