#!/usr/bin/env python3
"""Deterministically derive the AID prefixes for the 7-member (3-of-7) Root /
2-of-2 GARs reproducer, and VALIDATE the method by first reproducing the known
old 2-of-2 prefixes exactly.

KERI derivation is version-stable, so computing under 1.2.x reproduces what
1.1.x kli will produce at runtime, provided the inception inputs match. We mirror
kli's group inception path (keri.app.habbing.GroupHab.make):
  - Root  : eventing.incept(... cnfg=['EO'], data=None, code=Blake3_256)
  - GARs  : eventing.delcept(... delpre=ROOT_PRE, code=Blake3_256)
Local member AIDs are derived by actually incepting each salt's hab in a temp
Habery (exactly as kli incept does).
"""
import os
import shutil

from keri.app import habbing
from keri.core import coring, eventing

# Throwaway keystore base; cleaned up at exit. Must run temp=False so the salt is
# stretched with the same tier kli uses (temp=True uses a different quick stretch).
SCRATCH = "deriv7scratch"

PASSCODE = "DoB26Fj4x9LboAFWJra17O"
WITS = [
    "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
    "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
    "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX",
]
# Local member config (delegator-1.json / gars-1.json — all identical).
LOCAL = dict(transferable=True, wits=WITS, toad=2, icount=1, ncount=1, isith="1", nsith="1")

# salt suffix -> member.  root1/root2/gar1/gar2 keep their existing salts;
# root3..root7 extend the pattern with o5..o9.
SALT = lambda suf: f"0ACDEyMzQ1Njc4OWdoaWpd{suf}"
ROOT_SALTS = {f"root{i}": SALT(s) for i, s in zip(range(1, 8), ["o1", "o2", "o5", "o6", "o7", "o8", "o9"])}
GAR_SALTS = {"gar1": SALT("o3"), "gar2": SALT("o4")}

# Known-good values produced by the old 2-of-2 run (validation anchors).
KNOWN = {
    "root1": "EF11YNn4i0r0dX1KNrWs_ATQH878L3blwCMOSgwQVi57",
    "root2": "ENBdaRLJH7JOBAZo6aZbXelFP_I9yMd-RFrJ6pJ7V3CY",
    "gar1": "EM0Di_wQZhUA0uKsR0gC0bSnOxcroCX-JbUuX9TBcvA1",
    "gar2": "EA7cQdIZoCoQGWbjdVQYBVo4aNURsQml-vnEV8RMaSIG",
}
OLD_ROOT_PRE = "ECbVd-kmWq0J8DHxLN6bKz3WbHtSl8RgeTD3VtnF9tQ4"
OLD_GARS_PRE = "EAbWX_-KFnE51AB7pi9UJNDCQwjmPXvmzkB7RJJWv4pG"


def derive_member(name, salt):
    """Incept a single-sig hab from a salt in a real (non-temp) keystore so the salt
    is stretched exactly as kli does; return (pre, verfer_qb64, ndiger_qb64)."""
    with habbing.openHby(name=name, base=SCRATCH, salt=salt, bran=PASSCODE, temp=False) as hby:
        hab = hby.makeHab(name=name, **LOCAL)
        return hab.pre, hab.kever.verfers[0].qb64, hab.kever.ndigers[0].qb64


def group_pre(members, isith, nsith, estOnly=False, delpre=None):
    """Compute a multisig group inception SAID exactly as GroupHab.make() does."""
    keys = [m[1] for m in members]
    ndigs = [m[2] for m in members]
    cst = coring.Tholder(sith=isith).sith
    nst = coring.Tholder(sith=nsith).sith
    cnfg = [eventing.TraitDex.EstOnly] if estOnly else []
    if delpre:
        serder = eventing.delcept(keys=keys, delpre=delpre, isith=cst, nsith=nst, ndigs=ndigs,
                                  toad=3, wits=WITS, cnfg=cnfg, code=coring.MtrDex.Blake3_256)
    else:
        serder = eventing.incept(keys=keys, isith=cst, nsith=nst, ndigs=ndigs, toad=3, wits=WITS,
                                 cnfg=cnfg, code=coring.MtrDex.Blake3_256, data=None)
    return serder.pre


def main():
    roots = {name: derive_member(name, salt) for name, salt in ROOT_SALTS.items()}
    gars = {name: derive_member(name, salt) for name, salt in GAR_SALTS.items()}

    print("== local member prefixes ==")
    ok = True
    for name, m in {**roots, **gars}.items():
        expect = KNOWN.get(name)
        tag = ""
        if expect is not None:
            good = m[0] == expect
            ok &= good
            tag = "  OK" if good else f"  MISMATCH expected {expect}"
        print(f"  {name}: {m[0]}{tag}")

    # --- validation: reproduce the OLD 2-of-2 group prefixes ---
    old_root = group_pre([roots["root1"], roots["root2"]], isith="2", nsith="2", estOnly=True)
    old_gars = group_pre([gars["gar1"], gars["gar2"]], isith="2", nsith="2", delpre=OLD_ROOT_PRE)
    print("\n== validation (old 2-of-2) ==")
    print(f"  ROOT_PRE: {old_root}  {'OK' if old_root == OLD_ROOT_PRE else 'MISMATCH ' + OLD_ROOT_PRE}")
    print(f"  GARS_PRE: {old_gars}  {'OK' if old_gars == OLD_GARS_PRE else 'MISMATCH ' + OLD_GARS_PRE}")
    ok &= old_root == OLD_ROOT_PRE and old_gars == OLD_GARS_PRE

    if not ok:
        print("\n!! validation FAILED — derivation method does not match; not emitting new values")
        return

    # --- new values: Root 3-of-7 via weighted thirds, GARs unchanged 2-of-2 but new delpre ---
    # ["1/3"] x7: any three members' weights sum to 1, satisfying the threshold.
    thirds = ["1/3"] * 7
    new_root = group_pre([roots[f"root{i}"] for i in range(1, 8)], isith=thirds, nsith=thirds, estOnly=True)
    new_gars = group_pre([gars["gar1"], gars["gar2"]], isith="2", nsith="2", delpre=new_root)
    print("\n== NEW values (Root 3-of-7) ==")
    for i in range(1, 8):
        print(f'  ROOT{i}_PRE="{roots[f"root{i}"][0]}"')
    print(f'  GAR1_PRE="{gars["gar1"][0]}"')
    print(f'  GAR2_PRE="{gars["gar2"][0]}"')
    print(f'  ROOT_PRE="{new_root}"')
    print(f'  GARS_PRE="{new_gars}"')
    print("\n  root member aids (multisig-root.json order):")
    for i in range(1, 8):
        print(f'    "{roots[f"root{i}"][0]}",')


def cleanup():
    """Remove the throwaway keystore from every keri head dir it might land in."""
    for root in ("/usr/local/var/keri", os.path.expanduser("~/.keri")):
        for sub in ("db", "ks", "cf"):
            shutil.rmtree(os.path.join(root, sub, SCRATCH), ignore_errors=True)


if __name__ == "__main__":
    try:
        main()
    finally:
        cleanup()
