# -*- encoding: utf-8 -*-
"""
tests.db.dbing module

"""

import logging
import os

import pytest

from hio.base import doing
from hio.core.tcp import clienting, serving

from keri import help  # logger support
from keri import core, kering
from keri.core import eventing, coring, serdering

from keri.app import habbing, directing

from keri.demo import demoing


@pytest.fixture()
def directHabs():
    """Provide temporary sender and receiver habitats for direct-mode tests."""
    with habbing.openHab(name="alice-directing", temp=True) as (_, alice), \
            habbing.openHab(name="bob-directing", temp=True) as (_, bob):
        yield alice, bob


def makeRemoter(ims=b"", *, cutoff=False):
    """Create an accepted connection buffer for direct Reactant tests."""
    remoter = serving.Remoter(ha=("127.0.0.1", 5632), ca=("127.0.0.1", 5633), cs=None)
    remoter.rxbs.extend(ims)
    remoter.cutoff = cutoff
    return remoter


def test_directing_basic():
    """
    Test directing
    """
    help.ogler.resetLevel(level=logging.INFO)

    raw = b"raw salt to test"

    #  create bob signers and secrecies
    bobSigners = core.Salter(raw=raw).signers(count=8, path="bob", temp=True)
    bobSecrecies = [[signer.qb64] for signer in bobSigners]

    # bob inception transferable (nxt digest not empty)
    bobSerder = eventing.incept(keys=[bobSigners[0].verfer.qb64],
                                ndigs=[coring.Diger(ser=bobSigners[1].verfer.qb64b).qb64],
                                code=coring.MtrDex.Blake3_256)

    bob = bobSerder.ked["i"]
    assert bob == 'EFa1wAk_coghxxGCID6jEN79Kmvyj0Y1wWN_ndUv3LjW'


    #  create eve signers and secrecies
    eveSigners = core.Salter(raw=raw).signers(count=8, path="eve", temp=True)
    eveSecrecies = [[signer.qb64] for signer in eveSigners]

    # eve inception transferable (nxt digest not empty)
    eveSerder = eventing.incept(keys=[eveSigners[0].verfer.qb64],
                                ndigs=[coring.Diger(ser=eveSigners[1].verfer.qb64b).qb64],
                                code=coring.MtrDex.Blake3_256)

    eve = eveSerder.ked["i"]
    assert eve == 'EFhg5my9DuMU6gw1CVk6QgkmZKBttWSXDzVzWVmxh0_K'


    with (habbing.openHby(name="eve", base="test") as eveHby,
          habbing.openHby(name="bob", base="test") as bobHby):

        limit = 1.0
        tock = 0.03125
        doist = doing.Doist(limit=limit, tock=tock)

        bobPort = 5620  # bob's TCP listening port for server
        evePort = 5621  # eve's TCP listneing port for server

        # setup bob
        bobHab = bobHby.makeHab(name="Bob", secrecies=bobSecrecies)
        assert bobHab.iserder.said == bobSerder.said
        assert bobHab.pre == bob

        bobClient = clienting.Client(tymth=doist.tymen(), host='127.0.0.1', port=evePort)
        bobClientDoer = clienting.ClientDoer(tymth=doist.tymen(), client=bobClient)

        bobDirector = directing.Director(hab=bobHab, client=bobClient)
        assert bobDirector.hab == bobHab
        assert bobDirector.client == bobClient
        assert id(bobDirector.hab.kvy.kevers) == id(bobHab.kevers)
        assert bobDirector.hab.kvy.db == bobHby.db

        bobReactor = directing.Reactor(hab=bobHab, client=bobClient)
        assert bobReactor.hab == bobHab
        assert bobReactor.client == bobClient
        assert id(bobReactor.hab.kvy.kevers) == id(bobHab.kevers)
        assert bobReactor.hab.kvy.db == bobHby.db
        assert id(bobReactor.parser.ims) == id(bobReactor.client.rxbs)
        assert id(bobReactor.client.rxbs) == id(bobDirector.client.rxbs)

        bobServer = serving.Server(host="", port=bobPort)
        bobServerDoer = serving.ServerDoer(server=bobServer)

        bobDirectant = directing.Directant(hab=bobHab, server=bobServer)
        assert bobDirectant.hab == bobHab
        assert bobDirectant.server == bobServer
        # Bob's Reactants created on demand

        # setup eve
        eveHab = eveHby.makeHab(name="Eve", secrecies=eveSecrecies)
        print(eveHab.iserder.pretty())
        print(eveSerder.pretty())
        assert eveHab.iserder.said == eveSerder.said
        assert eveHab.pre == eve

        eveClient = clienting.Client(tymth=doist.tymen(), host='127.0.0.1', port=bobPort)
        eveClientDoer = clienting.ClientDoer(tymth=doist.tymen(), client=eveClient)

        eveDirector = directing.Director(hab=eveHab, client=eveClient)
        assert eveDirector.hab == eveHab
        assert eveDirector.client == eveClient
        assert id(eveDirector.hab.kvy.kevers) == id(eveHab.kevers)
        assert eveDirector.hab.kvy.db == eveHby.db

        eveReactor = directing.Reactor(hab=eveHab, client=eveClient)
        assert eveReactor.hab == eveHab
        assert eveReactor.client == eveClient
        assert id(eveReactor.hab.kvy.kevers) == id(eveHab.kevers)
        assert eveReactor.hab.kvy.db == eveHby.db
        assert id(eveReactor.parser.ims) == id(eveReactor.client.rxbs)
        assert id(eveReactor.client.rxbs) == id(eveDirector.client.rxbs)

        eveServer = serving.Server(host="", port=evePort)
        eveServerDoer = serving.ServerDoer(server=eveServer)

        eveDirectant = directing.Directant(hab=eveHab, server=eveServer)
        assert eveDirectant.hab == eveHab
        assert eveDirectant.server == eveServer
        # Eve's Reactants created on demand

        bobMsgTx = b"Hi Eve I am  Bob"
        bobDirector.client.tx(bobMsgTx)

        eveMsgTx = b"Hi Bob its me Eve"
        eveDirector.client.tx(eveMsgTx)

        doers = [bobClientDoer, bobDirector, bobReactor, bobServerDoer, bobDirectant,
                 eveClientDoer, eveDirector, eveReactor, eveServerDoer, eveDirectant]
        doist.do(doers=doers)
        assert doist.tyme == limit

        assert bobClient.opened is False
        assert bobServer.opened is False
        assert eveClient.opened is False
        assert eveServer.opened is False

        assert not bobClient.txbs
        ca, ix = list(eveServer.ixes.items())[0]
        eveMsgRx = bytes(ix.rxbs)  # ColdStart Error flushes buffer
        assert eveMsgRx == b''
        # assert eveMsgRx == bobMsgTx

        assert not eveClient.txbs
        ca, ix = list(bobServer.ixes.items())[0]
        bobMsgRx = bytes(ix.rxbs)  # ColdStart Error flushes buffer
        assert bobMsgRx == b''
        # assert bobMsgRx == eveMsgTx

    assert not os.path.exists(eveHby.db.path)
    assert not os.path.exists(bobHby.db.path)

    help.ogler.resetLevel(level=help.ogler.level)
    """End Test"""


def test_reactant_drains_complete_messages_after_receive_cutoff(directHabs):
    """Parse both buffered events after receive EOF; only the last completes RX drain.
    Bob must advance Alice's key state through both events without receive failure.
    This checks inbound parsing only; Bob's receipt cues are not sent to Alice.
    """
    alice, bob = directHabs

    first = alice.makeOwnEvent(sn=0)
    alice.interact()
    second = alice.makeOwnEvent(sn=1)

    remoter = makeRemoter(first + second, cutoff=True)
    reactant = directing.Reactant(hab=bob, remoter=remoter)
    dog = reactant.msgDo(tymth=lambda: 0.0, tock=0.0)

    assert next(dog) == 0.0  # Prime msgDo at its enter-context yield.

    assert next(dog) == 0.0  # Parse and dispatch the first buffered message.
    assert not reactant.messageInProgress
    assert not reactant.rxDrained  # The buffered successor still prevents drain.
    assert reactant.kevery.kevers[alice.pre].sn == 0

    assert next(dog) == 0.0  # Parse and dispatch the second buffered message.
    assert not reactant.messageInProgress
    assert reactant.rxDrained  # Both complete messages reached a safe EOF boundary.
    assert not reactant.rxFailed
    assert reactant.kevery.kevers[alice.pre].sn == 1
    dog.close()


def test_reactant_rejects_incomplete_message_at_receive_cutoff(directHabs):
    """Treat EOF within a body or its attachments as incomplete-message failure.
    Record ShortageError and discard the unusable remainder without reporting
    successful receive drain.
    """
    alice, bob = directHabs

    message = alice.makeOwnEvent(sn=0)
    bodySize = serdering.SerderKERI(raw=message).size

    # Exercise shortages in the body, at its boundary, and in attachments.
    for cut in (10, bodySize, len(message) - 1):
        remoter = makeRemoter(message[:cut], cutoff=True)
        reactant = directing.Reactant(hab=bob, remoter=remoter)
        dog = reactant.msgDo(tymth=lambda: 0.0, tock=0.0)

        assert next(dog) == 0.0  # Prime msgDo at its enter-context yield.
        assert next(dog) == 0.0  # Turn the parser shortage at EOF into failure.
        assert not reactant.messageInProgress
        assert not reactant.rxDrained
        assert reactant.rxFailed  # Incomplete EOF is terminal, never a clean drain.
        assert isinstance(reactant.rxError, kering.ShortageError)
        assert "buffered bytes remain" in str(reactant.rxError)
        assert not remoter.rxbs  # Discard the unusable suffix after recording failure.
        dog.close()


# False: attachments arrive later; True: receive EOF arrives before the attachments.
@pytest.mark.parametrize("cutoff", [False, True])
def test_reactant_tracks_consumed_partial_message(directHabs, cutoff):
    """An empty buffer is not drained while the parser still needs attachments.
    Supplying them completes and accepts the event; receive cutoff instead
    fails the partial message without accepting it.
    """
    alice, bob = directHabs
    message = alice.makeOwnEvent(sn=0)
    bodySize = serdering.SerderKERI(raw=message).size
    remoter = makeRemoter(message[:bodySize])
    reactant = directing.Reactant(hab=bob, remoter=remoter)
    dog = reactant.msgDo(tymth=lambda: 0.0, tock=0.0)
    try:
        next(dog)
        next(dog)  # Consume the body, then wait for its attachments.
        assert not remoter.rxbs
        assert reactant.messageInProgress
        assert not reactant.rxDrained
        assert not reactant.rxFailed

        if cutoff:
            remoter.cutoff = True  # EOF makes the missing attachments unrecoverable.
        else:
            remoter.rxbs.extend(message[bodySize:])  # Supply the rest of the event.
        next(dog)
        # Both paths end parsing; only the non-cutoff case accepts the event.
        assert not reactant.messageInProgress
        assert reactant.rxFailed == cutoff
        assert reactant.rxDrained == (not cutoff)
        assert (alice.pre in bob.kevers) == (not cutoff)
    finally:
        dog.close()


def test_reactant_tracks_active_response_iterator(directHabs, monkeypatch):
    """A popped cue can still owe responses after the cue queue becomes empty.
    Report response production complete only when its iterator finishes,
    even though the generated bytes remain queued for transport.
    """
    _, bob = directHabs
    remoter = makeRemoter()
    reactant = directing.Reactant(hab=bob, remoter=remoter)

    # Exercise the documented multiple-message-per-cue producer contract.
    def responses(cues):
        assert cues.pull() == {"kin": "multi"}
        yield b"first"
        yield b"second"

    monkeypatch.setattr(bob, "processCuesIter", responses)
    dog = reactant.cueDo(tymth=lambda: 0.0, tock=0.0)
    try:
        next(dog)  # Prime cueDo at its initial yield; no cues processed yet.
        assert reactant.responseSettled
        reactant.kevery.cues.append({"kin": "multi"})
        assert not reactant.responseSettled

        next(dog)  # Pop the cue, queue the first response, and suspend cueDo.
        assert remoter.txbs == b"first"
        assert not reactant.kevery.cues
        assert not reactant.responseSettled  # The popped cue still owes output.
        next(dog)  # Resume the same producer and queue its second response.
        assert remoter.txbs == b"firstsecond"
        assert not reactant.responseSettled  # Producer exhaustion is not observed yet.
        next(dog)  # Observe producer exhaustion and clear cueInProgress.
        assert reactant.responseSettled  # Local production, not transport drain.
        assert remoter.txbs
    finally:
        dog.close()
    assert not reactant.cueInProgress


def test_runcontroller_demo():
    """
    Test demo runController function
    """
    help.ogler.resetLevel(level=logging.DEBUG)

    name = "bob"  # must be one of 'bob', 'sam', 'eve'
    remote = 5621
    local = 5620
    expire = 1.0

    raw = b"raw salt to test"

    #  create secrecies
    secrecies = [[signer.qb64] for signer in
                 core.Salter(raw=raw).signers(count=8,
                                                path=name,
                                                temp=True)]

    doers = demoing.setupDemoController(secrecies=secrecies,
                                        name=name,
                                        remotePort=remote,
                                        localPort=local)

    directing.runController(doers=doers, expire=expire)

    help.ogler.resetLevel(level=help.ogler.level)
    """End Test"""


if __name__ == "__main__":
    test_directing_basic()
