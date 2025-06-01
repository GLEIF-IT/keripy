# -*- encoding: utf-8 -*-
"""
KERI
keri.kli.commands module

"""
import argparse

from hio import help
from hio.base import doing

from keri.app import habbing
from keri.app.cli.common import existing
from keri.core import parsing
from keri.vdr import credentialing, verifying
from keri.vdr import eventing as teventing

logger = help.ogler.getLogger()

parser = argparse.ArgumentParser(description='Import key events in CESR stream format')
parser.set_defaults(handler=lambda args: imprt(args),
                    transferable=True)
parser.add_argument('--name', '-n', help='keystore name and file location of KERI keystore', required=True)
parser.add_argument('--base', '-b', help='additional optional prefix to file location of KERI keystore',
                    required=False, default="")
parser.add_argument('--passcode', '-p', help='21 character encryption passcode for keystore (is not saved)',
                    dest="bran", default=None)  # passcode => bran
parser.add_argument("--file", help="File of streamed CESR events to import", required=True)


def imprt(args):
    """ Command line list credential registries handler

    """

    ed = ImportDoer(name=args.name,
                    base=args.base,
                    bran=args.bran,
                    file=args.file)
    return [ed]


class ImportDoer(doing.DoDoer):

    def __init__(self, name, base, bran, file):
        self.name = name
        self.base = base
        self.file = file

        self.hby = existing.setupHby(name=name, base=base, bran=bran)
        self.rgy = credentialing.Regery(hby=self.hby, name=self.name, base=self.base)
        self.vry = verifying.Verifier(hby=self.hby, reger=self.rgy.reger)
        doers = [doing.doify(self.importDo), habbing.HaberyDoer(self.hby)]

        super(ImportDoer, self).__init__(doers=doers)

    def importDo(self, tymth, tock=0.0, **kwa):
        """ Import credential from file

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value

        Returns:  doifiable Doist compatible generator method

        """
        # enter context
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        with open(self.file, 'rb') as f:
            ims = f.read()
            parsing.Parser(kvy=self.hby.kvy, rvy=self.hby.rvy, tvy=self.rgy.tvy, vry=self.vry).parse(ims=ims)
            self.hby.kvy.processEscrows()
            self.rgy.tvy.processEscrows()

        self.exit()
        return True