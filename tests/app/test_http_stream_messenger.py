"""Single-PUT messenger outcomes over real HTTP and TLS connections."""

from contextlib import contextmanager
import select
import socket
import ssl
import struct
import time

import pytest

from hio.core.http import httping

from keri.app import agenting, habbing
from tests.support.scheduling import openDoist


@contextmanager
def openStreamPeer(*, msg=None, tlsFiles=None):
    """Connect a stream messenger to a controllable server socket, without answering.

    The server stands in for a witness transport. Tests supply its responses and
    closure timing; no HTTP service method, exception or HIO flag is patched.
    """
    useTls = tlsFiles is not None
    scheme = "https" if useTls else "http"
    if useTls:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = context.maximum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(tlsFiles["certpath"], tlsFiles["keypath"])
    with habbing.openHab(name="http-stream-outcome", temp=True) as (_, hab), socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        server.setblocking(False)
        msg = hab.makeOwnInception() if msg is None else msg
        messenger = agenting.streamMessengerFrom(
            hab=hab, pre=hab.pre, urls={scheme: f"{scheme}://127.0.0.1:{server.getsockname()[1]}"},
            msg=msg, headers={"X-Test-Stream": "preserved"})
        if useTls:
            messenger.client.connector.context.load_verify_locations(tlsFiles["cafilepath"])
        # Entry opens the socket and starts the budget; recur drives TCP/TLS and the PUT.
        with openDoist(doers=[messenger], tock=0.03125, limit=1.0) as doist:
            peer = None
            try:
                deadline = time.monotonic() + 1.0  # Fixture guard, not a messenger timeout.
                while peer is None or not messenger.client.connector.connected:
                    if time.monotonic() >= deadline:
                        pytest.fail("HTTP stream fixture connection setup timed out")
                    doist.recur()
                    if peer is None:
                        try:
                            peer, _ = server.accept()
                            peer.setblocking(False)
                            if useTls:
                                peer = context.wrap_socket(peer, server_side=True, do_handshake_on_connect=False)
                        except BlockingIOError:
                            pass
                    if useTls and peer is not None:
                        try:
                            peer.do_handshake()  # The fixture drives the server half of TLS setup.
                        except (ssl.SSLWantReadError, ssl.SSLWantWriteError):
                            pass
                    time.sleep(0.001)
                yield messenger, peer, doist
            finally:
                if peer is not None:
                    peer.close()


@pytest.fixture
def connectedHttpStreamMessenger(request, witnessTlsFiles):
    """Yield a messenger and peer; pytest's indirect request.param selects TLS.

    request is pytest's fixture context, not an HTTP request. True selects TLS;
    omission or False selects HTTP. witnessTlsFiles supplies temporary server
    credentials and client trust through tests/app/conftest.py.
    """
    useTls = getattr(request, "param", False)
    with openStreamPeer(tlsFiles=witnessTlsFiles if useTls else None) as connected:
        yield connected


def receiveStreamRequest(messenger, peer, doist):
    """Verify the complete PUT at the peer before allowing a test response."""
    deadline = time.monotonic() + 1.0
    while messenger.client.connector.txbs or not messenger.client.waited:
        if time.monotonic() >= deadline:
            pytest.fail("HTTP stream request transmission timed out")
        doist.recur()
        time.sleep(0.001)
    expected = messenger.client.requester.msg
    assert expected
    received = bytearray()
    while len(received) < len(expected):
        # Read readiness does not promise the entire request; accumulate partial reads.
        assert select.select([peer], [], [], max(0.0, deadline - time.monotonic()))[0]
        chunk = peer.recv(len(expected) - len(received))
        assert chunk
        received.extend(chunk)
    assert received == expected
    return received


def finishStream(messenger, doist):
    """Drive ordinary messenger service to completion with a wall-clock test guard."""
    deadline = time.monotonic() + 1.0
    while not messenger.done:
        if time.monotonic() >= deadline:
            pytest.fail("HTTP stream messenger did not finish")
        doist.recur()
        time.sleep(0.001)


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_stream_requires_finite_positive_connection_deadline(timeout):
    """Reject connection budgets that cannot bound initial establishment."""
    with pytest.raises(ValueError, match="finite and positive"):
        agenting.HTTPStreamMessenger(hab=None, wit="wit", url="http://127.0.0.1:1",
                                     connectTimeout=timeout)


@pytest.mark.parametrize("scheme", ["http", "https"])
def test_stream_bounds_refused_connection(scheme):
    """Refusal consumes one absolute connection budget, with no response invented."""
    with socket.socket() as endpoint:
        endpoint.bind(("127.0.0.1", 0))  # Reserve a port without listening: connections are refused.
        tock = 0.03125
        messenger = agenting.HTTPStreamMessenger(
            hab=None, wit="wit", url=f"{scheme}://127.0.0.1:{endpoint.getsockname()[1]}",
            msg=b"untransmitted", connectTimeout=4 * tock)
        with openDoist(doers=[messenger], tock=tock, limit=1.0) as doist:
            started = doist.tyme  # Entry starts the deadline on this logical clock.
            while not messenger.done and doist.tyme <= started + 8 * tock:
                doist.recur()
            assert messenger.done and isinstance(messenger.error, TimeoutError)
            assert doist.tyme <= started + messenger.connectTimeout + tock
            assert messenger.rep is None and messenger.failed
            assert messenger.client.connector.cs is None and not messenger.deeds


def test_stream_bounds_tls_handshake():
    """Completing TCP without a TLS answer cannot bypass the connection deadline."""
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)  # The kernel completes TCP; this stand-in server never answers TLS.
        tock = 0.03125
        messenger = agenting.HTTPStreamMessenger(
            hab=None, wit="wit", url=f"https://127.0.0.1:{server.getsockname()[1]}",
            connectTimeout=8 * tock)
        with openDoist(doers=[messenger], tock=tock, limit=1.0) as doist:
            started = doist.tyme
            tcpConnected = False
            while not messenger.done and doist.tyme <= started + 16 * tock:
                doist.recur()
                tcpConnected = tcpConnected or messenger.client.connector.accepted
                time.sleep(0.001)
            assert tcpConnected and messenger.done and isinstance(messenger.error, TimeoutError)
            assert doist.tyme <= started + messenger.connectTimeout + tock
            assert messenger.rep is None and messenger.client.connector.cs is None and not messenger.deeds


# The indirect column selects the fixture transport; closeFramed passes to the test.
@pytest.mark.parametrize("connectedHttpStreamMessenger, closeFramed", [
    pytest.param(False, False, id="http-204"),
    pytest.param(True, False, id="tls12-204"),
    pytest.param(False, True, id="http-eof-body"),
], indirect=["connectedHttpStreamMessenger"])
def test_stream_completes_successful_put(connectedHttpStreamMessenger, closeFramed):
    """Preserve PUT payload/headers, capture a successful response, and close the child."""
    messenger, peer, doist = connectedHttpStreamMessenger
    received = receiveStreamRequest(messenger, peer, doist)
    headers, body = received.split(b"\r\n\r\n", 1)
    assert headers.startswith(b"PUT / HTTP/1.1\r\n")
    fields = dict(line.split(b": ", 1) for line in bytes(headers).split(b"\r\n")[1:])
    assert fields[b"Content-Type"] == b"application/cesr"
    assert fields[b"Cesr-Destination"] == messenger.wit.encode()
    assert fields[b"X-Test-Stream"] == b"preserved"
    assert int(fields[b"Content-Length"]) == len(body)
    assert body == messenger.hab.makeOwnInception()
    if closeFramed:
        peer.sendall(b"HTTP/1.1 200 OK\r\n\r\ncomplete")
        peer.shutdown(socket.SHUT_WR)  # The server's EOF supplies the response body boundary.
    else:
        peer.sendall(b"HTTP/1.1 204 No Content\r\nContent-Length: 0\r\n\r\n")
    finishStream(messenger, doist)
    assert messenger.rep.status == (200 if closeFramed else 204) and not messenger.rep.errored
    assert messenger.rep.body == (b"complete" if closeFramed else b"")
    assert not messenger.failed and messenger.error is None
    assert messenger.client.connector.cs is None and not messenger.deeds


@pytest.mark.parametrize("status", [302, 503], ids=["redirect", "server-error"])
def test_stream_retains_rejected_response(connectedHttpStreamMessenger, status):
    """Retain the rejected response and error without following a redirect or replaying."""
    messenger, peer, doist = connectedHttpStreamMessenger
    receiveStreamRequest(messenger, peer, doist)
    peer.sendall(f"HTTP/1.1 {status} Test\r\nContent-Length: 0\r\nLocation: /elsewhere\r\n\r\n".encode())
    finishStream(messenger, doist)
    assert messenger.rep.status == status and not messenger.rep.errored
    assert messenger.failed and isinstance(messenger.error, httping.HTTPException)
    assert not messenger.client.redirects and not messenger.client.requests
    assert messenger.client.connector.cs is None and not messenger.deeds


@pytest.mark.parametrize("response", [
    b"", b"HTTP/1.1 200 OK\r\nContent-Length: 20\r\n\r\nshort",
], ids=["absent", "truncated-body"])
def test_stream_fails_incomplete_response(connectedHttpStreamMessenger, response):
    """Server EOF before a complete response is a failure, even with a 200 header."""
    messenger, peer, doist = connectedHttpStreamMessenger
    receiveStreamRequest(messenger, peer, doist)
    peer.sendall(response)
    peer.shutdown(socket.SHUT_WR)  # The stand-in server ends an unfinished response.
    finishStream(messenger, doist)
    assert messenger.rep.errored and messenger.failed
    assert isinstance(messenger.error, httping.HTTPException)
    assert messenger.client.connector.cs is None and not messenger.deeds


def test_stream_connection_deadline_ends_after_connect(connectedHttpStreamMessenger):
    """An established PUT may wait beyond the initial connection budget for its response."""
    messenger, peer, doist = connectedHttpStreamMessenger
    receiveStreamRequest(messenger, peer, doist)  # The server deliberately leaves the PUT unanswered.
    doist.tyme += messenger.connectTimeout + 1.0
    doist.recur()
    assert not messenger.done and not messenger.failed and messenger.rep is None
    assert messenger.client.waited


def test_stream_cancellation_closes_client(connectedHttpStreamMessenger):
    """Removing an unanswered messenger closes its socket and scheduled child."""
    messenger, peer, doist = connectedHttpStreamMessenger
    receiveStreamRequest(messenger, peer, doist)
    doist.remove([messenger])  # The owner cancels the attempt rather than inventing a transport failure.
    assert messenger.client.connector.cs is None and not messenger.deeds
    assert messenger.rep is None and not messenger.failed


def test_stream_retains_reset_during_send():
    """A peer reset while a large PUT is still buffered ends the attempt with its cause."""
    # A batch can exceed socket buffering. Do not drain the peer before aborting it.
    with openStreamPeer(msg=b"x" * (8 * 1024 * 1024)) as (messenger, peer, doist):
        connector = messenger.client.connector
        assert connector.txbs and messenger.client.waited
        peer.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
        peer.close()  # Abort the server while the client still has bytes to transmit.
        assert select.select([connector.cs], [], [], 1.0)[0]
        finishStream(messenger, doist)
        assert messenger.failed and isinstance(messenger.error, OSError)
        assert messenger.error is connector.error and connector.txbs
        assert connector.cs is None and not messenger.deeds


def test_stream_keeps_response_before_receive_reset(connectedHttpStreamMessenger):
    """A buffered success remains inspectable when the same service turn observes reset."""
    messenger, peer, doist = connectedHttpStreamMessenger
    receiveStreamRequest(messenger, peer, doist)
    connector = messenger.client.connector
    response = b"HTTP/1.1 204 No Content\r\nContent-Length: 0\r\n\r\n"
    peer.sendall(response)
    # Hold the complete bytes before parsing so success and reset are judged in one turn.
    deadline = time.monotonic() + 1.0
    while len(connector.rxbs) < len(response):
        assert select.select([connector.cs], [], [], max(0.0, deadline - time.monotonic()))[0]
        connector.serviceReceives()
    assert connector.rxbs == response and messenger.rep is None
    peer.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    peer.close()  # The server aborts after its complete response has reached the client.
    assert select.select([connector.cs], [], [], 1.0)[0]
    doist.recur()
    assert messenger.done and messenger.rep.status == 204 and not messenger.rep.errored
    assert messenger.failed and isinstance(messenger.error, ConnectionResetError)
    assert messenger.error is connector.error
    assert connector.cs is None and not messenger.deeds


def test_stream_receives_after_clean_send_close(connectedHttpStreamMessenger):
    """Contract: a fully sent PUT can finish receiving after external send shutdown.
    Ordinary HTTPStreamMessenger processing does not initiate this half-close.
    """
    messenger, peer, doist = connectedHttpStreamMessenger
    receiveStreamRequest(messenger, peer, doist)
    messenger.client.connector.shutdownSend()  # Real local half-close with receive still open.
    doist.recur()  # Without a response yet, clean send closure must not end the attempt.
    assert not messenger.done and not messenger.failed and messenger.rep is None
    assert messenger.client.waited
    peer.sendall(b"HTTP/1.1 204 No Content\r\nContent-Length: 0\r\n\r\n")
    finishStream(messenger, doist)
    assert messenger.rep.status == 204 and not messenger.failed
    assert messenger.client.connector.cs is None and not messenger.deeds
