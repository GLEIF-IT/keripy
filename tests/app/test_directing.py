# -*- encoding: utf-8 -*-
"""
tests.db.dbing module

"""

import logging
import os
import socket

import pytest

from hio.base import doing
from hio.core.tcp import clienting, serving

from keri import help  # logger support
from keri import core, kering
from keri.core import eventing, coring, serdering

from keri.app import habbing, directing

from keri.db import dbing
from keri.demo import demoing


@pytest.fixture()
def directHabs():
    """Provide temporary sender and receiver habitats for direct-mode tests."""
    with habbing.openHab(name="alice-directing", temp=True) as (_, alice), \
            habbing.openHab(name="bob-directing", temp=True) as (_, bob):
        yield alice, bob


def makeRemoter(ims=b"", *, cutoff=False, cs=None, tymeout=None):
    """Create an accepted connection buffer for direct Reactant tests."""
    remoter = serving.Remoter(ha=("127.0.0.1", 5632), ca=("127.0.0.1", 5633),
                              cs=cs, tymeout=tymeout)
    remoter.rxbs.extend(ims)
    remoter.cutoff = cutoff
    return remoter


def drainSocket(sock):
    """Return all currently readable bytes without blocking."""
    sock.setblocking(False)
    received = bytearray()
    while True:
        try:
            data = sock.recv(4096)
        except BlockingIOError:
            break
        if not data:
            break
        received.extend(data)
    return bytes(received)


def recurUntil(doist, condition, message):
    """Recur a bounded Doist until condition is true or its limit expires."""
    if doist.limit is None or doist.limit <= 0.0:
        raise ValueError("recur_until requires a positive Doist limit")

    stop = doist.tyme + doist.limit
    while not condition():
        if doist.tyme >= stop:
            raise AssertionError(message)
        doist.recur()


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


def test_directant_drains_response_after_peer_half_close(directHabs):
    """EOF before Reactant creation must not discard Alice's buffered request.
    Bob drains its response before closing; Alice reads and accepts Bob's receipt.
    This proves delivery over this socket, not remote durable storage.
    """
    alice, bob = directHabs
    remoterSocket, peerSocket = socket.socketpair()
    remoter = makeRemoter(cs=remoterSocket, tymeout=1.0)
    ca = remoter.ca

    server = serving.Server(host="127.0.0.1", port=0, tymeout=1.0)
    directant = directing.Directant(hab=bob, server=server)
    serverDoer = serving.ServerDoer(server=server)
    doist = doing.Doist(tock=0.03125, limit=1.0,
                        doers=[directant, serverDoer])
    doist.enter()
    remoter.wind(doist.tymen())
    server.ixes[ca] = remoter

    try:
        peerSocket.sendall(alice.makeOwnEvent(sn=0))
        peerSocket.shutdown(socket.SHUT_WR)  # Send EOF but keep response reads open.
        # Exercise EOF arriving before Directant creates the per-connection parser.
        remoter.serviceReceives()
        assert remoter.cutoff and remoter.rxbs

        # Parse the request, drain its receipt, and then remove the connection.
        recurUntil(
            doist,
            condition=lambda: ca not in server.ixes,
            message="peer-half-closed connection did not drain its response",
        )

        assert alice.pre in bob.kevers  # should have processed request before close
        response = drainSocket(peerSocket)
        alice.psr.parse(ims=bytearray(response))  # Process Bob's inception and receipt.
        receipts = alice.db.getVrcs(dbing.dgKey(alice.pre, alice.iserder.said))
        assert any(bytes(receipt).startswith(bob.pre.encode()) for receipt in receipts)
        assert not remoter.txbs  # should have drained the local response buffer
        assert ca not in directant.rants
        assert ca not in directant.drainStops
    finally:
        doist.exit()
        peerSocket.close()


# Neither case has a Reactant: the second adds output with no application owner.
@pytest.mark.parametrize("queued", [b"", b"ownerless output"])
def test_directant_closes_receive_cutoff_without_buffered_input(directHabs, queued):
    """An EOF connection without input or a Reactant closes immediately.
    Both an empty send buffer and unexpected ownerless output avoid a speculative
    drain deadline; neither case has application work to supervise.
    """
    _, bob = directHabs

    remoter = makeRemoter(cutoff=True)
    remoter.txbs.extend(queued)
    ca = remoter.ca
    server = serving.Server()
    server.ixes[ca] = remoter
    directant = directing.Directant(hab=bob, server=server)
    directant.wind(lambda: 0.0)
    dog = directant.serviceDo(tymth=lambda: 0.0, tock=0.0)

    next(dog)  # Prime serviceDo at its enter-context yield.
    next(dog)  # Remove the EOF connection without creating a Reactant or deadline.
    assert ca not in server.ixes
    assert ca not in directant.rants
    assert ca not in directant.drainStops  # should remove deadline bookkeeping

    dog.close()
    server.close()


def test_directant_requires_finite_positive_drain_timeout(directHabs):
    """Reject zero, negative, infinite and NaN drain durations.
    Every retained EOF connection must have a finite positive lifetime bound.
    """
    _, bob = directHabs
    server = serving.Server()

    # A bounded drain deadline must be positive and finite.
    for drainTymeout in (0.0, -1.0, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            directing.Directant(hab=bob, server=server,
                                drainTymeout=drainTymeout)

    server.close()


def test_directant_timeout_services_boundary_input_before_drain(directHabs):
    """Input waiting at idle expiry refreshes the timer before local shutdown.
    Complete a split request at that boundary, then let idle expiry close normally;
    Alice must still be able to read and accept Bob's receipt after cleanup.
    """
    alice, bob = directHabs
    message = alice.makeOwnEvent(sn=0)
    split = len(message) // 2

    remoterSocket, peerSocket = socket.socketpair()
    remoter = makeRemoter(message[:split], cs=remoterSocket,
                          tymeout=0.0625)  # two hio ticks timeout
    ca = remoter.ca

    server = serving.Server(host="127.0.0.1", port=0, tymeout=0.0625)
    directant = directing.Directant(hab=bob, server=server)
    serverDoer = serving.ServerDoer(server=server)
    doist = doing.Doist(tock=0.03125, limit=1.0,
                        doers=[directant, serverDoer])
    doist.enter()
    remoter.wind(doist.tymen())
    server.ixes[ca] = remoter

    try:
        # First recurrence creates the Reactant.
        doist.recur()  # time accumulated = 1 tick or 0.03125
        assert ca in directant.rants
        rant = directant.rants[ca]

        # Second recurrence advances its parser to wait at the idle boundary.
        doist.recur()  # time accumulated = 2 ticks or 0.0625 - timeout/expiry occurs
        assert remoter.tymer.expired  # Establish that final receive runs at expiry.
        assert rant.messageInProgress

        # Final receive refreshes HIO's timer instead of closing at the boundary.
        peerSocket.sendall(message[split:])
        doist.recur()
        assert not remoter.cutoff  # Boundary input refreshed the timer before shutdown.
        assert not remoter.tymer.expired
        assert ca not in directant.drainStops  # No drain starts on a refreshed connection.

        # No further input: the next idle expiry initiates the bounded local drain.
        recurUntil(
            doist,
            condition=lambda: ca not in server.ixes,
            message="timed-out connection did not finish draining",
        )

        assert alice.pre in bob.kevers  # should have completed the split request
        assert rant.rxDrained
        assert not rant.rxFailed
        response = drainSocket(peerSocket)
        alice.psr.parse(ims=bytearray(response))  # Accept Bob's inception and receipt.
        receipts = alice.db.getVrcs(dbing.dgKey(alice.pre, alice.iserder.said))
        assert any(bytes(receipt).startswith(bob.pre.encode()) for receipt in receipts)
        assert not remoter.txbs
        assert ca not in directant.rants
        assert ca not in directant.drainStops
    finally:
        doist.exit()
        peerSocket.close()


def test_directant_tx_cutoff_accounts_for_unsent_response(
        directHabs, monkeypatch):
    """Terminal sending must still admit input waiting on the open receive side.
    Directant takes a final receive pass, then Bob parses the request during drain;
    its unsendable receipt is logged, not treated as delivered.
    """
    alice, bob = directHabs
    remoterSocket, peerSocket = socket.socketpair()
    remoter = makeRemoter(cs=remoterSocket, tymeout=1.0)
    remoter.txCutoff = True  # Send is terminal; receive still needs final service.
    ca = remoter.ca

    server = serving.Server()
    server.ixes[ca] = remoter
    directant = directing.Directant(hab=bob, server=server,
                                    drainTymeout=0.25)
    # Directant must consume socket input and account for its unsendable receipt.
    doist = doing.Doist(tock=0.03125, limit=1.0, doers=[directant])
    doist.enter()
    errors = []
    monkeypatch.setattr(directing.logger, "error",
                        lambda msg, *args: errors.append(msg % args))

    try:
        # Leave input in the kernel buffer for Directant's txCutoff receive pass.
        peerSocket.sendall(alice.makeOwnEvent(sn=0))
        assert not remoter.cutoff
        assert not remoter.rxbs

        recurUntil(
            doist,
            condition=lambda: ca not in server.ixes,
            message="transmit-cutoff connection did not terminate",
        )

        assert alice.pre in bob.kevers  # Final receive must still process the request.
        assert remoter.cutoff  # Directant initiated receive shutdown without peer EOF.
        assert remoter.txbs  # Receipt remains queued because send is terminal.
        assert any("after transmit cutoff" in error for error in errors)  # expose terminal reason
        assert any(f"txbs={len(remoter.txbs)}" in error for error in errors)  # account for unsent bytes
        assert ca not in directant.rants
        assert ca not in directant.drainStops
    finally:
        doist.exit()
        server.close()
        peerSocket.close()


def test_directant_idle_expiry_ends_incomplete_request(directHabs):
    """Idle expiry with no new input must end an incomplete request as a shortage.
    The active parser reaches receive failure before its Reactant is removed;
    no event or receipt is accepted for the truncated request.
    """
    alice, bob = directHabs
    message = alice.makeOwnEvent(sn=0)
    bodySize = serdering.SerderKERI(raw=message).size
    remoterSocket, peerSocket = socket.socketpair()
    remoter = makeRemoter(message[:bodySize], cs=remoterSocket, tymeout=0.0625)
    ca = remoter.ca
    server = serving.Server()
    server.ixes[ca] = remoter
    directant = directing.Directant(hab=bob, server=server)
    doist = doing.Doist(tock=0.03125, limit=1.0, doers=[directant])
    doist.enter()

    try:
        doist.recur()  # Create the Reactant while the idle timer is still running.
        rant = directant.rants[ca]
        doist.recur()  # Consume the body and wait for attachments at idle expiry.
        assert remoter.tymer.expired
        assert rant.messageInProgress
        assert not remoter.rxbs  # An empty buffer does not mean parsing is complete.

        doist.recur()  # No boundary input: shut down receive but retain the active parser.
        assert remoter.cutoff
        assert directant.rants[ca] is rant
        # The parser has its own cadence; let it observe EOF before supervisor cleanup.
        recurUntil(doist, lambda: rant.rxFailed,
                   "idle-expired parser did not report its incomplete request")
        assert rant.rxFailed
        assert isinstance(rant.rxError, kering.ShortageError)
        assert not rant.rxDrained

        recurUntil(doist, lambda: ca not in server.ixes,
                   "idle-expired partial request did not terminate")
        assert alice.pre not in bob.kevers
        assert not remoter.txbs
        assert not drainSocket(peerSocket)
        assert ca not in directant.rants
        assert ca not in directant.drainStops
    finally:
        doist.exit()
        server.close()
        peerSocket.close()


def test_directant_response_drain_stops_at_absolute_deadline(
        directHabs, monkeypatch):
    """Partial send progress may refresh idle time but must not extend the drain deadline.
    Simulated one-byte sends leave output pending when the absolute deadline wins;
    removal must log the abandoned bytes and release the Reactant.
    """
    alice, bob = directHabs
    remoterSocket, peerSocket = socket.socketpair()
    remoter = makeRemoter(alice.makeOwnEvent(sn=0), cutoff=True,
                          cs=remoterSocket, tymeout=1.0)

    # Simulate one-byte writes that continually refresh HIO's idle timer.
    def serviceOneByteAndRefreshTimer():
        if remoter.txbs:
            del remoter.txbs[:1]
            remoter.refresh()

    monkeypatch.setattr(remoter, "serviceSends",
                        serviceOneByteAndRefreshTimer)
    ca = remoter.ca

    server = serving.Server(host="127.0.0.1", port=0, tymeout=1.0)
    directant = directing.Directant(hab=bob, server=server,
                                    drainTymeout=0.125)
    serverDoer = serving.ServerDoer(server=server)
    doist = doing.Doist(tock=0.03125, limit=1.0,
                        doers=[directant, serverDoer])
    doist.enter()
    remoter.wind(doist.tymen())
    server.ixes[ca] = remoter
    errors = []
    monkeypatch.setattr(directing.logger, "error",
                        lambda msg, *args: errors.append(msg % args))

    try:
        # First recurrence fixes Directant's non-refreshing drain deadline.
        doist.recur()
        drainStop = directant.drainStops[ca]
        transportRemaining = remoter.tymer.remaining

        # Second recurrence advances output and refreshes only HIO's timer.
        doist.recur()
        assert directant.drainStops[ca] == drainStop  # Partial sends cannot extend drain.
        assert remoter.tymer.remaining > transportRemaining  # HIO timer did refresh.

        recurUntil(
            doist,
            condition=lambda: ca not in server.ixes,
            message="blocked response did not reach its drain deadline",
        )

        assert alice.pre in bob.kevers
        assert remoter.txbs  # Absolute deadline wins before the trickle can drain output.
        assert any("after drain deadline expired" in error for error in errors)  # expose deadline reason
        assert any(f"txbs={len(remoter.txbs)}" in error for error in errors)
        assert any("txCutoff=False" in error for error in errors)
        assert ca not in directant.rants
        assert ca not in directant.drainStops
    finally:
        doist.exit()
        peerSocket.close()


def test_directant_peer_eof_stops_on_transmit_cutoff(directHabs, monkeypatch):
    """After receive EOF, terminal sending must end the drain with unsent-work diagnostics.
    Buffered input is still processed; its receipt cannot be delivered.
    This does not exercise transmit failure initiating receive shutdown (B3).
    """
    alice, bob = directHabs
    remoter = makeRemoter(alice.makeOwnEvent(sn=0), cutoff=True)
    remoter.txCutoff = True  # Model a terminal send side after receive has ended.
    server = serving.Server()
    server.ixes[remoter.ca] = remoter
    directant = directing.Directant(hab=bob, server=server)
    doist = doing.Doist(tock=0.03125, limit=1.0, doers=[directant])
    errors = []
    monkeypatch.setattr(directing.logger, "error", lambda msg, *args: errors.append(msg % args))
    doist.enter()
    try:
        recurUntil(doist, lambda: remoter.ca not in server.ixes,
                   "transmit cutoff did not terminate the peer-EOF drain")
        assert alice.pre in bob.kevers
        assert remoter.txbs  # The generated receipt remains unsent.
        assert any("after transmit cutoff" in error for error in errors)
        assert any(f"txbs={len(remoter.txbs)}" in error for error in errors)
        assert remoter.ca not in directant.rants
        assert not directant.drainStops
    finally:
        doist.exit()
        server.close()


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
