# Plan: Environment Variable Tock Configuration for Doers

## Overview

Add environment variable support for configuring tock values on doer methods to allow production systems to reduce CPU spinning by increasing tock intervals when idle.

## Pattern

Follow the existing pattern used for LMDB map sizes:
- Define constant: `KERI_<COMPONENT>_<METHOD>_TOCK = "KERI_<COMPONENT>_<METHOD>_TOCK"`
- Read at module level: `os.getenv(KERI_<COMPONENT>_<METHOD>_TOCK, <default>)`
- Use as default parameter value

## Tock Configurations

### File: `src/keri/app/indirecting.py`

| Class | Method | Line | Current | Default | Env Variable |
|-------|--------|------|---------|---------|--------------|
| WitnessStart | msgDo | 182 | 0.0 | 0.0 | `KERI_WITNESS_MSG_TOCK` |
| WitnessStart | escrowDo | 204 | 0.0 | **1.0** | `KERI_WITNESS_ESCROW_TOCK` |
| WitnessStart | cueDo | 230 | 0.0 | **0.25** | `KERI_WITNESS_CUE_TOCK` |
| Indirector | msgDo | 366 | 0.0 | 0.0 | `KERI_INDIRECTOR_MSG_TOCK` |
| Indirector | cueDo | 393 | 0.0 | **0.25** | `KERI_INDIRECTOR_CUE_TOCK` |
| Indirector | escrowDo | 421 | 0.0 | **1.0** | `KERI_INDIRECTOR_ESCROW_TOCK` |
| MailboxDirector | pollDo | 581 | 0.0 | **0.5** | `KERI_MAILBOX_POLL_TOCK` |
| MailboxDirector | msgDo | 659 | 0.0 | 0.0 | `KERI_MAILBOX_MSG_TOCK` |
| MailboxDirector | escrowDo | 684 | 0.0 | **1.0** | `KERI_MAILBOX_ESCROW_TOCK` |
| Poller | eventDo | 757 | 0.0 | **0.5** | `KERI_POLLER_EVENT_TOCK` |
| ReceiptEnd | interceptDo | 1155 | 0.0 | **0.1** | `KERI_RECEIPT_INTERCEPT_TOCK` |

### File: `src/keri/app/agenting.py`

| Class | Method | Line | Current | Default | Env Variable |
|-------|--------|------|---------|---------|--------------|
| WitnessReceiptor | receiptDo | 298 | 0.0 | 0.0 | `KERI_WITNESS_RECEIPTOR_TOCK` |
| WitnessInquisitor | msgDo | 453 | 1.0 | 1.0 | `KERI_WITNESS_INQUISITOR_TOCK` |
| WitnessPublisher | msgDo | 721 | 0.0 | **0.25** | `KERI_WITNESS_PUBLISHER_TOCK` |
| TCPMessenger | msgDo | 815 | 0.0 | 0.0 | Keep as-is (connection-specific) |
| HTTPMessenger | msgDo | 878 | 0.0 | 0.0 | Keep as-is (connection-specific) |

### File: `src/keri/app/directing.py`

| Class | Method | Line | Current | Default | Env Variable |
|-------|--------|------|---------|---------|--------------|
| Reactor | msgDo | 210 | 0.0 | 0.0 | `KERI_REACTOR_MSG_TOCK` |
| Reactor | cueDo | 237 | 0.0 | **0.25** | `KERI_REACTOR_CUE_TOCK` |
| Reactor | escrowDo | 264 | 0.0 | **1.0** | `KERI_REACTOR_ESCROW_TOCK` |
| Reactant | msgDo | 564 | 0.0 | 0.0 | `KERI_REACTANT_MSG_TOCK` |
| Reactant | cueDo | 592 | 0.0 | **0.25** | `KERI_REACTANT_CUE_TOCK` |
| Reactant | escrowDo | 623 | 0.0 | **1.0** | `KERI_REACTANT_ESCROW_TOCK` |

### File: `src/keri/app/storing.py`

| Class | Method | Line | Current | Default | Env Variable |
|-------|--------|------|---------|---------|--------------|
| Respondant | cueDo | 251 | 0.0 | **0.25** | `KERI_RESPONDANT_CUE_TOCK` |

## Implementation Steps

### Step 1: Create tocking.py module

Create new file `src/keri/app/tocking.py` to centralize tock configuration:

```python
# -*- encoding: utf-8 -*-
"""
keri.app.tocking module

Centralized tock configuration for doer timing control.
Environment variables allow production tuning without code changes.
"""
import os

# Witness component tocks (indirecting.py - WitnessStart)
KERI_WITNESS_MSG_TOCK_KEY = "KERI_WITNESS_MSG_TOCK"
KERI_WITNESS_ESCROW_TOCK_KEY = "KERI_WITNESS_ESCROW_TOCK"
KERI_WITNESS_CUE_TOCK_KEY = "KERI_WITNESS_CUE_TOCK"

WitnessMsgTock = float(os.getenv(KERI_WITNESS_MSG_TOCK_KEY, "0.0"))
WitnessEscrowTock = float(os.getenv(KERI_WITNESS_ESCROW_TOCK_KEY, "1.0"))
WitnessCueTock = float(os.getenv(KERI_WITNESS_CUE_TOCK_KEY, "0.25"))

# Indirector component tocks (indirecting.py - Indirector)
KERI_INDIRECTOR_MSG_TOCK_KEY = "KERI_INDIRECTOR_MSG_TOCK"
KERI_INDIRECTOR_CUE_TOCK_KEY = "KERI_INDIRECTOR_CUE_TOCK"
KERI_INDIRECTOR_ESCROW_TOCK_KEY = "KERI_INDIRECTOR_ESCROW_TOCK"

IndirectorMsgTock = float(os.getenv(KERI_INDIRECTOR_MSG_TOCK_KEY, "0.0"))
IndirectorCueTock = float(os.getenv(KERI_INDIRECTOR_CUE_TOCK_KEY, "0.25"))
IndirectorEscrowTock = float(os.getenv(KERI_INDIRECTOR_ESCROW_TOCK_KEY, "1.0"))

# MailboxDirector component tocks (indirecting.py - MailboxDirector)
KERI_MAILBOX_POLL_TOCK_KEY = "KERI_MAILBOX_POLL_TOCK"
KERI_MAILBOX_MSG_TOCK_KEY = "KERI_MAILBOX_MSG_TOCK"
KERI_MAILBOX_ESCROW_TOCK_KEY = "KERI_MAILBOX_ESCROW_TOCK"

MailboxPollTock = float(os.getenv(KERI_MAILBOX_POLL_TOCK_KEY, "0.5"))
MailboxMsgTock = float(os.getenv(KERI_MAILBOX_MSG_TOCK_KEY, "0.0"))
MailboxEscrowTock = float(os.getenv(KERI_MAILBOX_ESCROW_TOCK_KEY, "1.0"))

# Poller component tocks (indirecting.py - Poller)
KERI_POLLER_EVENT_TOCK_KEY = "KERI_POLLER_EVENT_TOCK"

PollerEventTock = float(os.getenv(KERI_POLLER_EVENT_TOCK_KEY, "0.5"))

# ReceiptEnd component tocks (indirecting.py - ReceiptEnd)
KERI_RECEIPT_INTERCEPT_TOCK_KEY = "KERI_RECEIPT_INTERCEPT_TOCK"

ReceiptInterceptTock = float(os.getenv(KERI_RECEIPT_INTERCEPT_TOCK_KEY, "0.1"))

# Reactor component tocks (directing.py - Reactor)
KERI_REACTOR_MSG_TOCK_KEY = "KERI_REACTOR_MSG_TOCK"
KERI_REACTOR_CUE_TOCK_KEY = "KERI_REACTOR_CUE_TOCK"
KERI_REACTOR_ESCROW_TOCK_KEY = "KERI_REACTOR_ESCROW_TOCK"

ReactorMsgTock = float(os.getenv(KERI_REACTOR_MSG_TOCK_KEY, "0.0"))
ReactorCueTock = float(os.getenv(KERI_REACTOR_CUE_TOCK_KEY, "0.25"))
ReactorEscrowTock = float(os.getenv(KERI_REACTOR_ESCROW_TOCK_KEY, "1.0"))

# Reactant component tocks (directing.py - Reactant)
KERI_REACTANT_MSG_TOCK_KEY = "KERI_REACTANT_MSG_TOCK"
KERI_REACTANT_CUE_TOCK_KEY = "KERI_REACTANT_CUE_TOCK"
KERI_REACTANT_ESCROW_TOCK_KEY = "KERI_REACTANT_ESCROW_TOCK"

ReactantMsgTock = float(os.getenv(KERI_REACTANT_MSG_TOCK_KEY, "0.0"))
ReactantCueTock = float(os.getenv(KERI_REACTANT_CUE_TOCK_KEY, "0.25"))
ReactantEscrowTock = float(os.getenv(KERI_REACTANT_ESCROW_TOCK_KEY, "1.0"))

# Respondant component tocks (storing.py - Respondant)
KERI_RESPONDANT_CUE_TOCK_KEY = "KERI_RESPONDANT_CUE_TOCK"

RespondantCueTock = float(os.getenv(KERI_RESPONDANT_CUE_TOCK_KEY, "0.25"))

# WitnessReceiptor component tocks (agenting.py)
KERI_WITNESS_RECEIPTOR_TOCK_KEY = "KERI_WITNESS_RECEIPTOR_TOCK"

WitnessReceiptorTock = float(os.getenv(KERI_WITNESS_RECEIPTOR_TOCK_KEY, "0.0"))

# WitnessInquisitor component tocks (agenting.py)
KERI_WITNESS_INQUISITOR_TOCK_KEY = "KERI_WITNESS_INQUISITOR_TOCK"

WitnessInquisitorTock = float(os.getenv(KERI_WITNESS_INQUISITOR_TOCK_KEY, "1.0"))

# WitnessPublisher component tocks (agenting.py)
KERI_WITNESS_PUBLISHER_TOCK_KEY = "KERI_WITNESS_PUBLISHER_TOCK"

WitnessPublisherTock = float(os.getenv(KERI_WITNESS_PUBLISHER_TOCK_KEY, "0.25"))
```

### Step 2: Update indirecting.py

1. Add import: `from . import tocking`
2. Update method defaults:

```python
# WitnessStart
def msgDo(self, tymth=None, tock=None):
    ...
    self.tock = tock if tock is not None else tocking.WitnessMsgTock

def escrowDo(self, tymth=None, tock=None):
    ...
    self.tock = tock if tock is not None else tocking.WitnessEscrowTock

def cueDo(self, tymth=None, tock=None):
    ...
    self.tock = tock if tock is not None else tocking.WitnessCueTock

# Similar pattern for Indirector, MailboxDirector, Poller, ReceiptEnd
```

### Step 3: Update agenting.py

1. Add import: `from . import tocking`
2. Update WitnessReceiptor, WitnessInquisitor, WitnessPublisher methods

### Step 4: Update directing.py

1. Add import: `from . import tocking`
2. Update Reactor and Reactant methods

### Step 5: Update storing.py

1. Add import: `from . import tocking`
2. Update Respondant.cueDo method

### Step 6: Update doers-timing-inventory.md

Add documentation section on configurable tocks.

## Default Value Rationale

| Tock Type | Default | Rationale |
|-----------|---------|-----------|
| msgDo | 0.0 | Message processing should remain responsive |
| escrowDo | 1.0 | Escrow processing is not time-critical |
| cueDo | 0.25 | Cue processing can tolerate 250ms delay |
| pollDo | 0.5 | Polling can tolerate 500ms intervals |
| eventDo | 0.5 | Event processing has internal yields |
| interceptDo | 0.1 | HTTP interception needs moderate responsiveness |

## Production Deployment

For a production witness system, operators can set environment variables:

```bash
# Recommended production values for witness
export KERI_WITNESS_ESCROW_TOCK=1.0
export KERI_WITNESS_CUE_TOCK=0.25
export KERI_MAILBOX_ESCROW_TOCK=1.0
export KERI_MAILBOX_POLL_TOCK=0.5
export KERI_POLLER_EVENT_TOCK=0.5
```

For high-throughput systems requiring lower latency:

```bash
# Lower latency configuration
export KERI_WITNESS_ESCROW_TOCK=0.5
export KERI_WITNESS_CUE_TOCK=0.1
export KERI_MAILBOX_POLL_TOCK=0.25
```

## Testing

1. Verify default behavior unchanged when env vars not set
2. Verify env var overrides work correctly
3. Run existing test suite to ensure no regressions
4. Add unit tests for tocking module
