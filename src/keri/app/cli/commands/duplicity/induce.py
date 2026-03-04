# -*- encoding: utf-8 -*-
"""
keri.kli.commands.duplicity.induce module

Command to intentionally induce duplicity by creating a divergent interaction
event and sending it to a single witness. This is TEST TOOLING ONLY for
verifying watcher duplicity detection.

WARNING: Any AID subjected to this process is permanently compromised.
"""
import argparse
import json

from hio.base import doing

from keri import kering
from keri.app import httping
from keri.app.cli.common import existing
from keri.app import habbing, agenting

parser = argparse.ArgumentParser(description='Induce duplicity by sending a divergent event to a single witness (TEST ONLY)')
parser.set_defaults(handler=lambda args: induce(args))
parser.add_argument('--name', '-n', help='keystore name and file location of KERI keystore', required=True)
parser.add_argument('--base', '-b', help='additional optional prefix to file location of KERI keystore',
                    required=False, default="")
parser.add_argument('--alias', '-a', help='human readable alias for the identifier', required=True)
parser.add_argument('--passcode', '-p', help='21 character encryption passcode for keystore (is not saved)',
                    dest="bran", default=None)
parser.add_argument('--data', '-d', help='Anchor data for the interaction event, \'@\' allowed for file path',
                    default=None, action="store", required=False)
parser.add_argument('--witness', '-w', help='AID prefix of the single witness to send the event to', required=True)


def induce(args):
    """
    Creates a divergent interaction event and sends it to a single witness,
    intentionally inducing duplicity for testing purposes.

    Args:
        args (parseargs): Command line arguments

    Returns:
        list: List of doers to execute
    """
    name = args.name
    alias = args.alias
    base = args.base
    bran = args.bran
    witness = args.witness

    if args.data is not None:
        try:
            if args.data.startswith("@"):
                with open(args.data[1:], "r") as f:
                    data = json.load(f)
            else:
                data = json.loads(args.data)
        except json.JSONDecodeError:
            raise kering.ConfigurationError("data supplied must be valid JSON to anchor in a seal")

        if not isinstance(data, list):
            data = [data]
    else:
        data = None

    induceDoer = DuplicityInduceDoer(name=name, base=base, alias=alias, bran=bran,
                                      data=data, witness=witness)

    return [induceDoer]


class DuplicityInduceDoer(doing.DoDoer):
    """
    DoDoer that creates a divergent interaction event and sends it to a single
    witness, intentionally inducing duplicity for testing watcher detection.

    WARNING: This will permanently compromise the AID.
    """

    def __init__(self, name, base, bran, alias, data=None, witness=None):
        """
        Initialize the DuplicityInduceDoer.

        Parameters:
            name (str): Keystore name
            base (str): Base directory for keystore
            bran (str): Passcode for keystore
            alias (str): Alias of the identifier
            data (list): Anchor data for the interaction event
            witness (str): AID prefix of the single witness to send to
        """
        self.alias = alias
        self.data = data
        self.witness = witness

        self.hby = existing.setupHby(name=name, base=base, bran=bran)
        self.hbyDoer = habbing.HaberyDoer(habery=self.hby)
        doers = [self.hbyDoer, doing.doify(self.induceDo)]

        super(DuplicityInduceDoer, self).__init__(doers=doers)

    def induceDo(self, tymth, tock=0.0, **opts):
        """
        Generator method that creates the duplicitous event and sends it.
        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        # Get the hab
        hab = self.hby.habByName(name=self.alias)
        if hab is None:
            print(f"Error: No identifier found with alias '{self.alias}'")
            self.remove([self.hbyDoer])
            return

        # Verify the witness is in the identifier's witness list
        if self.witness not in hab.kever.wits:
            print(f"Error: Witness {self.witness} is not in the witness list for {self.alias}")
            print(f"Current witnesses: {hab.kever.wits}")
            self.remove([self.hbyDoer])
            return

        # Show confirmation warning
        print("\n" + "=" * 60)
        print("  WARNING: DUPLICITY INDUCTION")
        print("=" * 60)
        print()
        print("This command creates a divergent event log entry and publishes")
        print("it to a single witness. This WILL produce detectable duplicity")
        print("for this AID.")
        print()
        print("THIS AID WILL BE PERMANENTLY COMPROMISED.")
        print()
        print("This command exists solely for testing watcher duplicity")
        print("detection pipelines. Do not use it on production identifiers.")
        print()
        print(f"  AID:      {hab.pre}")
        print(f"  Alias:    {self.alias}")
        print(f"  Base:     {self.hby.base}")
        print(f"  Witness:  {self.witness}")
        print(f"  Data:     {self.data}")
        print()

        try:
            response = input("Type 'yes I want duplicity' to proceed: ")
        except EOFError:
            print("\nAborted: No input received (non-interactive mode)")
            self.remove([self.hbyDoer])
            return

        if response != "yes I want duplicity":
            print("\nAborted: Confirmation not received")
            self.remove([self.hbyDoer])
            return

        print()

        # Create and sign the interaction event
        print(f"Creating interaction event with data: {self.data}")
        hab.interact(data=self.data)
        sn = hab.kever.sn

        # Get the signed event bytes
        msg = hab.makeOwnEvent(sn=sn)

        print(f"Event created at sequence number: {sn}")

        # Create HTTP client for the single witness
        try:
            client, clientDoer = agenting.httpClient(hab, self.witness)
            self.extend([clientDoer])
        except kering.MissingEntryError as e:
            print(f"Error: Unable to create HTTP client for witness {self.witness}: {e}")
            print("Make sure the witness OOBI has been resolved.")
            self.remove([self.hbyDoer])
            return

        # Send the event to the single witness using the receipts endpoint
        print(f"Sending event to witness: {self.witness}")
        httping.streamCESRRequests(client=client, dest=self.witness, ims=bytearray(msg), path="receipts")

        # Wait for response (but don't require receipt)
        while not client.responses:
            _ = yield self.tock

        rep = client.respond()
        if rep.status == 200:
            print(f"Event accepted by witness (status: {rep.status})")
        else:
            print(f"Warning: Witness returned status {rep.status}")

        print()
        print("=" * 60)
        print("  DUPLICITY INDUCED SUCCESSFULLY")
        print("=" * 60)
        print()
        print(f"Prefix:           {hab.pre}")
        print(f"Sequence Number:  {sn}")
        print(f"Witness:          {self.witness}")
        print()
        print("This AID now has a divergent event at this sequence number.")
        print("A watcher querying multiple witnesses should detect the conflict.")
        print()

        # Cleanup
        self.remove([clientDoer, self.hbyDoer])
        return
