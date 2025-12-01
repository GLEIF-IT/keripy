# -*- encoding: utf-8 -*-
"""
tests.app.test_tocking module

Tests for tocking module - centralized tock configuration.
"""
import os
import importlib


def test_tocking_defaults():
    """Test that tocking module loads with expected default values"""
    from keri.app import tocking

    assert tocking.WitnessMsgTock == 0.0
    assert tocking.WitnessEscrowTock == 1.0
    assert tocking.WitnessCueTock == 0.25
    assert tocking.IndirectorMsgTock == 0.0
    assert tocking.IndirectorCueTock == 0.25
    assert tocking.IndirectorEscrowTock == 1.0
    assert tocking.MailboxPollTock == 0.5
    assert tocking.MailboxMsgTock == 0.0
    assert tocking.MailboxEscrowTock == 1.0
    assert tocking.PollerEventTock == 0.5
    assert tocking.ReceiptInterceptTock == 0.1
    assert tocking.ReactorMsgTock == 0.0
    assert tocking.ReactorCueTock == 0.25
    assert tocking.ReactorEscrowTock == 1.0
    assert tocking.ReactantMsgTock == 0.0
    assert tocking.ReactantCueTock == 0.25
    assert tocking.ReactantEscrowTock == 1.0
    assert tocking.RespondantCueTock == 0.25
    assert tocking.WitnessReceiptorTock == 0.0
    assert tocking.WitnessInquisitorTock == 1.0
    assert tocking.WitnessPublisherTock == 0.25


def test_tocking_env_override():
    from keri.app import tocking

    # Set env var and reimport to test override
    test_value = "2.5"
    os.environ[tocking.KERI_WITNESS_ESCROW_TOCK_KEY] = test_value

    try:
        # Reimport to pick up env var
        importlib.reload(tocking)
        assert tocking.WitnessEscrowTock == 2.5
    finally:
        # Clean up and restore defaults
        del os.environ[tocking.KERI_WITNESS_ESCROW_TOCK_KEY]
        importlib.reload(tocking)


def test_tocking_key_constants():
    from keri.app import tocking

    assert tocking.KERI_WITNESS_MSG_TOCK_KEY == "KERI_WITNESS_MSG_TOCK"
    assert tocking.KERI_WITNESS_ESCROW_TOCK_KEY == "KERI_WITNESS_ESCROW_TOCK"
    assert tocking.KERI_WITNESS_CUE_TOCK_KEY == "KERI_WITNESS_CUE_TOCK"
    assert tocking.KERI_INDIRECTOR_MSG_TOCK_KEY == "KERI_INDIRECTOR_MSG_TOCK"
    assert tocking.KERI_REACTOR_ESCROW_TOCK_KEY == "KERI_REACTOR_ESCROW_TOCK"
