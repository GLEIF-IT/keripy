# -*- encoding: utf-8 -*-
"""
keri.app.cli.commands module

"""
import argparse

from hio.base import doing

from keri.core import signing

parser = argparse.ArgumentParser(description='Request a credential from another party by initiating an IPEX exchange')
parser.set_defaults(handler=lambda args: handler(args))


def handler(_):
    return [doing.doify(nonce)]


def nonce(tymth, tock=0.0, **kwa):
    """ nonce
    """
    _ = (yield tock)

    print(signing.Salter().qb64)
