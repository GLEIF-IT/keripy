# Root + GARs delegated multisig reproducer

Recreates a production scenario where Root (delegator, multisig) was on KERIpy 1.1.x,
from GARs (delegate, multisig) still on 1.1.x.

The script is split across the upgrade boundary because citadel's migration
does not rewrite escrow sub-db keys (`pdes`, `udes`, etc.) from the 1.1.x
plain-prefix format to the 1.2.x `<prefix>.<sn_hex>` format. Running the drt
send before migration leaves entries citadel can't read.

Root is a **7-member** establishment-only multisig with a weighted **["1/3"]x7**
threshold — any three signatures satisfy it. To mirror production, all seven
members sign the inception (so every member holds the group hab); downstream
events then need only three signatures. GARs is an unchanged **2-of-2** delegate
(gar1/gar2). Because Root is establishment-only, every Root approval is anchored
in a group *rotation*, which requires all seven members to have rotated locally
first.

## Phases

| Phase | Script                       | Run under     | Notes |
|-------|------------------------------|---------------|-------|
| A     | `setup-root-gars.sh`         | kli 1.1.4x    | Creates Root (7 members, all sign) + GARs (2-of-2); anchors GARs inception via a 3-signer (root1/root2/root3) Root rotation. Exits quiescent. |
| A′    | `rotate-root.sh` (optional)  | kli 1.1.4x    | Rotates Root TWICE, carrying all 7 each time but with disjoint quorums — sn=1→2 signed by root1/root2/root7, then sn=2→3 signed by root3/root4/root5 — to exercise the threshold and the carry-forward of non-signers. Advances Root to sn=3. |
| B     | (manual)                     | citadel 1.2.x | Open root1/root2/root3; let citadel migrate. |
| C     | `rotate-gars.sh`             | kli 1.1.4x    | Rotates GAR locals, dispatches the drt, then stops the rotate processes — GARs left pending at sn=0. The Root non-signers (root4..root7) are NOT rotated; they carry forward inert (as in production). |
| D     | (citadel UI)                 | citadel 1.2.x | In each signer (root1/root2/root3) rotate + refresh key state, then approve the drt; citadel anchors it in a 3-signer Root group rotation. Only the three signers rotate — their keys satisfy the 3-of-7 threshold and root4..root7 carry forward inert. |
| E     | `finalize-gars-rotation.sh`  | kli 1.1.4x    | gar1/gar2 pull the anchor and commit GARs at sn=1. |

Phase A′ is independent of the GARs/citadel flow; run it only when you want to
test Root rotations under different signing quorums. Each member's group hab only
advances when it co-signs, so after A′ the keystores sit at different sns
(root3/root4/root5 at sn=3, root1/root2/root7 at sn=2, root6 at sn=1). If you run
it before Phase B, open the **last-quorum** keystores (root3/root4/root5) in
citadel to see Root at its latest sn=3.

## Prerequisites

```
source scripts/demo/demo-scripts.sh
kli witness demo                       # in another terminal
rm -rf ~/.keri /usr/local/var/keri/*   # clean slate
```

All keystores use passcode `DoB26Fj4x9LboAFWJra17O` (override via `PASSCODE` env var).

## AIDs (deterministic, hardcoded)

```
root1 local    : EF11YNn4i0r0dX1KNrWs_ATQH878L3blwCMOSgwQVi57  (signer)
root2 local    : ENBdaRLJH7JOBAZo6aZbXelFP_I9yMd-RFrJ6pJ7V3CY  (signer)
root3 local    : EMEmbjR7mw0LvPk8co4q8Ks_0iX2anSnFu0NXh2WI80U  (signer)
root4 local    : ELAxo784aHZUWnRyd44VlkruUmiqQWc-pPYnZT-NtxLT
root5 local    : EDoJYSnGXF6C2ftkcAWr4pBDDOPy3p6UDDPw2Mkm957u
root6 local    : EMBkecmXbrbX_MOZnjbLi5DT975gPaMywbu_xRx3GZEH
root7 local    : EESfhafScg-EQcdvmSxDKBZ9tZ31gRVpg9uR4sKZy4GD
gar1  local    : EM0Di_wQZhUA0uKsR0gC0bSnOxcroCX-JbUuX9TBcvA1
gar2  local    : EA7cQdIZoCoQGWbjdVQYBVo4aNURsQml-vnEV8RMaSIG
Root  multisig : ENeFvERfrz5_7n3kElLVA5BcTnuBqE1hpc0OyuV_pKXc  (["1/3"]x7, EstOnly)
GARs  multisig : EM3Zwe5Pc-JjYy2y72kAf4FHc0WiWku-RO2vmfoN9LSI  (2-of-2)
```

These are SAIDs of the inception inputs. Change any salt, witness, threshold, or
member and they (plus the `aids`/`delpre` in `data/multisig-root.json` and
`data/multisig-gars.json`) must be regenerated — run `vLEI/derive-root7-prefixes.py`,
which recomputes every value and self-validates against the known set before printing.
