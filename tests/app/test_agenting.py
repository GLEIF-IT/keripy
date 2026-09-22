# -*- encoding: utf-8 -*-
"""
tests.app.agenting module

"""
import time
import socket
import select
import struct
from contextlib import closing

import falcon
import pytest

from hio.base import doing, tyming
from hio.core import http
from hio.core.tcp import serving

from keri import kering, core
from keri.core import coring, serdering
from keri.core.coring import Seqner
from keri.help import nowIso8601
from keri.app import habbing, indirecting, agenting, directing
from keri.db import basing, dbing
from keri.vdr import eventing, viring
from tests.app.test_directing import openDoist


def test_http_messengers_read_state_after_client_service():
    expected = http.clienting.Response(
        version=(1, 1),
        status=204,
        reason=None,
        headers={},
        body=b"",
        data=None,
        request=None,
        errored=False,
        error=None,
    )

    # Test both types of messenger
    for klas in (agenting.HTTPMessenger, agenting.HTTPStreamMessenger):
        kwa = dict(
            hab=None,
            wit="witness",
            url="http://127.0.0.1:1",
        )
        if klas is agenting.HTTPStreamMessenger:
            kwa["msg"] = b"message"

        messenger = klas(**kwa)
        serviced = False

        def service():  # mock just to verify order of call to messenger
            nonlocal serviced
            if not serviced:
                messenger.client.responses.append(expected._asdict())  # mock HTTP success
                serviced = True

        messenger.client.service = service  # Inject mock into service
        doist = doing.Doist(tock=0.03125, limit=1.0, doers=[messenger])
        doist.enter()

        try:
            doist.recur()  # iterate doers normally exactly once

            assert serviced
            if isinstance(messenger, agenting.HTTPStreamMessenger):
                assert messenger.done  # stream messenger is done after one message
                assert messenger.rep == expected  # should be exactly one response
            else:
                assert list(messenger.sent) == [expected]  # should be exactly one response
        finally:
            doist.exit()


def test_stream_messenger_from_admits_tcp_payload():
    with habbing.openHab(name="tcp-stream-payload", temp=True) as (_, hab):
        msg = hab.makeOwnInception()
        messenger = agenting.streamMessengerFrom(
            hab=hab,
            pre=hab.pre,
            urls={kering.Schemes.tcp: "tcp://127.0.0.1:5631"},
            msg=msg,
        )

        assert list(messenger.msgs) == [bytearray(msg)]


@pytest.mark.parametrize("klas", [agenting.TCPMessenger,
                                  agenting.TCPStreamMessenger])
def test_tcp_messenger_accounts_for_real_delivery(klas):
    with habbing.openHby(name="sender", temp=True) as senderHby, \
            habbing.openHby(name="receiver", temp=True) as receiverHby:
        senderHab = senderHby.makeHab(name="sender")
        receiverHab = receiverHby.makeHab(name="receiver",
                                          transferable=False)

        server = serving.Server(host="127.0.0.1", port=0)
        assert server.reopen()
        server.eha = server.ha
        messenger = klas(hab=senderHab,
                         wit=receiverHab.pre,
                         url=f"tcp://127.0.0.1:{server.ha[1]}")
        msg = bytearray(senderHab.makeOwnEvent(sn=0))

        # Queuing work must make the messenger non-idle before scheduling starts.
        assert messenger.idle
        messenger.msgs.append(msg)
        assert not messenger.idle

        doist = doing.Doist(tock=0.01,
                            limit=1.0,
                            doers=[serving.ServerDoer(server=server),
                                   directing.Directant(hab=receiverHab,
                                                       server=server),
                                   messenger])
        doist.enter()
        try:
            deadline = doist.tyme + doist.limit

            # Advance until the message leaves the queue but is still being sent.
            while (not messenger.messageInProgress and
                   doist.tyme < deadline):
                doist.recur()
                time.sleep(doist.tock)

            assert messenger.messageInProgress
            assert not messenger.idle

            # Continue through local transmission and parsing by the receiver.
            while ((not messenger.idle or
                    senderHab.pre not in receiverHby.kevers) and
                   doist.tyme < deadline):
                doist.recur()
                time.sleep(doist.tock)

            assert senderHab.pre in receiverHby.kevers

            # Consuming the completion cue must not make completed work non-idle.
            assert messenger.sent.popleft() == msg
            assert messenger.idle
        finally:
            doist.exit()



@pytest.fixture
def connectedTcpMessenger():
    """Connect a real messenger to a loopback server without sending application data."""
    with (
        habbing.openHab(name="tcp-outcome", temp=True) as (_, hab),
        closing(serving.Server(host="127.0.0.1", port=0, tymeout=0.0)) as server,
    ):
        assert server.reopen()
        server.eha = server.ha  # Advertise the port assigned by the OS.
        messenger = agenting.TCPMessenger(
            hab=hab, wit=hab.pre, url=f"tcp://127.0.0.1:{server.ha[1]}",
        )
        with openDoist(doers=[messenger], tock=0.03125, limit=1.0) as doist:
            # The scheduler drives the client; the test accepts on the server side.
            for _ in range(100):
                doist.recur()
                server.serviceConnects()
                if messenger.client is not None and messenger.client.connected and server.ixes:
                    break
                time.sleep(0.001)  # Let the OS progress the real TCP handshake.
            assert messenger.client.connected and len(server.ixes) == 1
            yield messenger, next(iter(server.ixes.values())), doist


def test_tcp_messenger_bounds_refused_connection():
    """Stop refused connection attempts after four ticks of logical scheduler time.
    HIO socket reopens do not reset the deadline; failure retains outstanding work
    without producing a sent notification.
    """
    with (
        habbing.openHab(name="tcp-refused", temp=True) as (_, hab),
        socket.socket() as endpoint,
    ):
        # Port 0 asks the OS for a free port. Bind reserves it, but without listen()
        # there is no listener to establish and queue connections for accept().
        endpoint.bind(("127.0.0.1", 0))
        tock = 0.03125  # Each recur() advances logical time by 1/32 second.
        first, second = b"first", b"second"
        messenger = agenting.TCPMessenger(
            hab=hab, wit=hab.pre, url=f"tcp://127.0.0.1:{endpoint.getsockname()[1]}",
            msgs=agenting.decking.Deck([first, second]), connectTimeout=4 * tock,
        )
        with openDoist(doers=[messenger], tock=tock, limit=1.0) as doist:
            # Capture the shared logical clock before recur() runs the messenger
            # and advances time. This is not a wall-clock timestamp.
            started = doist.tyme
            connectionDeadline = started + messenger.connectTimeout
            # Eight ticks is only a test-loop guard against a broken implementation.
            guardDeadline = started + 2 * messenger.connectTimeout
            doist.recur()  # Start the connection deadline and admit the first message.
            while not messenger.done and doist.tyme <= guardDeadline:
                doist.recur()  # Each retry consumes the same absolute time budget.
            # Prove termination by timeout, not merely that the loop guard expired.
            assert messenger.done and messenger.failed
            assert isinstance(messenger.error, TimeoutError)
            # The messenger times out at tick 4 (0.125); recur() then advances the
            # clock to tick 5 (0.15625) before returning to this assertion.
            assert doist.tyme <= connectionDeadline + doist.tock
            assert messenger.unsent == len(first) + len(second)
            assert messenger.messageInProgress and list(messenger.msgs) == [second]
            assert not messenger.idle and not messenger.sent
            assert messenger.client.cs is None and not messenger.deeds


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_tcp_messenger_requires_finite_positive_connection_deadline(timeout):
    """Reject values that would disable or make the initial connection bound invalid."""
    with pytest.raises(ValueError, match="finite and positive"):
        agenting.TCPMessenger(hab=None, wit="wit", url="tcp://127.0.0.1:1",
                             connectTimeout=timeout)


def test_tcp_messenger_receive_eof_still_sends(connectedTcpMessenger):
    """A peer closing only its send direction can still receive our queued message.
    Verify the bytes at the peer, not just the messenger's local completion cue.
    """
    messenger, remoter, doist = connectedTcpMessenger
    remoter.cs.shutdown(socket.SHUT_WR)  # Server stops sending but keeps reading.
    for _ in range(20):
        doist.recur()  # Client observes receive EOF without closing its send direction.
        if messenger.client.cutoff:
            break
    assert messenger.client.cutoff and not messenger.client.txCutoff

    # The initial-connect deadline no longer applies to this established connection.
    doist.tyme += messenger.connectTimeout + 1.0
    msg = b"output after receive EOF"
    messenger.msgs.append(msg)
    for _ in range(20):
        doist.recur()  # Client admits and flushes output despite receive EOF.
        remoter.serviceReceives()  # Server reads the actual bytes from the socket.
        if messenger.sent and remoter.rxbs == msg:
            break
    assert remoter.rxbs == msg
    assert list(messenger.sent) == [msg]
    assert messenger.idle and not messenger.failed


def test_tcp_messenger_retains_transmit_failure(connectedTcpMessenger):
    """A send failure preserves its cause and all unsent bytes, then closes the child.
    Shut down the socket's send direction so HIO observes a real broken pipe.
    """
    messenger, _, doist = connectedTcpMessenger
    first, second = b"not sent", b"still queued"
    messenger.msgs.extend([first, second])
    # receiptDo services sends before admitting new messages. This turn therefore
    # buffers first via client.tx(), then yields without attempting its socket send.
    doist.recur()
    assert messenger.messageInProgress and messenger.client.txbs == first

    # Shut down between admission and transmission, without setting HIO's flags.
    messenger.client.cs.shutdown(socket.SHUT_WR)
    # receiptDo resumes, loops back to serviceSends(), and discovers the broken pipe.
    doist.recur()
    assert messenger.done and messenger.failed
    cause = messenger.error
    assert isinstance(cause, BrokenPipeError)
    assert messenger.unsent == len(first) + len(second)
    assert messenger.client.txbs == first and list(messenger.msgs) == [second]
    assert not messenger.sent and not messenger.idle
    assert messenger.client.cs is None and not messenger.deeds
    messenger._fail(ConnectionError("later cleanup"))
    assert messenger.error is cause  # A later report cannot overwrite the first cause.



def test_tcp_messenger_keeps_sent_before_receive_failure(connectedTcpMessenger):
    """Account for a drained send before HIO reports a real peer reset on receive.
    Control the socket-service order to make this boundary deterministic; no HIO
    errors or flags are injected. The second message must remain outstanding.
    """
    messenger, remoter, doist = connectedTcpMessenger
    first, second = b"sent before failure", b"not admitted"
    messenger.msgs.extend([first, second])
    doist.recur()  # Admit first into txbs; receiptDo has not attempted its send yet.
    client = messenger.client
    assert messenger.messageInProgress and client.txbs == first

    # Drain through real HIO socket service without advancing the messenger.
    # This holds it at the boundary between sending bytes and recording completion.
    client.serviceSends()
    assert not client.txbs and not messenger.sent
    # Wait up to one wall-clock second for readiness; normally returns immediately.
    # This bounds the test wait without advancing the scheduler's logical clock.
    assert select.select(
        [remoter.cs],  # Sockets to watch for read readiness.
        [],           # No sockets watched for write readiness.
        [],           # No sockets watched for exceptional conditions.
        1.0,          # Maximum wall-clock wait in seconds.
    )[0]  # Assert that the returned list of readable sockets is nonempty.
    remoter.serviceReceives()
    assert remoter.rxbs == first  # Prove delivery before provoking the receive failure.

    # Abort the peer socket: zero-time SO_LINGER makes close send RST, not FIN.
    # Bypass Remoter.close(), whose graceful shutdown would change that scenario.
    remoter.cs.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    remoter.cs.close()
    remoter.cs = None  # The fixture still owns the Remoter, but its socket is closed.
    assert select.select([client.cs], [], [], 1.0)[0]  # Wait for OS readiness, not scheduler time.
    assert client.error is None and not client.cutoff and not client.txCutoff

    # serviceSends sees no buffered bytes. receiptDo records first as sent, then
    # real HIO receive observes ECONNRESET and sets error/cutoff/txCutoff itself.
    doist.recur()
    assert list(messenger.sent) == [first]
    assert messenger.done and isinstance(messenger.error, ConnectionResetError)
    assert messenger.error is client.error and client.cutoff and client.txCutoff
    assert messenger.unsent == len(second) and list(messenger.msgs) == [second]
    assert not messenger.messageInProgress and not messenger.idle
    assert client.cs is None and not messenger.deeds


def test_tcp_messenger_retains_failure_before_admission(connectedTcpMessenger):
    """A peer reset observed before admission leaves all queued messages unsent.
    Let real HIO receive service set the error and closure flags; the messenger
    must retain that cause and clean up without popping either message.
    """
    messenger, remoter, doist = connectedTcpMessenger
    client = messenger.client
    first, second = b"not admitted", b"still queued"
    messenger.msgs.extend([first, second])

    # Abort the connected peer before the messenger gets a turn to admit output.
    # SO_LINGER with zero timeout produces RST; graceful shutdown would send FIN.
    remoter.cs.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    remoter.cs.close()
    remoter.cs = None  # Prevent fixture cleanup from closing this socket again.
    # Wait for the OS to expose the reset without servicing HIO or advancing time.
    assert select.select([client.cs], [], [], 1.0)[0]
    assert client.error is None and not client.cutoff and not client.txCutoff
    assert not client.txbs and not messenger.messageInProgress

    # receiptDo services receives before admission. HIO observes ECONNRESET, and
    # the messenger's closure check exits before msgs.popleft() or client.tx().
    doist.recur()
    assert messenger.done and isinstance(messenger.error, ConnectionResetError)
    assert messenger.error is client.error and client.cutoff and client.txCutoff
    assert list(messenger.msgs) == [first, second]
    assert messenger.unsent == len(first) + len(second)
    assert not client.txbs and not messenger.sent
    assert not messenger.messageInProgress and not messenger.idle
    assert client.cs is None and not messenger.deeds


def test_http_messenger_accounts_for_real_delivery():
    with habbing.openHby(name="http-sender", temp=True) as senderHby, \
            habbing.openHby(name="http-receiver", temp=True) as receiverHby:
        senderHab = senderHby.makeHab(name="sender")
        receiverHab = receiverHby.makeHab(name="receiver",
                                          transferable=False)
        endpoint = indirecting.HttpEnd(rxbs=receiverHab.psr.ims)
        app = falcon.App()
        app.add_route("/", endpoint)
        servant = serving.Server(host="127.0.0.1", port=0)
        server = http.Server(app=app, servant=servant)
        assert server.reopen()
        servant.eha = servant.ha

        messenger = agenting.HTTPMessenger(
            hab=senderHab,
            wit=receiverHab.pre,
            url=f"http://127.0.0.1:{servant.ha[1]}",
        )
        msg = bytearray(senderHab.makeOwnEvent(sn=0))

        # The queued inception keeps the messenger active until its response arrives.
        messenger.msgs.append(bytearray(msg))
        assert not messenger.idle

        doist = doing.Doist(tock=0.01,
                            limit=1.0,
                            doers=[http.ServerDoer(server=server), messenger])
        doist.enter()
        try:
            deadline = doist.tyme + doist.limit

            # Drive the real HTTP exchange until the pending response is accounted for.
            while (not messenger.idle and doist.tyme < deadline):
                doist.recur()
                time.sleep(doist.tock)

            # Verify transport success and application-layer delivery to the receiver.
            response = messenger.sent.popleft()
            assert response.status == 204
            receiverHab.psr.parse()
            assert senderHab.pre in receiverHby.kevers

            # Removing the response cue does not erase completed lifecycle state.
            assert messenger.idle
        finally:
            doist.exit()


@pytest.fixture
def connectedHttpMessenger():
    """Connect a real HTTP messenger to a raw peer for response and socket tests."""
    with habbing.openHab(name="http-outcome", temp=True) as (_, hab), socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        server.setblocking(False)
        messenger = agenting.HTTPMessenger(
            hab=hab, wit=hab.pre, url=f"http://127.0.0.1:{server.getsockname()[1]}")
        with openDoist(doers=[messenger], tock=0.03125, limit=1.0) as doist:
            peer = None
            try:
                for _ in range(100):
                    doist.recur()  # The messenger drives its client; the fixture accepts the peer.
                    if peer is None:
                        try:
                            peer, _ = server.accept()
                            peer.setblocking(False)
                        except BlockingIOError:
                            pass
                    if peer is not None and messenger.client.connector.connected:
                        break
                    time.sleep(0.001)  # Let the OS progress the loopback handshake.
                assert peer is not None and messenger.client.connector.connected
                yield messenger, peer, doist, hab
            finally:
                if peer is not None:
                    peer.close()


def sendHttpRequests(messenger, peer, doist, hab, count=1):
    """Queue CESR requests and verify the first complete HTTP request at the peer.
    HIO waits for its response before transmitting any later queued request.
    """
    for _ in range(count):
        messenger.msgs.append(bytearray(hab.makeOwnInception()))
    for _ in range(20):
        doist.recur()  # msgDo queues HTTP requests; responseDo services the client.
        if messenger.pending == count and not messenger.client.connector.txbs:
            break
    assert messenger.pending == count and messenger.client.waited
    assert not messenger.client.connector.txbs
    assert len(messenger.client.requests) == count - 1

    # Empty txbs proves local drain only. Read the exact built HTTP request at
    # the peer before it responds; a one-second wall-clock guard tolerates CI load.
    expected = messenger.client.requester.msg
    assert expected
    received = bytearray()
    deadline = time.monotonic() + 1.0
    while len(received) < len(expected):
        assert select.select(
            [peer],  # Watch for read readiness without consuming bytes.
            [],     # No write-readiness interest.
            [],     # No exceptional-condition interest.
            max(0.0, deadline - time.monotonic()),  # Remaining wall-clock budget.
        )[0]  # An empty readable list means the test guard expired.
        chunk = peer.recv(len(expected) - len(received))
        assert chunk  # EOF before the full request is not successful delivery.
        received.extend(chunk)
    assert received == expected


@pytest.mark.parametrize("scheme", ["http", "https"])
def test_http_messenger_bounds_refused_connection(scheme):
    """Refusal terminates at an absolute scheduler deadline and retains pending work.
    Reserving an unlistened port allows real HIO reopen attempts without a server.
    """
    with habbing.openHab(name="http-refused", temp=True) as (_, hab), socket.socket() as endpoint:
        # Reserve an OS-selected port without listen(): TCP connections are refused.
        endpoint.bind(("127.0.0.1", 0))
        tock = 0.03125  # One tick is 1/32 of a logical scheduler second.
        messenger = agenting.HTTPMessenger(
            hab=hab, wit=hab.pre, url=f"{scheme}://127.0.0.1:{endpoint.getsockname()[1]}",
            connectTimeout=4 * tock)
        messenger.msgs.append(bytearray(hab.makeOwnInception()))
        with openDoist(doers=[messenger], tock=tock, limit=1.0) as doist:
            # responseDo starts its budget during scheduler entry, at this time.
            started = doist.tyme
            connectionDeadline = started + messenger.connectTimeout
            guardDeadline = started + 2 * messenger.connectTimeout  # Eight-tick test guard.
            while not messenger.done and doist.tyme <= guardDeadline:
                doist.recur()  # HIO retries consume the same absolute connection budget.
            assert messenger.done and isinstance(messenger.error, TimeoutError)
            # Timeout is observed at tick 4; recur() advances to tick 5 before returning.
            assert doist.tyme <= connectionDeadline + doist.tock
            assert messenger.pending == 1 and not messenger.idle and not messenger.sent
            assert messenger.client.connector.cs is None and not messenger.deeds


def test_http_messenger_bounds_tls_handshake():
    """A TCP peer that never answers TLS cannot bypass the initial connection budget."""
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)  # The OS can complete TCP even without an application accept().
        tock = 0.03125
        messenger = agenting.HTTPMessenger(
            hab=None, wit="wit", url=f"https://127.0.0.1:{server.getsockname()[1]}",
            connectTimeout=8 * tock)
        with openDoist(doers=[messenger], tock=tock, limit=1.0) as doist:
            started = doist.tyme  # Shared logical clock, not elapsed wall-clock time.
            connectionDeadline = started + messenger.connectTimeout
            guardDeadline = started + 2 * messenger.connectTimeout  # Sixteen-tick test guard.
            accepted = False
            while not messenger.done and doist.tyme <= guardDeadline:
                doist.recur()  # TCP connects, but this raw listener never speaks TLS.
                accepted |= messenger.client.connector.accepted
                time.sleep(0.001)  # Let the OS progress TCP; this is not the TLS deadline.
            assert accepted and messenger.done
            assert isinstance(messenger.error, TimeoutError)
            # The eighth-tick timeout is observed after recur() advances to tick 9.
            assert doist.tyme <= connectionDeadline + doist.tock
            assert messenger.client.connector.cs is None and not messenger.deeds


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_http_messenger_requires_finite_positive_connection_deadline(timeout):
    """Reject connection budgets that cannot bound initial establishment."""
    with pytest.raises(ValueError, match="finite and positive"):
        agenting.HTTPMessenger(hab=None, wit="wit", url="http://127.0.0.1:1",
                               connectTimeout=timeout)


@pytest.mark.parametrize("status", [204, 302, 503])
def test_http_messenger_classifies_real_response(connectedHttpMessenger, status):
    """Only a complete 2xx response clears pending work; redirects are not replayed."""
    messenger, peer, doist, hab = connectedHttpMessenger
    sendHttpRequests(messenger, peer, doist, hab)
    peer.sendall(f"HTTP/1.1 {status} Test\r\nContent-Length: 0\r\nLocation: /elsewhere\r\n\r\n".encode())
    for _ in range(20):
        doist.recur()  # Parse the real HTTP response and apply messenger policy.
        if messenger.sent or messenger.done:
            break
        time.sleep(0.001)
    if status == 204:
        assert messenger.sent.popleft().status == status
        assert messenger.idle and not messenger.failed
        # A subsequent unanswered request is outside the initial connection budget.
        sendHttpRequests(messenger, peer, doist, hab)
        doist.tyme += messenger.connectTimeout + 1.0
        doist.recur()
        assert messenger.pending == 1 and messenger.client.waited and not messenger.failed
    else:
        assert not messenger.sent
        assert messenger.failedResponse.status == status
        assert messenger.done and messenger.failed and not messenger.sent
        assert messenger.pending == 1 and not messenger.idle
        assert messenger.client.connector.cs is None and not messenger.deeds
        assert not messenger.client.redirects


@pytest.mark.parametrize("response, success", [
    (b"HTTP/1.1 200 OK\r\n\r\nclose framed body", True),
    (b"HTTP/1.1 200 OK\r\nContent-Length: 20\r\n\r\nshort", False),
    (b"HTTP/1.1 200 OK\r\nContent-Length:", False),
    (b"", False),
])
def test_http_messenger_settles_response_before_eof(connectedHttpMessenger, response, success):
    """EOF completes close framing but fails truncated or absent HTTP responses.
    A later queued request stays pending even when the first response succeeded.
    """
    messenger, peer, doist, hab = connectedHttpMessenger
    sendHttpRequests(messenger, peer, doist, hab, count=2)
    peer.sendall(response)
    peer.shutdown(socket.SHUT_WR)  # End the response while leaving the peer's read side open.
    for _ in range(20):
        doist.recur()
        if messenger.done:
            break
        time.sleep(0.001)
    assert messenger.done and messenger.failed
    assert messenger.pending == (1 if success else 2) and not messenger.idle
    if success:
        rep = messenger.sent.popleft()
        assert rep.status == 200 and rep.body == b"close framed body" and not rep.errored
        assert messenger.failedResponse is None
    else:
        assert not messenger.sent and messenger.failedResponse.errored
    assert messenger.client.connector.cs is None and not messenger.deeds


def test_http_messenger_retains_send_failure(connectedHttpMessenger):
    """A real broken pipe retains its HIO cause and outstanding request accounting."""
    messenger, _, doist, hab = connectedHttpMessenger
    connector = messenger.client.connector
    # Close the OS send direction without setting HIO's flags. Its next socket
    # send must discover the broken pipe, rather than reject admission artificially.
    connector.cs.shutdown(socket.SHUT_WR)
    messenger.msgs.append(bytearray(hab.makeOwnInception()))
    doist.recur()  # msgDo queues the request; HTTP service admits it and attempts sending.
    assert messenger.done and isinstance(messenger.error, BrokenPipeError)
    assert messenger.error is connector.error and connector.txCutoff
    assert messenger.pending == 1 and not messenger.idle and not messenger.sent
    assert connector.cs is None and not messenger.deeds
    first = messenger.error
    messenger._fail(ConnectionError("later error"))
    assert messenger.error is first


def test_http_messenger_retains_reset_before_transmission(connectedHttpMessenger):
    """An observed peer reset leaves a queued HTTP request untransmitted.
    Real HIO receive service sets the error and flags before HTTP service runs.
    """
    messenger, peer, doist, hab = connectedHttpMessenger
    connector = messenger.client.connector
    messenger.msgs.append(bytearray(hab.makeOwnInception()))
    # An abortive peer close generates RST. No exception or HIO flag is injected.
    peer.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    peer.close()
    assert select.select([connector.cs], [], [], 1.0)[0]  # Bounded OS wait, not scheduler time.
    connector.serviceReceives()
    cause = connector.error
    assert isinstance(cause, ConnectionResetError) and connector.cutoff and connector.txCutoff

    # msgDo encodes the CESR message into an HTTP request. HIO's cutoff branch
    # then skips request transmission; responseDo retains the failure and cleans up.
    doist.recur()
    assert messenger.done and messenger.error is cause
    assert messenger.pending == 1 and len(messenger.client.requests) == 1
    assert not connector.txbs and not messenger.client.waited and not messenger.sent
    assert not messenger.idle and connector.cs is None and not messenger.deeds


def test_http_messenger_keeps_response_before_receive_reset(connectedHttpMessenger):
    """A complete buffered HTTP response remains successful when HIO observes RST.
    Control real socket-service ordering to expose the boundary deterministically;
    no service method, error, or closure flag is patched.
    """
    messenger, peer, doist, hab = connectedHttpMessenger
    sendHttpRequests(messenger, peer, doist, hab, count=2)
    client = messenger.client
    connector = client.connector
    response = b"HTTP/1.1 204 No Content\r\nContent-Length: 0\r\n\r\n"
    peer.sendall(response)

    # Receive the response through HIO without parsing or advancing the messenger.
    # This preserves waited=True, so the next request cannot be transmitted yet.
    deadline = time.monotonic() + 1.0
    while len(connector.rxbs) < len(response):
        assert select.select([connector.cs], [], [], max(0.0, deadline - time.monotonic()))[0]
        connector.serviceReceives()
    assert connector.rxbs == response and client.waited and not client.responses
    assert not messenger.sent

    # Reset only after the full response is buffered, avoiding a packet-arrival race.
    peer.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    peer.close()
    assert select.select([connector.cs], [], [], 1.0)[0]
    assert connector.error is None and not connector.cutoff and not connector.txCutoff

    # HIO observes the real reset, then parses the already-buffered response.
    # The messenger accounts for that success before retaining the transport failure.
    doist.recur()
    assert messenger.done and isinstance(messenger.error, ConnectionResetError)
    assert messenger.error is connector.error and connector.cutoff and connector.txCutoff
    assert messenger.sent.popleft().status == 204 and messenger.failedResponse is None
    assert messenger.pending == 1 and len(client.requests) == 1 and not messenger.idle
    assert connector.cs is None and not messenger.deeds


def test_receiptor_tocks_are_generator_local():
    with habbing.openHby(name="receiptor-generator-tocks", temp=True) as hby:
        receiptor = agenting.Receiptor(hby=hby)
        seen = []

        def receipt(pre, sn=None, auths=None, tock=0.0):
            seen.append(("receipt", tock))
            yield tock

        def get(pre, sn=None, tock=0.0):
            seen.append(("get", tock))
            yield tock

        receiptor.receipt = receipt
        receiptor.get = get
        receiptor.msgs.append({"pre": "witness"})
        receiptor.gets.append({"pre": "query"})

        witness = receiptor.witDo(tymth=lambda: 0.0, tock=0.011)
        query = receiptor.gitDo(tymth=lambda: 0.0, tock=0.013)

        assert next(witness) == 0.011
        assert next(query) == 0.013
        assert next(witness) == 0.011
        assert next(query) == 0.013
        assert seen == [("receipt", 0.011), ("get", 0.013)]

        witness.close()
        query.close()


def test_witness_publisher_idle_tracks_queued_and_active_work(monkeypatch):
    with habbing.openHby(name="publisher-lifecycle", temp=True) as hby:
        wit = hby.makeHab(name="witness", transferable=False)
        hab = hby.makeHab(name="controller", transferable=True,
                          wits=[wit.pre])

        # Replace the HTTP/TCP transport so this test isolates the publisher's
        # child-Doer lifecycle management.
        class FakeMessenger(doing.Doer):
            def __init__(self, wit):
                super().__init__()
                self.wit = wit
                self.msgs = []

            @property
            def idle(self):
                return not self.msgs

        messenger = FakeMessenger(wit.pre)
        monkeypatch.setattr(agenting, "messenger",
                            lambda hab, wit: messenger)

        publisher = agenting.WitnessPublisher(hby=hby)
        evt = dict(pre=hab.pre, said=hab.pre,
                   msg=hab.makeOwnInception())
        publisher.msgs.append(evt)

        # The queued event is pending work before a messenger is scheduled.
        assert not publisher.idle

        doist = doing.Doist(tock=0.03125, limit=1.0,
                            doers=[publisher])
        doist.enter()
        try:
            # The first recurrence transfers the event to an active child.
            doist.recur()
            assert messenger in publisher.witers
            assert not publisher.idle

            # Simulate transport drain so the next recurrence removes the child.
            messenger.msgs.clear()
            doist.recur()

            assert publisher.idle
            assert list(publisher.cues) == [evt]
            assert messenger not in publisher.doers

            # Completion cues are consumable output, not lifecycle state.
            publisher.cues.popleft()
            assert publisher.idle
        finally:
            doist.exit()


def test_witness_receiptor(seeder):
    with habbing.openHby(name="wan", salt=core.Salter(raw=b'wann-the-witness').qb64) as wanHby, \
            habbing.openHby(name="wil", salt=core.Salter(raw=b'will-the-witness').qb64) as wilHby, \
            habbing.openHby(name="wes", salt=core.Salter(raw=b'wess-the-witness').qb64) as wesHby, \
            habbing.openHby(name="pal", salt=core.Salter(raw=b'0123456789abcdef').qb64) as palHby:

        wanDoers = indirecting.setupWitness(alias="wan", hby=wanHby, tcpPort=5632, httpPort=5642)
        wilDoers = indirecting.setupWitness(alias="wil", hby=wilHby, tcpPort=5633, httpPort=5643)
        wesDoers = indirecting.setupWitness(alias="wes", hby=wesHby, tcpPort=5634, httpPort=5644)

        wanHab = wanHby.habByName(name="wan")
        wilHab = wilHby.habByName(name="wil")
        wesHab = wesHby.habByName(name="wes")
        seeder.seedWitEnds(palHby.db, witHabs=[wanHab, wilHab, wesHab], protocols=[kering.Schemes.tcp])

        rctDoer = ReceiptDoer(hby=palHby, wanHab=wanHab, wilHab=wilHab, wesHab=wesHab)

        limit = 5.0
        tock = 0.03125
        doers = wanDoers + wilDoers + wesDoers + [rctDoer]
        doist = doing.Doist(limit=limit, tock=tock, doers=doers)
        doist.enter()
        tymer = tyming.Tymer(tymth=doist.tymen(), duration=doist.limit)

        while not (rctDoer.done or tymer.expired):
            doist.recur()
            time.sleep(doist.tock)

        doist.exit()

        assert rctDoer.done is True


class ReceiptDoer(doing.DoDoer):
    """ Test scenario of witness receipts. """

    def __init__(self, hby, wanHab, wilHab, wesHab):
        self.hby = hby
        self.wanHab = wanHab
        self.wilHab = wilHab
        self.wesHab = wesHab

        super(ReceiptDoer, self).__init__(doers=[doing.doify(self.testDo)])

    def testDo(self, tymth, tock=0.0, **kwa):
        """ Execute a series of kli commands for this test scenario """
        # enter context
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        palHab = self.hby.makeHab(name="pal", wits=[self.wanHab.pre, self.wilHab.pre], transferable=True)

        witDoer = agenting.WitnessReceiptor(hby=self.hby)
        witDoer.msgs.append(dict(pre=palHab.pre))
        self.extend([witDoer])

        kev = palHab.kever
        ser = kev.serder
        dgkey = dbing.dgKey(ser.preb, ser.saidb)

        while True:
            wilWigs = self.wilHab.db.getWigs(dgkey)
            wanWigs = self.wanHab.db.getWigs(dgkey)
            if len(wilWigs) == 2 and len(wanWigs) == 2:
                break
            yield self.tock

        # Controller should send endpoints between witnesses.  Check for Endpoints for each other:
        keys = (self.wanHab.pre, kering.Schemes.tcp)
        said = self.wilHab.db.lans.get(keys=keys)
        assert said is not None
        keys = (self.wilHab.pre, kering.Schemes.tcp)
        said = self.wanHab.db.lans.get(keys=keys)
        assert said is not None

        palHab.rotate(adds=[self.wesHab.pre])

        witDoer.msgs.append(dict(pre=palHab.pre, sn=1))

        kev = palHab.kever
        ser = kev.serder
        dgkey = dbing.dgKey(ser.preb, ser.saidb)

        while True:
            wilWigs = self.wilHab.db.getWigs(dgkey)
            wanWigs = self.wanHab.db.getWigs(dgkey)
            wesWigs = self.wesHab.db.getWigs(dgkey)
            if len(wilWigs) == 3 and len(wanWigs) == 3 and len(wesWigs) == 3:
                break
            yield self.tock

        self.remove([witDoer])
        return True


def test_witness_sender(seeder):
    with habbing.openHby(name="wan", salt=core.Salter(raw=b'wann-the-witness').qb64) as wanHby, \
            habbing.openHby(name="wil", salt=core.Salter(raw=b'will-the-witness').qb64) as wilHby, \
            habbing.openHby(name="wes", salt=core.Salter(raw=b'wess-the-witness').qb64) as wesHby, \
            habbing.openHby(name="pal", salt=core.Salter(raw=b'0123456789abcdef').qb64) as palHby:

        # looks like bad magic value in seeder is causing this to fail
        pdoer = PublishDoer(wanHby, wilHby, wesHby, palHby, seeder)
        directing.runController(doers=[pdoer], expire=10.0)
        assert pdoer.done is True


class PublishDoer(doing.DoDoer):

    def __init__(self, wanHby, wilHby, wesHby, palHby, seeder):
        wanDoers = indirecting.setupWitness(alias="wan", hby=wanHby, tcpPort=5632, httpPort=5642)
        wilDoers = indirecting.setupWitness(alias="wil", hby=wilHby, tcpPort=5633, httpPort=5643)
        wesDoers = indirecting.setupWitness(alias="wes", hby=wesHby, tcpPort=5634, httpPort=5644)
        # Pull the regers out of the Doers so the regers are reused and do not trigger an LMDB error on reuse
        self.regers = dict(
            wan=next(doer.baser for doer in wanDoers if isinstance(doer, basing.BaserDoer)),
            wil=next(doer.baser for doer in wilDoers if isinstance(doer, basing.BaserDoer)),
            wes=next(doer.baser for doer in wesDoers if isinstance(doer, basing.BaserDoer)),
        )

        wanHab = wanHby.habByName(name="wan")
        wilHab = wilHby.habByName(name="wil")
        wesHab = wesHby.habByName(name="wes")
        seeder.seedWitEnds(palHby.db, witHabs=[wanHab, wilHab, wesHab], protocols=[kering.Schemes.tcp])

        self.palHab = palHby.makeHab(name="pal", wits=[wanHab.pre, wilHab.pre, wesHab.pre], transferable=True)

        self.witDoer = agenting.WitnessPublisher(hby=palHby)
        doers = wanDoers + wilDoers + wesDoers + [self.witDoer]
        self.toRemove = list(doers)
        doers.extend([doing.doify(self.testDo)])

        super(PublishDoer, self).__init__(doers=doers)

    def testDo(self, tymth, tock=0.0, **kwa):
        """ Run the test and exit and remove all child doers when done """
        self.wind(tymth)
        self.tock = tock
        yield self.tock

        regser = eventing.incept(pre=self.palHab.pre, baks=[], code=coring.MtrDex.Blake3_256)
        serder = eventing.issue(vcdig=regser.pre,
                                regk="EbA1o_bItVC9i6YB3hr2C3I_Gtqvz02vCmavJNoBA3Jg")
        msg = bytearray(serder.raw)
        msg.extend(core.Counter(core.Codens.SealSourceCouples, count=1,
                                gvrsn=kering.Vrsn_1_0).qb64b)
        msg.extend(Seqner(sn=self.palHab.kever.sn).qb64b)
        msg.extend(self.palHab.kever.serder.saidb)

        self.witDoer.msgs.append(dict(pre=self.palHab.pre, msg=msg))

        while not self.witDoer.cues:
            yield self.tock

        cue = self.witDoer.cues.popleft()
        assert cue["pre"] == self.palHab.pre
        assert cue["msg"] == msg

        for name in ["wes", "wil", "wan"]:
            reger = self.regers[name]
            while True:
                raw = reger.getTvt(dbing.dgKey(serder.preb, serder.saidb))
                if raw:
                    found = serdering.SerderKERI(raw=bytes(raw))
                    if found and serder.pre == found.pre:
                        break
                yield self.tock

        self.remove(self.toRemove)
        return True


def test_witness_inquisitor(mockHelpingNowUTC, seeder):
    with habbing.openHby(name="wan", salt=core.Salter(raw=b'wann-the-witness').qb64) as wanHby, \
            habbing.openHby(name="wil", salt=core.Salter(raw=b'will-the-witness').qb64) as wilHby, \
            habbing.openHby(name="wes", salt=core.Salter(raw=b'wess-the-witness').qb64) as wesHby, \
            habbing.openHby(name="pal", salt=core.Salter(raw=b'0123456789abcdef').qb64) as palHby, \
            habbing.openHby(name="qin", salt=core.Salter(raw=b'abcdef0123456789').qb64) as qinHby:
        wanDoers = indirecting.setupWitness(alias="wan", hby=wanHby, tcpPort=5632, httpPort=5642)
        wilDoers = indirecting.setupWitness(alias="wil", hby=wilHby, tcpPort=5633, httpPort=5643)
        wesDoers = indirecting.setupWitness(alias="wes", hby=wesHby, tcpPort=5634, httpPort=5644)

        wanHab = wanHby.habByName(name="wan")
        wilHab = wilHby.habByName(name="wil")
        wesHab = wesHby.habByName(name="wes")
        seeder.seedWitEnds(palHby.db, witHabs=[wanHab, wilHab, wesHab], protocols=[kering.Schemes.tcp])
        seeder.seedWitEnds(qinHby.db, witHabs=[wanHab, wilHab, wesHab], protocols=[kering.Schemes.tcp])

        palHab = palHby.makeHab(name="pal", wits=[wanHab.pre, wilHab.pre, wesHab.pre], transferable=True)
        qinHab = qinHby.makeHab(name="qin", wits=[wanHab.pre, wilHab.pre, wesHab.pre], transferable=True)

        palWitDoer = agenting.WitnessReceiptor(hby=palHby)
        palWitDoer.msgs.append(dict(pre=palHab.pre))
        qinWitDoer = agenting.WitnessReceiptor(hby=qinHby)
        qinWitDoer.msgs.append(dict(pre=qinHab.pre))

        qinWitq = agenting.WitnessInquisitor(hby=qinHby)
        # query up a few to make sure it still works
        stamp = nowIso8601()  # need same time stamp or not duplicate
        qinWitq.query(src=qinHab.pre, pre=palHab.pre, stamp=stamp, wits=palHab.kever.wits)
        qinWitq.query(src=qinHab.pre, pre=palHab.pre, stamp=stamp, wits=palHab.kever.wits)
        qinWitq.query(src=qinHab.pre, pre=palHab.pre, stamp=stamp, wits=palHab.kever.wits)
        palWitq = agenting.WitnessInquisitor(hby=palHby)
        palWitq.query(src=palHab.pre, pre=qinHab.pre, stamp=stamp, wits=qinHab.kever.wits)

        limit = 5.0
        tock = 0.03125
        doist = doing.Doist(limit=limit, tock=tock)
        doers = wanDoers + wilDoers + wesDoers + [palWitDoer, qinWitDoer]
        doist.do(doers=doers)

        for hab in [palHab, qinHab]:
            kev = hab.kever
            ser = kev.serder
            dgkey = dbing.dgKey(ser.preb, ser.saidb)

            wigs = wanHab.db.getWigs(dgkey)
            assert len(wigs) == 3
            wigs = wilHab.db.getWigs(dgkey)
            assert len(wigs) == 3
            wigs = wesHab.db.getWigs(dgkey)
            assert len(wigs) == 3

        doist = doing.Doist(limit=limit, tock=tock)
        doers = wanDoers + wilDoers + wesDoers + [qinWitq, palWitq]
        doist.do(doers=doers)

        assert palHab.pre in qinHab.kevers
        assert qinHab.pre in palHab.kevers
