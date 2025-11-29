# Doers, DoDoers, and Doists: Complete Timing Inventory

This document provides a comprehensive inventory of all Doers, DoDoers, and Doists in the KERI codebase with their timing configurations.

## Table of Contents

- [Overview](#overview)
- [Timing Model](#timing-model)
- [Doer Classes](#doer-classes-13-total)
- [DoDoer Classes](#dodoer-classes-76-total)
- [Doist Instances](#doist-instances)
- [Non-Default Tock Values](#non-default-tock-values)
- [Timing Summary](#timing-summary)
- [Execution Hierarchy](#execution-hierarchy)

---

## Overview

| Component | Count | Purpose |
|-----------|-------|---------|
| **Doer** | 13 | Simple task executors (lifecycle management) |
| **DoDoer** | 76 | Nested schedulers (run other doers) |
| **Doist** | 1 | Root scheduler (top-level event loop) |
| **Generator Methods** | ~120 | Doified methods with tock parameters |

---

## Timing Model

### What is Tock?

`tock` is a float value representing the desired time (in seconds) between runs of a doer.

| Tock Value | Meaning | Frequency |
|------------|---------|-----------|
| `0.0` | Run as soon as possible | Every Doist cycle (~31ms) |
| `0.03125` | Default Doist cycle | ~32 times/second |
| `1.0` | Throttled execution | Once per second |

## Doer Classes (13 total)

Simple task executors that handle lifecycle management.

### Core Infrastructure Doers

| Class | File | Line | Default Tock | Purpose |
|-------|------|------|--------------|---------|
| `Consoler` | `app/apping.py` | 18 | 0.0 | Console interaction |
| `ConfigerDoer` | `app/configing.py` | 197 | 0.0 | Configuration loading |
| `Director` | `app/directing.py` | 19 | 0.0 | Direct mode coordinator |
| `HaberyDoer` | `app/habbing.py` | 854 | 0.0 | Habery lifecycle |
| `KeeperDoer` | `app/keeping.py` | 314 | 0.0 | Keeper lifecycle |
| `ManagerDoer` | `app/keeping.py` | 1728 | 0.0 | Manager lifecycle |
| `AdjudicationDoer` | `app/watching.py` | 165 | 0.0 | Watcher adjudication |
| `BaserDoer` | `db/basing.py` | 3228 | 0.0 | Database lifecycle |
| `RegeryDoer` | `vdr/credentialing.py` | 127 | 0.0 | Registry lifecycle |

### CLI Migration Doers

| Class | File | Line | Default Tock | Purpose |
|-------|------|------|--------------|---------|
| `CleanDoer` | `cli/commands/clean.py` | 43 | 0.0 | Clean command |
| `CleanDoer` | `cli/commands/migrate/show.py` | 45 | 0.0 | Migration show |
| `ListDoer` | `cli/commands/migrate/list.py` | 44 | 0.0 | Migration list |
| `MigrateDoer` | `cli/commands/migrate/run.py` | 46 | 0.0 | Migration run |

---

## DoDoer Classes (excluding KLI)

Nested schedulers that manage and run child doers.

### Directing DoDoers

| Class | File | Line | Default Tock | Child Doers |
|-------|------|------|--------------|-------------|
| `Reactor` | `app/directing.py` | 94 | 0.0 | msgDo, cueDo, escrowDo |
| `Directant` | `app/directing.py` | 299 | 0.0 | serviceDo |
| `Reactant` | `app/directing.py` | 444 | **0.03125** | msgDo, cueDo, escrowDo |

### Agenting DoDoers

| Class | File | Line | Default Tock | Child Doers |
|-------|------|------|--------------|-------------|
| `Receiptor` | `app/agenting.py` | 28 | 0.0 | witDo, gitDo |
| `WitnessReceiptor` | `app/agenting.py` | 266 | 0.0 | receiptDo |
| `WitnessInquisitor` | `app/agenting.py` | 423 | 0.0 | msgDo (**tock=1.0**) |
| `WitnessPublisher` | `app/agenting.py` | 564 | 0.0 | sendDo |
| `TCPMessenger` | `app/agenting.py` | 654 | 0.0 | receiptDo, msgDo |
| `TCPStreamMessenger` | `app/agenting.py` | 748 | 0.0 | receiptDo, msgDo |
| `HTTPMessenger` | `app/agenting.py` | 842 | 0.0 | msgDo, responseDo |
| `HTTPStreamMessenger` | `app/agenting.py` | 925 | 0.0 | msgDo |

### Indirecting DoDoers

| Class | File | Line | Default Tock | Child Doers |
|-------|------|------|--------------|-------------|
| `WitnessStart` | `app/indirecting.py` | 144 | 0.0 | start, msgDo, escrowDo, cueDo |
| `Indirector` | `app/indirecting.py` | 263 | 0.0 | msgDo, cueDo, escrowDo |
| `MailboxDirector` | `app/indirecting.py` | 455 | 0.0 | pollDo, msgDo, escrowDo |
| `Poller` | `app/indirecting.py` | 727 | 0.0 | eventDo |
| `ReceiptEnd` | `app/indirecting.py` | 1029 | 0.0 | interceptDo |

### Querying DoDoers

| Class | File | Line | Default Tock | Purpose |
|-------|------|------|--------------|---------|
| `QueryDoer` | `app/querying.py` | 12 | 0.0 | Key state queries |
| `KeyStateNoticer` | `app/querying.py` | 24 | 0.0 | Key state notifications |
| `LogQuerier` | `app/querying.py` | 67 | 0.0 | Log queries |
| `SeqNoQuerier` | `app/querying.py` | 91 | 0.0 | Sequence number queries |
| `AnchorQuerier` | `app/querying.py` | 123 | 0.0 | Anchor queries |

### Credential DoDoers

| Class | File | Line | Default Tock | Child Doers |
|-------|------|------|--------------|-------------|
| `Registrar` | `vdr/credentialing.py` | 491 | 0.0 | escrowDo (**tock=1.0**) |
| `Credentialer` | `vdr/credentialing.py` | 766 | 0.0 | escrowDo (**tock=1.0**) |
| `WalletDoer` | `vc/walleting.py` | 54 | 0.0 | escrowDo, verifierDo |

### Other Core DoDoers

| Class | File | Line | Default Tock | Child Doers |
|-------|------|------|--------------|-------------|
| `Anchorer` | `app/delegating.py` | 22 | 0.0 | escrowDo (**tock=1.0**) |
| `Counselor` | `app/grouping.py` | 23 | 0.0 | escrowDo (**tock=1.0**) |
| `Poster` | `app/forwarding.py` | 25 | 0.0 | deliverDo |
| `Respondant` | `app/storing.py` | 175 | 0.0 | responseDo, cueDo |
| `Signaler` | `app/signaling.py` | 90 | 0.0 | expireDo |
| `Clienter` | `app/httping.py` | 214 | 0.0 | clientDo |

---

## Doist Instances

### Main Doist (runController)

| Location | File | Line | Tock | Mode |
|----------|------|------|------|------|
| `runController` | `app/directing.py` | 663-664 | **0.03125** | real=True |

```python
tock = 0.03125  # ~31ms cycle time (~32 cycles/second)
doist = doing.Doist(limit=expire, tock=tock, real=True, doers=doers)
```

---

## Non-Default Tock Values

These methods/classes use tock values other than 0.0:

### Throttled Operations (tock=1.0)

| Method | Class | File | Line | Reason |
|--------|-------|------|------|--------|
| `msgDo` | `WitnessInquisitor` | `app/agenting.py` | 453 | Throttle witness queries |
| `escrowDo` | `Counselor` | `app/grouping.py` | 75 | Group escrow processing |
| `escrowDo` | `Anchorer` | `app/delegating.py` | 98 | Delegation escrow |
| `escrowDo` | `Registrar` | `vdr/credentialing.py` | 655 | Registry escrow |
| `escrowDo` | `Credentialer` | `vdr/credentialing.py` | 881 | Credential escrow |

### Class-Level Tock Overrides

| Class | File | Line | Tock | Reason |
|-------|------|------|------|--------|
| `Reactant` | `app/directing.py` | 444 | **0.03125** | Class attribute override |

---

## Timing Summary

### Tock Value Distribution

| Tock Value | Count | Usage |
|------------|-------|-------|
| **0.0** | ~120 | Most operations (run ASAP) |
| **0.03125** (1/32s) | 2 | Doist default, Reactant class |
| **0.125** | 3 | Demo directors |
| **1.0** | 5 | Escrow processing, witness queries |
| **1.03125** | 1 | Demo |

### Execution Frequency by Tock

| Tock | Cycles/Second | Use Case |
|------|---------------|----------|
| 0.0 | ~32 (limited by Doist) | Message processing, cue handling |
| 0.03125 | ~32 | Default Doist cycle |
| 0.125 | 8 | Demo pacing |
| 1.0 | 1 | Escrow processing, witness queries |

---

## Execution Hierarchy

```
Doist (tock=0.03125, real=True)
│
├── Doer: HaberyDoer (lifecycle management)
├── Doer: KeeperDoer (lifecycle management)
├── Doer: BaserDoer (lifecycle management)
│
├── DoDoer: Reactor/Reactant (tock=0.0 or 0.03125)
│   ├── msgDo (tock=0.0) ────────────► runs every ~31ms
│   ├── cueDo (tock=0.0) ────────────► runs every ~31ms
│   └── escrowDo (tock=0.0) ─────────► runs every ~31ms
│
├── DoDoer: Indirector (tock=0.0)
│   ├── msgDo (tock=0.0) ────────────► runs every ~31ms
│   ├── cueDo (tock=0.0) ────────────► runs every ~31ms
│   └── escrowDo (tock=0.0) ─────────► runs every ~31ms
│
├── DoDoer: WitnessInquisitor (tock=0.0)
│   └── msgDo (tock=1.0) ────────────► runs every 1 second
│
├── DoDoer: Counselor (tock=0.0)
│   └── escrowDo (tock=1.0) ─────────► runs every 1 second
│
├── DoDoer: Anchorer (tock=0.0)
│   └── escrowDo (tock=1.0) ─────────► runs every 1 second
│
├── DoDoer: Registrar (tock=0.0)
│   └── escrowDo (tock=1.0) ─────────► runs every 1 second
│
└── DoDoer: Credentialer (tock=0.0)
    └── escrowDo (tock=1.0) ─────────► runs every 1 second
```

---

## Generator Method Pattern

All doified methods follow this pattern:

```python
def msgDo(self, tymth=None, tock=0.0):
    """
    Generator method for message processing.

    Args:
        tymth: Injected closure to get current time
        tock: Initial tock value (time between runs)
    """
    # ENTER CONTEXT
    self.wind(tymth)        # Inject time dependency
    self.tock = tock        # Set initial tock
    _ = (yield self.tock)   # First yield: enter, scheduler takes control

    # RECUR CONTEXT
    while True:
        # Do work here
        self.processMessages()

        # Yield tock to scheduler
        # - Returns control to scheduler
        # - Scheduler sends back .tyme when it's time to run again
        yield self.tock

    # EXIT CONTEXT (reached via GeneratorExit or return)
    return False  # Return value becomes doer.done
```

---

*Generated from keripy v1.2.9 codebase analysis*
