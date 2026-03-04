# Duplicity Induction Testing for KERI Watchers

## Purpose

This document describes a procedure for intentionally producing detectable duplicity for a KERI AID. The goal is to create two divergent key event logs for the same identifier, deliver each version to a different witness, and then verify that a watcher correctly detects the inconsistency.

This is **test tooling only**. Any AID subjected to this process is permanently compromised.

## Background

Duplicity in KERI is the condition where a controller has produced two or more conflicting signed events at the same sequence number. A functioning watcher should detect this by querying multiple witnesses and comparing their KELs for the same prefix. If two witnesses hold different events at the same `sn` for the same AID, the watcher has cryptographic proof of controller misbehavior.

## Architecture

All components run on a single machine. We use keripy's `--base` flag to maintain two completely separate key stores seeded with identical key material, simulating a malicious controller operating from two locations.

```text
┌─────────────────────┐     ┌─────────────────────┐
│   Key Store A       │     │   Key Store B       │
│   --base /tmp/dup_a │     │   --base /tmp/dup_b │
│                     │     │                     │
│   icp  (sn=0) ──────┼─────┼── icp  (sn=0)       │  ← identical
│   ixn  (sn=1) ✗     │     │   ixn  (sn=1) ✗     │  ← divergent
└─────────┬───────────┘     └──────────┬──────────┘
          │                            │
          │ submit to                  │ submit to
          │ witness 1 only             │ witness 2 only
          ▼                            ▼
   ┌──────────────┐           ┌──────────────┐
   │  Witness 1   │           │  Witness 2   │
   │  http 5631   │           │  http 5633   │
   │              │           │              │
   │  KEL:        │           │  KEL:        │
   │  sn=0: icp   │           │  sn=0: icp   │
   │  sn=1: ixn_A │           │  sn=1: ixn_B │
   └──────┬───────┘           └──────┬───────┘
          │                          │
          └──────────┬───────────────┘
                     │
                     ▼
              ┌──────────────┐
              │   Watcher    │
              │              │
              │  Queries both│
              │  witnesses,  │
              │  detects     │
              │  conflict at │
              │  sn=1        │
              └──────────────┘
```

## Prerequisites

- keripy installed with the `kli` command available

### Copy Configuration Files

```bash
rm -rf /tmp/dup_a /tmp/dup_b /tmp/witness1 /tmp/witness2
rm -rf /tmp/keri/cf
rm -f /tmp/inception.json
mkdir -p /tmp/keri/cf
cp src/keri/app/cli/commands/duplicity/witness1.json /tmp/keri/cf/
cp src/keri/app/cli/commands/duplicity/witness2.json /tmp/keri/cf/
cp src/keri/app/cli/commands/duplicity/inception.json /tmp/
cp src/keri/app/cli/commands/duplicity/controller.json /tmp/keri/cf/
```

### Initialize Witness Keystores (deterministic AIDs)

Initialize witness keystores with fixed salts to ensure consistent AIDs:

```bash
kli init --name wit1 --base /tmp/witness1 --nopasscode \
    --salt "0AChVQ-jx1P-I7YDX0zHHXIK" \
    --config-dir /tmp --config-file witness1.json

kli init --name wit2 --base /tmp/witness2 --nopasscode \
    --salt "0ACOvPFdUhJOCllqUfKFJ4fQ" \
    --config-dir /tmp --config-file witness2.json
```

### Incept Witness Identifiers

Create the non-transferable witness identifiers:

```bash
kli incept --name wit1 --base /tmp/witness1 --alias wit1 \
    --icount 1 --ncount 0 --isith 1 --nsith 0 --toad 0

kli incept --name wit2 --base /tmp/witness2 --alias wit2 \
    --icount 1 --ncount 0 --isith 1 --nsith 0 --toad 0
```

With the salts above, the AIDs should be:

- **Witness 1**: `BM0tKLGgoVnS3uVJj4jLzjKu7ohbEGtr-ZV6WYN6LKlo`
- **Witness 2**: `BG1rKcljah4JNbzMXtrhpXVKrFw7eMWfkKE9nyqtPiv_`

### Register Witness Endpoints

Register endpoint locations so controllers can discover them via OOBI:

```bash
kli ends add --name wit1 --base /tmp/witness1 --alias wit1 \
    --eid BM0tKLGgoVnS3uVJj4jLzjKu7ohbEGtr-ZV6WYN6LKlo --role controller
kli location add --name wit1 --base /tmp/witness1 --alias wit1 \
    --url "http://127.0.0.1:5631/"
kli location add --name wit1 --base /tmp/witness1 --alias wit1 \
    --url "tcp://127.0.0.1:5632/"

kli ends add --name wit2 --base /tmp/witness2 --alias wit2 \
    --eid BG1rKcljah4JNbzMXtrhpXVKrFw7eMWfkKE9nyqtPiv_ --role controller
kli location add --name wit2 --base /tmp/witness2 --alias wit2 \
    --url "http://127.0.0.1:5633/"
kli location add --name wit2 --base /tmp/witness2 --alias wit2 \
    --url "tcp://127.0.0.1:5634/"
```

### Start Witnesses

```bash
kli witness start --name wit1 --alias wit1 --base /tmp/witness1 \
    --config-dir /tmp --config-file witness1.json -H 5631 -T 5632

kli witness start --name wit2 --alias wit2 --base /tmp/witness2 \
    --config-dir /tmp --config-file witness2.json -H 5633 -T 5634
```

## Procedure

### Step 1: Initialize Two Identical Key Stores

Both key stores use the same salt, which produces identical key material. The controller config file contains the witness OOBIs which are resolved automatically during init.

```bash
kli init --name duptest --base /tmp/dup_a --salt "0ACDEyMzQ1Njc4OWxtbm9aBc" --nopasscode \
    --config-dir /tmp --config-file controller.json

kli init --name duptest --base /tmp/dup_b --salt "0ACDEyMzQ1Njc4OWxtbm9aBc" --nopasscode \
    --config-dir /tmp --config-file controller.json
```

### Step 2: Incept on Both Stores

Both stores incept with the **same full witness list**. Each witness sees the same `icp` event twice, which is harmless.

```bash
kli incept --name duptest --base /tmp/dup_a --alias duptest --transferable \
    --wits "BM0tKLGgoVnS3uVJj4jLzjKu7ohbEGtr-ZV6WYN6LKlo" \
    --wits "BG1rKcljah4JNbzMXtrhpXVKrFw7eMWfkKE9nyqtPiv_" \
    --toad 1 --file /tmp/inception.json

kli incept --name duptest --base /tmp/dup_b --alias duptest --transferable \
    --wits "BM0tKLGgoVnS3uVJj4jLzjKu7ohbEGtr-ZV6WYN6LKlo" \
    --wits "BG1rKcljah4JNbzMXtrhpXVKrFw7eMWfkKE9nyqtPiv_" \
    --toad 1 --file /tmp/inception.json
```

Verify both produced the same prefix.

### Step 3: Induce Duplicity

This is where the new tooling comes in. We create a divergent interaction event on each store and deliver it to a single witness.

```bash
kli duplicity induce --name duptest --base /tmp/dup_a \
    --alias duptest \
    --data '{"anchor": "branch_a"}' \
    --witness "BM0tKLGgoVnS3uVJj4jLzjKu7ohbEGtr-ZV6WYN6LKlo"

kli duplicity induce --name duptest --base /tmp/dup_b \
    --alias duptest \
    --data '{"anchor": "branch_b"}' \
    --witness "BG1rKcljah4JNbzMXtrhpXVKrFw7eMWfkKE9nyqtPiv_"
```

After this step, witness 1 holds `ixn_A` at `sn=1` and witness 2 holds `ixn_B` at `sn=1`. Both are validly signed by the same key pair.
