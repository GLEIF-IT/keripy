"""Incomplete attachment groups yield control without losing valid resumed evidence."""

import multiprocessing

import pytest

from keri import core, kering
from keri.core import eventing, parsing
from keri.core.counting import CtrDex_1_0
from keri.db import basing, dbing


def _resume_receipt(missing):
    """Run a real KEL/receipt round trip in a child that the parent can stop if parsing hangs."""
    controller = core.Signer(transferable=False)
    receipter = core.Signer(transferable=False)
    event = eventing.incept(keys=[controller.verfer.qb64])
    signature = controller.sign(event.raw, index=0)
    receipt = receipter.sign(event.raw)
    stream = bytearray(event.raw)
    stream.extend(core.Counter(core.Codens.ControllerIdxSigs, gvrsn=kering.Vrsn_1_0).qb64b)
    stream.extend(signature.qb64b)
    stream.extend(core.Counter(core.Codens.NonTransReceiptCouples, gvrsn=kering.Vrsn_1_0).qb64b)
    remaining = receipter.verfer.qb64b + receipt.qb64b
    if missing == "cigar":
        stream.extend(receipter.verfer.qb64b)
        remaining = receipt.qb64b

    with basing.openDB(name="receipt-shortage", temp=True) as db:
        kvy = eventing.Kevery(db=db)
        parser = parsing.Parser(kvy=kvy).onceParsator(ims=stream, framed=True, local=False)
        try:
            assert next(parser) is None  # Waiting must reach the caller, not spin inside a helper.
            assert event.pre not in kvy.kevers
            stream.extend(remaining)
            with pytest.raises(StopIteration):
                next(parser)
            assert kvy.kevers[event.pre].serder.said == event.said
            assert db.getRcts(dbing.dgKey(event.pre, event.said)) == [
                receipter.verfer.qb64b + receipt.qb64b
            ]
        finally:
            parser.close()


@pytest.mark.parametrize("missing", ["verfer", "cigar"])
def test_receipt_shortage_yields_and_resumes(missing):
    """Missing receipt material yields; supplying it later preserves KEL and receipt acceptance."""
    process = multiprocessing.get_context("spawn").Process(target=_resume_receipt, args=(missing,))
    process.start()
    try:
        process.join(timeout=10)
        assert not process.is_alive(), "receipt shortage blocked the parser instead of yielding"
        assert process.exitcode == 0
    finally:
        if process.is_alive():
            process.kill()
        process.join()
        process.close()


def test_sad_path_receipt_shortage_yields_before_returning_groups():
    """Nested SAD-path extraction yields only waiting signals and returns complete signature groups."""
    signer = core.Signer(transferable=False)
    body = eventing.incept(keys=[signer.verfer.qb64]).raw
    cigar = signer.sign(body)
    path = core.Pather(path=["a"])
    stream = bytearray(path.qb64b + core.Counter(core.Codens.NonTransReceiptCouples, gvrsn=kering.Vrsn_1_0).qb64b
                       + signer.verfer.qb64b)
    parser = parsing.Parser()._sadPathSigGroup(core.Counter(core.Codens.SadPathSigGroups, gvrsn=kering.Vrsn_1_0), stream)
    assert next(parser) is None
    stream.extend(cigar.qb64b)
    with pytest.raises(StopIteration) as completed:
        next(parser)
    [(code, (subpath, received))] = completed.value.value
    assert code == CtrDex_1_0.NonTransReceiptCouples
    assert subpath.path == path.path
    assert received.verfer.qb64 == signer.verfer.qb64
    assert received.verfer.verify(received.raw, body)


def test_counted_receipt_frame_still_aborts_on_shortage():
    """An already collected counted frame cannot wait for bytes outside that frame."""
    parser = parsing.Parser()._nonTransReceiptCouples(
        core.Counter(core.Codens.NonTransReceiptCouples, gvrsn=kering.Vrsn_1_0), bytearray(), pipelined=True
    )
    with pytest.raises(kering.ShortageError):
        next(parser)
