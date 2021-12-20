from typing import Callable, Iterable, Iterator, Optional, TypeVar

T = TypeVar('T')
U = TypeVar('U')


def map_opt(opt: Optional[T], fn: Callable[[T], U]) -> Optional[U]:
  return None if opt is None else fn(opt)
