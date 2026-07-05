#!/bin/bash
# Phase A of the Root/GARs reproducer.
#
# Creates a 3-of-7 multisig "Root" AID and a 2-of-2 multisig "GARs" AID
# delegated from Root, anchors the GARs inception in Root's KEL via
# kli delegate confirm, and exits with the keystores in a quiescent state
# (no pending delegations in any escrow).
#
# Root has SEVEN members (root1..root7) with a weighted threshold of ["1/3"]x7,
# i.e. any THREE members satisfy signing and rotation. To mirror production, ALL
# SEVEN members sign the inception (so every member holds the group hab and can
# participate later). Downstream events then need only three signatures — the
# GARs delegation approval below is signed by root1/root2/root3, and
# rotate-root.sh exercises a later rotation signed by root1/root2/root7.
#
# Because Root is establishment-only, it can only approve a delegation by
# anchoring the seal in a group ROTATION. A group rotation reveals EVERY member's
# pre-committed next key, so ALL seven root members must rotate their own local
# hab (and the approving signers must re-query everyone's new key state) before
# the approval — even though only three of them sign it.
#
# Prefixes below are deterministic SAIDs of the inception inputs; regenerate them
# with vLEI/derive-root7-prefixes.py if any salt / threshold / member changes.
#
# Run under kli 1.1.4x. After this completes, point your 1.2.x software
# (citadel) at the root1/root2/root3 keystores — its migration will run cleanly
# against the quiescent DB. Then run rotate-gars.sh.
#
# Prerequisites:
#   source scripts/demo/demo-scripts.sh
#   kli witness demo                # in another terminal
#   rm -rf ~/.keri /usr/local/var/keri/*   # start from a clean keystore

WITNESS_HOST="http://127.0.0.1:5642"
WIT="BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha"

# 22-character passcode shared by all keystores. Override via env if desired.
PASSCODE="${PASSCODE:-DoB26Fj4x9LboAFWJra17O}"

# ---- Members -------------------------------------------------------------
# Root members and their keystore salts (root1/root2/gar1/gar2 keep their
# original salts; root3..root7 extend the pattern with o5..o9).
ROOT_NAMES=(root1 root2 root3 root4 root5 root6 root7)
ROOT_SALTS=(
    0ACDEyMzQ1Njc4OWdoaWpdo1
    0ACDEyMzQ1Njc4OWdoaWpdo2
    0ACDEyMzQ1Njc4OWdoaWpdo5
    0ACDEyMzQ1Njc4OWdoaWpdo6
    0ACDEyMzQ1Njc4OWdoaWpdo7
    0ACDEyMzQ1Njc4OWdoaWpdo8
    0ACDEyMzQ1Njc4OWdoaWpdo9
)
ROOT_PRES=(
    EF11YNn4i0r0dX1KNrWs_ATQH878L3blwCMOSgwQVi57
    ENBdaRLJH7JOBAZo6aZbXelFP_I9yMd-RFrJ6pJ7V3CY
    EMEmbjR7mw0LvPk8co4q8Ks_0iX2anSnFu0NXh2WI80U
    ELAxo784aHZUWnRyd44VlkruUmiqQWc-pPYnZT-NtxLT
    EDoJYSnGXF6C2ftkcAWr4pBDDOPy3p6UDDPw2Mkm957u
    EMBkecmXbrbX_MOZnjbLi5DT975gPaMywbu_xRx3GZEH
    EESfhafScg-EQcdvmSxDKBZ9tZ31gRVpg9uR4sKZy4GD
)
# All seven members sign the inception (mirrors production). The downstream GARs
# delegation approval is a 3-signature rotation; root1/root2/root3 perform it.
APPROVAL_SIGNERS=(root1 root2 root3)

# GAR members (unchanged 2-of-2).
GAR1_PRE="EM0Di_wQZhUA0uKsR0gC0bSnOxcroCX-JbUuX9TBcvA1"
GAR2_PRE="EA7cQdIZoCoQGWbjdVQYBVo4aNURsQml-vnEV8RMaSIG"

# Group AIDs (SAIDs of the multisig inception events).
ROOT_PRE="ENeFvERfrz5_7n3kElLVA5BcTnuBqE1hpc0OyuV_pKXc"
GARS_PRE="EM3Zwe5Pc-JjYy2y72kAf4FHc0WiWku-RO2vmfoN9LSI"

# ---- Root locals (root1..root7) -----------------------------------------
for i in "${!ROOT_NAMES[@]}"; do
    name="${ROOT_NAMES[$i]}"
    kli init --name "${name}" --passcode ${PASSCODE} --salt "${ROOT_SALTS[$i]}" --config-dir ${KERI_SCRIPT_DIR} --config-file demo-witness-oobis
    kli incept --name "${name}" --passcode ${PASSCODE} --alias "${name}" --file ${KERI_DEMO_SCRIPT_DIR}/data/delegator-1.json
done

# ---- GAR locals ---------------------------------------------------------
kli init --name gar1 --passcode ${PASSCODE} --salt 0ACDEyMzQ1Njc4OWdoaWpdo3 --config-dir ${KERI_SCRIPT_DIR} --config-file demo-witness-oobis
kli incept --name gar1 --passcode ${PASSCODE} --alias gar1 --file ${KERI_DEMO_SCRIPT_DIR}/data/gars-1.json

kli init --name gar2 --passcode ${PASSCODE} --salt 0ACDEyMzQ1Njc4OWdoaWpdo4 --config-dir ${KERI_SCRIPT_DIR} --config-file demo-witness-oobis
kli incept --name gar2 --passcode ${PASSCODE} --alias gar2 --file ${KERI_DEMO_SCRIPT_DIR}/data/gars-2.json

# ---- OOBIs: full mesh among all root members ----------------------------
# Every member signs the inception, so every member builds the group event (which
# lists all seven members' keys) and therefore needs key state (KEL + endpoints)
# for the other six. Resolve the full 7x6 mesh.
for i in "${!ROOT_NAMES[@]}"; do
    me="${ROOT_NAMES[$i]}"
    for j in "${!ROOT_NAMES[@]}"; do
        [ "${i}" = "${j}" ] && continue
        kli oobi resolve --name "${me}" --passcode ${PASSCODE} --oobi-alias "${ROOT_NAMES[$j]}" \
            --oobi ${WITNESS_HOST}/oobi/${ROOT_PRES[$j]}/witness/${WIT}
    done
done

# ---- Multisig incept "Root" (all 7 sign) --------------------------------
PID_LIST=""
for name in "${ROOT_NAMES[@]}"; do
    kli multisig incept --name "${name}" --passcode ${PASSCODE} --alias "${name}" --group Root --file ${KERI_DEMO_SCRIPT_DIR}/data/multisig-root.json &
    PID_LIST+=" $!"
done
wait $PID_LIST
unset PID_LIST

# ---- OOBIs: gar1 <-> gar2 -----------------------------------------------
kli oobi resolve --name gar1 --passcode ${PASSCODE} --oobi-alias gar2 --oobi ${WITNESS_HOST}/oobi/${GAR2_PRE}/witness/${WIT}
kli oobi resolve --name gar2 --passcode ${PASSCODE} --oobi-alias gar1 --oobi ${WITNESS_HOST}/oobi/${GAR1_PRE}/witness/${WIT}

# ---- OOBIs: gar1, gar2 -> Root (the delegator) --------------------------
kli oobi resolve --name gar1 --passcode ${PASSCODE} --oobi-alias Root --oobi ${WITNESS_HOST}/oobi/${ROOT_PRE}/witness/${WIT}
kli oobi resolve --name gar2 --passcode ${PASSCODE} --oobi-alias Root --oobi ${WITNESS_HOST}/oobi/${ROOT_PRE}/witness/${WIT}

# ---- OOBIs: signers -> gar1, gar2 (delegator learns delegate members) ----
# Out-of-band introduction of the GAR members to the Root signers. Without this
# Root has no key state for the gar locals, so the later /delegate/request (drt)
# exn — signed by a gar member — arrives from an "unknown" sender and the
# delegator can't verify it. Resolving here makes each gar a known contact with
# known witness endpoints, so the drt-time refresh can target those endpoints
# instead of probing every configured witness pool.
for signer in "${APPROVAL_SIGNERS[@]}"; do
    kli oobi resolve --name "${signer}" --passcode ${PASSCODE} --oobi-alias gar1 --oobi ${WITNESS_HOST}/oobi/${GAR1_PRE}/witness/${WIT}
    kli oobi resolve --name "${signer}" --passcode ${PASSCODE} --oobi-alias gar2 --oobi ${WITNESS_HOST}/oobi/${GAR2_PRE}/witness/${WIT}
done

# ---- Pre-rotate ALL root members so the group can rotate to approve ------
# Root is establishment-only: it can only approve a delegation by anchoring the
# seal in a ROTATION (not an interaction). A group rotation's new keys are EVERY
# member's pre-committed next keys, so each of the seven members must first rotate
# its own local hab (revealing those keys); then the approving signers re-query
# every other member's new key state so they can build the rotation. Done BEFORE
# the GARs delegation so its wait timer does not run during these rotations.
for name in "${ROOT_NAMES[@]}"; do
    kli rotate --name "${name}" --passcode ${PASSCODE} --alias "${name}"
done
for signer in "${APPROVAL_SIGNERS[@]}"; do
    for j in "${!ROOT_NAMES[@]}"; do
        member="${ROOT_NAMES[$j]}"
        [ "${signer}" = "${member}" ] && continue
        kli query --name "${signer}" --passcode ${PASSCODE} --alias "${signer}" --prefix ${ROOT_PRES[$j]}
    done
done

# ---- Multisig incept "GARs" (delegated from Root) -----------------------
# Longer --wait: the rotation-anchored approval (group rotation + counselor + witness receipts)
# takes longer than the old interaction-anchored path.
kli multisig incept --name gar1 --passcode ${PASSCODE} --alias gar1 --group GARs --wait 90 --file ${KERI_DEMO_SCRIPT_DIR}/data/multisig-gars.json &
PID_LIST+=" $!"
kli multisig incept --name gar2 --passcode ${PASSCODE} --alias gar2 --group GARs --wait 90 --file ${KERI_DEMO_SCRIPT_DIR}/data/multisig-gars.json &
PID_LIST+=" $!"

# Give the delegation request time to reach Root members
sleep 3

# ---- Root approves the GARs inception (3 of 7 sign) ---------------------
# Root is establishment-only, so the approval must anchor in a rotation (no --interact).
for signer in "${APPROVAL_SIGNERS[@]}"; do
    kli delegate confirm --name "${signer}" --passcode ${PASSCODE} --alias Root --auto &
    PID_LIST+=" $!"
done

wait $PID_LIST
unset PID_LIST

kli status --name root1 --passcode ${PASSCODE} --alias Root
kli status --name gar1 --passcode ${PASSCODE} --alias GARs

# ---- OOBIs: signers -> GARs (delegator learns the delegate group AID) ----
# Now that the GARs inception is approved and anchored, the group AID is
# established and witness-receipted, so its OOBI resolves. Root resolves it so
# the delegate group is a first-class known contact (KEL + endpoints) rather
# than something rediscovered reactively when the drt arrives.
sleep 2  # let GARs gather witness receipts on its now-anchored dip
for signer in "${APPROVAL_SIGNERS[@]}"; do
    kli oobi resolve --name "${signer}" --passcode ${PASSCODE} --oobi-alias GARs --oobi ${WITNESS_HOST}/oobi/${GARS_PRE}/witness/${WIT}
done

# ---- Clear 1.1.x escrow residue so 1.2.x can open the keystore ----------
# Even after kli delegate confirm, 1.1.x leaves <prefix>.<digest> entries in
# Root's `pdes` (and similar) that 1.2.x's OnIoDup readers crash on. Every member
# now holds the Root group hab, so clear all seven.
for name in "${ROOT_NAMES[@]}"; do
    python3 ${KERI_DEMO_SCRIPT_DIR}/vLEI/clear-1.1-escrows.py "${name}"
done
