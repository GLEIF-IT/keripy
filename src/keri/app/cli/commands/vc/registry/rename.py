import argparse

from keri import help
from hio.base import doing

from keri.app import indirecting, habbing, grouping
from keri.app.cli.common import existing
from keri.core import serdering
from keri.db.dbing import dgKey
from keri.kering import LikelyDuplicitousError
from keri.vdr import credentialing, viring

logger = help.ogler.getLogger()

parser = argparse.ArgumentParser(description='Rename an existing credential registry')
parser.set_defaults(handler=lambda args: registryRename(args),
                    transferable=True)
parser.add_argument('--name', '-n', help='Human readable reference', required=True)
parser.add_argument('--registry-name', '-r', help='Human readable name for registry, defaults to name of Habitat',
                    default=None, required=True)
parser.add_argument('--registry-said', '-rs', help='SAID of registry to rename',
                    default=None, required=True)
parser.add_argument('--base', '-b', help='additional optional prefix to file location of KERI keystore',
                    required=False, default="")
parser.add_argument('--passcode', '-p', help='21 character encryption passcode for keystore (is not saved)',
                    dest="bran", default=None)  # passcode => bran
parser.add_argument("--verbose", "-V", help="print JSON of all current events", action="store_true")


def registryRename(args):
    name = args.name
    bran = args.bran
    base = args.base
    verbose = args.verbose
    registryName = args.registry_name
    registrySaid = args.registry_said

    renameDoer = RegistryRenamer(name=name, base=base, bran=bran, registryName=registryName, registrySaid=registrySaid, verbose=verbose)

    doers = [renameDoer]
    return doers


class RegistryRenamer(doing.DoDoer):
    """
        Renamer Doer for credential registry
    """

    def __init__(self, name, base, bran, registryName, registrySaid, verbose):
        """


        """
        self.name = name
        self.registryName = registryName
        self.registrySAID = registrySaid
        self.verbose = verbose

        self.hby = existing.setupHby(name=name, base=base, bran=bran)
        self.hab = self.hby.habByName(name)
        self.rgy = credentialing.Regery(hby=self.hby, name=name, base=base)
        self.hbyDoer = habbing.HaberyDoer(habery=self.hby)  # setup doer
        counselor = grouping.Counselor(hby=self.hby)

        mbx = indirecting.MailboxDirector(hby=self.hby, topics=["/receipt", "/multisig", "/replay"])
        doers = [self.hbyDoer, counselor, mbx]
        self.toRemove = list(doers)

        doers.extend([doing.doify(self.renameDo)])
        super(RegistryRenamer, self).__init__(doers=doers)

    def renameDo(self, tymth, tock=0.0):
        """ Process incoming messages to incept a credential registry

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

        if self.rgy is None:
            print("No regery")
            return

        registry = self.rgy.registryByName(self.registrySAID)
        if registry is None:
            if self.registrySAID in self.rgy.regs:
                registry = self.rgy.regs[self.registrySAID]
                regk = registry.regk
            else:
                raw = self.rgy.reger.getTvt(key=dgKey(self.registrySAID, self.registrySAID))
                if raw is None:
                    print(f"{self.registrySAID} is not a valid reference to a credential registry")
                    return

                regser = serdering.SerderKERI(raw=bytes(raw))
                try:
                    registry = self.rgy.makeRegistry(name=self.registrySAID, prefix=self.hab.pre, vcp=regser)
                except LikelyDuplicitousError as e:
                    print(f"Ignoring error: {e} for registry {self.registrySAID} {registry}")
                regk = self.registrySAID
        else:
            regk = self.registrySAID

        regord = viring.RegistryRecord(registryKey=regk, prefix=self.hab.pre)
        self.rgy.reger.regs.pin(keys=(self.registryName,), val=regord)
        self.rgy.reger.regs.rem(keys=(self.name,))

        self.remove(self.toRemove)
