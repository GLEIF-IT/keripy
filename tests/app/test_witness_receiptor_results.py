"""WitnessReceiptor contracts using real habitats, receipts, and HIO failures."""

from contextlib import contextmanager
import socket
import time

import pytest

from keri import kering
from keri.app import agenting, habbing
from tests.support.scheduling import openDoist


@contextmanager
def receiptHabitats():
    """Own a controller and a nontransferable witness without opening a server."""
    with (
        habbing.openHby(name="receipt-controller", temp=True) as hby,
        habbing.openHab(name="receipt-witness", temp=True, transferable=False) as (_, witness),
    ):
        hab = hby.makeHab(name="controller", wits=[witness.pre])
        yield hby, hab, witness


def storeReceipt(hab, witness):
    """Sign an actual event as its witness and verify the receipt through the parser."""
    witness.psr.parse(ims=bytearray(hab.makeOwnInception()))
    hab.psr.parse(ims=bytearray(witness.witness(hab.kever.serder)))


def setEndpoint(hab, witness, endpoint, scheme="tcp"):
    """Publish the witness's signed endpoint to the controller's database."""
    url = f"{scheme}://127.0.0.1:{endpoint.getsockname()[1]}"
    hab.psr.parse(ims=bytearray(witness.makeLocScheme(url=url, scheme=scheme)))


def waitForResult(owner, doist):
    """Drive real socket work with a logical guard beyond the initial connect budget."""
    deadline = doist.tyme + 32.0
    while not owner.results:
        assert doist.tyme < deadline, "receipt attempt did not finish"
        doist.recur()
        time.sleep(0.001)  # Allow the OS to deliver connection refusal and socket I/O.
    return owner.results.popleft()


def test_receipt_results_correlate_repeated_completed_requests():
    """Repeated event keys get distinct tokens without creating no-work children."""
    with receiptHabitats() as (hby, hab, witness):
        storeReceipt(hab, witness)
        owner = agenting.WitnessReceiptor(hby=hby)
        tokens = [owner.submit(hab.pre, sn=0), owner.submit(hab.pre, sn=0)]
        with openDoist(doers=[owner], tock=0.03125, limit=1.0) as doist:
            results = [waitForResult(owner, doist), waitForResult(owner, doist)]
            assert [result.token for result in results] == tokens and tokens[0] != tokens[1]
            assert all(result.receiptsComplete and not result.errors for result in results)
            assert all(result.sn == 0 and result.said == hab.pre for result in results)
            assert len(owner.doers) == 1  # Only the owner loop, with no messenger children.
            assert len(owner.cues) == 2
            owner.cues.clear()
            assert not owner.msgs


def test_receipt_result_uses_requested_event_witnesses():
    """A later witness removal must not change the result for the inception event."""
    with receiptHabitats() as (hby, hab, witness):
        storeReceipt(hab, witness)
        hab.rotate(cuts=[witness.pre], toad=0)
        owner = agenting.WitnessReceiptor(hby=hby)
        owner.submit(hab.pre, sn=0)
        with openDoist(doers=[owner], tock=0.03125, limit=1.0) as doist:
            result = waitForResult(owner, doist)
            assert result.witnesses == result.receipts == (witness.pre,)
            assert result.threshold == 1 and result.thresholdMet
            assert not hab.kever.wits


def test_receipt_result_without_witnesses():
    """Zero-witness work yields a correlated no-work result but no legacy cue."""
    with habbing.openHab(name="no-witness", temp=True) as (hby, hab):
        owner = agenting.WitnessReceiptor(hby=hby)
        token = owner.submit(hab.pre)
        with openDoist(doers=[owner], tock=0.03125, limit=1.0) as doist:
            result = waitForResult(owner, doist)
            assert result.token == token and result.sn == 0
            assert result.threshold == 0 and result.propagationComplete
            assert not result.witnesses and not owner.cues and len(owner.doers) == 1


def test_forced_receipt_result_retains_verified_receipt_on_missing_endpoint():
    """Forced propagation reports endpoint failure without erasing verified receipts."""
    with receiptHabitats() as (hby, hab, witness):
        storeReceipt(hab, witness)
        owner = agenting.WitnessReceiptor(hby=hby, force=True)
        owner.submit(hab.pre)
        with openDoist(doers=[owner], tock=0.03125, limit=1.0) as doist:
            result = waitForResult(owner, doist)
            assert result.receiptsComplete and not result.propagationComplete
            assert isinstance(result.errors[witness.pre], kering.ConfigurationError)
            assert not owner.cues and len(owner.doers) == 1


@pytest.mark.parametrize("scheme", ["tcp", "http"])
def test_receipt_result_retains_refused_connection(scheme):
    """A real refused endpoint terminates the attempt and releases its failed child."""
    with receiptHabitats() as (hby, hab, witness), socket.socket() as endpoint:
        endpoint.bind(("127.0.0.1", 0))  # Reserve a port without listening for connections.
        setEndpoint(hab, witness, endpoint, scheme=scheme)
        owner = agenting.WitnessReceiptor(hby=hby)
        owner.submit(hab.pre)
        with openDoist(doers=[owner], tock=0.03125, limit=33.0) as doist:
            result = waitForResult(owner, doist)
            assert isinstance(result.errors[witness.pre], TimeoutError)
            assert not result.thresholdMet and not result.receipts and not owner.cues
            assert len(owner.doers) == 1


@pytest.mark.parametrize("invalidRequest", [dict(pre="unknown"), dict(sn=-1), dict(sn=100)],
                         ids=["unknown-habitat", "negative-sequence", "missing-event"])
def test_receipt_result_rejects_invalid_request(invalidRequest):
    """Bad local requests produce a terminal result instead of stopping the owner."""
    with habbing.openHab(name="bad-receipt-request", temp=True) as (hby, hab):
        evt = dict(pre=hab.pre, **invalidRequest) if "pre" not in invalidRequest else invalidRequest
        owner = agenting.WitnessReceiptor(hby=hby)
        owner.msgs.append(evt)  # Legacy queue admission also receives an attempt token.
        with openDoist(doers=[owner], tock=0.03125, limit=1.0) as doist:
            result = waitForResult(owner, doist)
            assert result.token and result.error is not None
            assert not result.thresholdMet and not owner.cues and len(owner.doers) == 1


def test_receipt_result_observes_receipt_before_classifying_transport_failure():
    """A separately delivered receipt can satisfy the event as its send attempt fails."""
    with receiptHabitats() as (hby, hab, witness), socket.socket() as endpoint:
        endpoint.bind(("127.0.0.1", 0))
        setEndpoint(hab, witness, endpoint)
        owner = agenting.WitnessReceiptor(hby=hby)
        owner.submit(hab.pre)
        with openDoist(doers=[owner], tock=0.03125, limit=33.0) as doist:
            doist.recur()  # Admit the request and schedule its real TCP messenger.
            child = next(doer for doer in owner.doers if isinstance(doer, agenting.TCPMessenger))
            doist.recur()  # Start the child's initial connection budget.
            assert child.client is not None and not owner.results and not child.failed

            # Like mailbox delivery, verified receipt processing is independent of
            # this connection. The next scheduler turn also expires the connection
            # budget, so both facts are available when the owner judges the attempt.
            storeReceipt(hab, witness)
            doist.tyme += child.connectTimeout + doist.tock
            doist.recur()
            assert child.failed and owner.results
            result = owner.results.popleft()
            assert result.receiptsComplete and result.thresholdMet
            assert result.errors[witness.pre] is child.error
            assert not result.propagationComplete and not owner.cues
            assert child not in owner.doers and child.client.cs is None


def test_receipt_attempt_cancellation_closes_owned_connection():
    """Stopping an owner waiting for a receipt closes its real connected child."""
    with receiptHabitats() as (hby, hab, witness), socket.socket() as endpoint:
        endpoint.bind(("127.0.0.1", 0))
        endpoint.listen(1)  # A bare peer accepts the request but supplies no receipt.
        setEndpoint(hab, witness, endpoint)
        owner = agenting.WitnessReceiptor(hby=hby)
        owner.submit(hab.pre)
        with openDoist(doers=[owner], tock=0.03125, limit=2.0) as doist:
            doist.recur()
            child = next(doer for doer in owner.doers if isinstance(doer, agenting.TCPMessenger))
            deadline = time.monotonic() + 1.0
            while child.client is None or not child.client.connected:
                assert time.monotonic() < deadline, "peer connection did not complete"
                doist.recur()
                time.sleep(0.001)
            peer, _ = endpoint.accept()
            with peer:
                assert not owner.results and not child.failed
        assert child.client.cs is None and child not in owner.doers
        assert not owner.results  # Cancellation is not a completed receipt attempt.


def test_receipt_result_separates_threshold_from_missing_replication():
    """One verified receipt can meet threshold while another witness has no endpoint."""
    with (
        habbing.openHby(name="threshold-controller", temp=True) as hby,
        habbing.openHab(name="available-witness", temp=True, transferable=False) as (_, witness),
        habbing.openHab(name="missing-witness", temp=True, transferable=False) as (_, missing),
        socket.socket() as endpoint,
    ):
        hab = hby.makeHab(name="controller", wits=[witness.pre, missing.pre], toad=1)
        storeReceipt(hab, witness)
        endpoint.bind(("127.0.0.1", 0))
        endpoint.listen(1)
        setEndpoint(hab, witness, endpoint)
        owner = agenting.WitnessReceiptor(hby=hby)
        owner.submit(hab.pre)
        with openDoist(doers=[owner], tock=0.03125, limit=1.0) as doist:
            doist.recur()  # The first witness has a child; the second cannot be routed.
            child = next(doer for doer in owner.doers if isinstance(doer, agenting.TCPMessenger))
            result = waitForResult(owner, doist)
            assert result.threshold == 1 and result.thresholdMet
            assert result.receipts == (witness.pre,) and not result.receiptsComplete
            assert isinstance(result.errors[missing.pre], kering.ConfigurationError)
            assert not result.propagationComplete and not owner.cues
            assert child not in owner.doers and child.client.cs is None


@pytest.mark.parametrize("scheme", ["tcp", "http"])
def test_receipt_result_retains_invalid_endpoint(scheme):
    """Malformed port configuration must reach the owner, even with deferred TCP setup."""
    with receiptHabitats() as (hby, hab, witness):
        endpoint = witness.makeLocScheme(url=f"{scheme}://127.0.0.1:invalid", scheme=scheme)
        hab.psr.parse(ims=bytearray(endpoint))
        owner = agenting.WitnessReceiptor(hby=hby)
        owner.submit(hab.pre)
        with openDoist(doers=[owner], tock=0.03125, limit=1.0) as doist:
            result = waitForResult(owner, doist)
            assert isinstance(result.errors[witness.pre], ValueError)
            assert not result.thresholdMet and not owner.cues
            assert len(owner.doers) == 1
