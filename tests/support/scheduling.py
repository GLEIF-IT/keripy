"""Context managers for manually driven test schedulers."""

from contextlib import contextmanager

from hio.base import doing


@contextmanager
def openDoist(*, doers, tock, limit):
    """Enter a manually driven Doist and guarantee scheduler cleanup."""
    doist = doing.Doist(doers=doers, tock=tock, limit=limit)
    try:
        doist.enter()
        yield doist
    finally:
        doist.exit()
