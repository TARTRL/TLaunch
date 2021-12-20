from threading import Event


def wait_for_stop():
  Event().wait()
