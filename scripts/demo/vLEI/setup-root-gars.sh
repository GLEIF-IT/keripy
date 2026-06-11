#!/bin/bash
# Phase A of the Root/GARs reproducer.
#
# Creates a 2-of-2 multisig "Root" AID and a 2-of-2 multisig "GARs" AID
# delegated from Root, anchors the GARs inception in Root's KEL via
# kli delegate confirm, and exits with the keystores in a quiescent state
# (no pending delegations in any escrow).
#
# Run under kli 1.1.4x. After this completes, point your 1.2.x software
# (citadel) at the root1/root2 keystores — its migration will run cleanly
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

# Hardcoded AIDs (must match what kli incept produces for the salts + JSON
# files below; also baked into data/multisig-root.json and data/multisig-gars.json).
ROOT1_PRE="EF11YNn4i0r0dX1KNrWs_ATQH878L3blwCMOSgwQVi57"
ROOT2_PRE="ENBdaRLJH7JOBAZo6aZbXelFP_I9yMd-RFrJ6pJ7V3CY"
GAR1_PRE="EM0Di_wQZhUA0uKsR0gC0bSnOxcroCX-JbUuX9TBcvA1"
GAR2_PRE="EA7cQdIZoCoQGWbjdVQYBVo4aNURsQml-vnEV8RMaSIG"
ROOT_PRE="ECbVd-kmWq0J8DHxLN6bKz3WbHtSl8RgeTD3VtnF9tQ4"
GARS_PRE="EAbWX_-KFnE51AB7pi9UJNDCQwjmPXvmzkB7RJJWv4pG"

# ---- Root locals --------------------------------------------------------
kli init --name root1 --passcode ${PASSCODE} --salt 0ACDEyMzQ1Njc4OWdoaWpdo1 --config-dir ${KERI_SCRIPT_DIR} --config-file demo-witness-oobis
kli incept --name root1 --passcode ${PASSCODE} --alias root1 --file ${KERI_DEMO_SCRIPT_DIR}/data/delegator-1.json

kli init --name root2 --passcode ${PASSCODE} --salt 0ACDEyMzQ1Njc4OWdoaWpdo2 --config-dir ${KERI_SCRIPT_DIR} --config-file demo-witness-oobis
kli incept --name root2 --passcode ${PASSCODE} --alias root2 --file ${KERI_DEMO_SCRIPT_DIR}/data/delegator-2.json

# ---- GAR locals ---------------------------------------------------------
kli init --name gar1 --passcode ${PASSCODE} --salt 0ACDEyMzQ1Njc4OWdoaWpdo3 --config-dir ${KERI_SCRIPT_DIR} --config-file demo-witness-oobis
kli incept --name gar1 --passcode ${PASSCODE} --alias gar1 --file ${KERI_DEMO_SCRIPT_DIR}/data/gars-1.json

kli init --name gar2 --passcode ${PASSCODE} --salt 0ACDEyMzQ1Njc4OWdoaWpdo4 --config-dir ${KERI_SCRIPT_DIR} --config-file demo-witness-oobis
kli incept --name gar2 --passcode ${PASSCODE} --alias gar2 --file ${KERI_DEMO_SCRIPT_DIR}/data/gars-2.json

# ---- OOBIs: root1 <-> root2 ---------------------------------------------
kli oobi resolve --name root1 --passcode ${PASSCODE} --oobi-alias root2 --oobi ${WITNESS_HOST}/oobi/${ROOT2_PRE}/witness/${WIT}
kli oobi resolve --name root2 --passcode ${PASSCODE} --oobi-alias root1 --oobi ${WITNESS_HOST}/oobi/${ROOT1_PRE}/witness/${WIT}

# ---- Multisig incept "Root" ---------------------------------------------
kli multisig incept --name root1 --passcode ${PASSCODE} --alias root1 --group Root --file ${KERI_DEMO_SCRIPT_DIR}/data/multisig-root.json &
PID_LIST+=" $!"
kli multisig incept --name root2 --passcode ${PASSCODE} --alias root2 --group Root --file ${KERI_DEMO_SCRIPT_DIR}/data/multisig-root.json &
PID_LIST+=" $!"
wait $PID_LIST
unset PID_LIST

# ---- OOBIs: gar1 <-> gar2 -----------------------------------------------
kli oobi resolve --name gar1 --passcode ${PASSCODE} --oobi-alias gar2 --oobi ${WITNESS_HOST}/oobi/${GAR2_PRE}/witness/${WIT}
kli oobi resolve --name gar2 --passcode ${PASSCODE} --oobi-alias gar1 --oobi ${WITNESS_HOST}/oobi/${GAR1_PRE}/witness/${WIT}

# ---- OOBIs: gar1, gar2 -> Root (the delegator) --------------------------
kli oobi resolve --name gar1 --passcode ${PASSCODE} --oobi-alias Root --oobi ${WITNESS_HOST}/oobi/${ROOT_PRE}/witness/${WIT}
kli oobi resolve --name gar2 --passcode ${PASSCODE} --oobi-alias Root --oobi ${WITNESS_HOST}/oobi/${ROOT_PRE}/witness/${WIT}

# ---- OOBIs: root1, root2 -> gar1, gar2 (delegator learns delegate members) --
# Out-of-band introduction of the GAR members to the Root delegator. Without
# this Root has no key state for the gar locals, so the later /delegate/request
# (drt) exn — signed by a gar member — arrives from an "unknown" sender and the
# delegator can't verify it. Resolving here makes each gar a known contact with
# known witness endpoints, so the drt-time refresh can target those endpoints
# instead of probing every configured witness pool.
kli oobi resolve --name root1 --passcode ${PASSCODE} --oobi-alias gar1 --oobi ${WITNESS_HOST}/oobi/${GAR1_PRE}/witness/${WIT}
kli oobi resolve --name root1 --passcode ${PASSCODE} --oobi-alias gar2 --oobi ${WITNESS_HOST}/oobi/${GAR2_PRE}/witness/${WIT}
kli oobi resolve --name root2 --passcode ${PASSCODE} --oobi-alias gar1 --oobi ${WITNESS_HOST}/oobi/${GAR1_PRE}/witness/${WIT}
kli oobi resolve --name root2 --passcode ${PASSCODE} --oobi-alias gar2 --oobi ${WITNESS_HOST}/oobi/${GAR2_PRE}/witness/${WIT}

# ---- Pre-rotate Root members so the group can rotate to approve ----------
# Root is establishment-only: it can only approve a delegation by anchoring the seal in a
# ROTATION (not an interaction). A group rotation's new keys are the members' pre-committed
# next keys, so each member must first rotate its own local hab (revealing those keys) and then
# learn the other member's new key state. Done BEFORE the GARs delegation so its wait timer
# does not run during these rotations.
kli rotate --name root1 --passcode ${PASSCODE} --alias root1
kli rotate --name root2 --passcode ${PASSCODE} --alias root2
kli query --name root1 --passcode ${PASSCODE} --alias root1 --prefix ${ROOT2_PRE}
kli query --name root2 --passcode ${PASSCODE} --alias root2 --prefix ${ROOT1_PRE}

# ---- Multisig incept "GARs" (delegated from Root) -----------------------
# Longer --wait: the rotation-anchored approval (group rotation + counselor + witness receipts)
# takes longer than the old interaction-anchored path.
kli multisig incept --name gar1 --passcode ${PASSCODE} --alias gar1 --group GARs --wait 90 --file ${KERI_DEMO_SCRIPT_DIR}/data/multisig-gars.json &
PID_LIST+=" $!"
kli multisig incept --name gar2 --passcode ${PASSCODE} --alias gar2 --group GARs --wait 90 --file ${KERI_DEMO_SCRIPT_DIR}/data/multisig-gars.json &
PID_LIST+=" $!"

# Give the delegation request time to reach Root members
sleep 3

# ---- Root approves the GARs inception -----------------------------------
# Root is establishment-only, so the approval must anchor in a rotation (no --interact).
kli delegate confirm --name root1 --passcode ${PASSCODE} --alias Root --auto &
PID_LIST+=" $!"
kli delegate confirm --name root2 --passcode ${PASSCODE} --alias Root --auto &
PID_LIST+=" $!"

wait $PID_LIST
unset PID_LIST

kli status --name root1 --passcode ${PASSCODE} --alias Root
kli status --name gar1 --passcode ${PASSCODE} --alias GARs

# ---- OOBIs: root1, root2 -> GARs (delegator learns the delegate group AID) --
# Now that the GARs inception is approved and anchored, the group AID is
# established and witness-receipted, so its OOBI resolves. Root resolves it so
# the delegate group is a first-class known contact (KEL + endpoints) rather
# than something rediscovered reactively when the drt arrives.
sleep 2  # let GARs gather witness receipts on its now-anchored dip
kli oobi resolve --name root1 --passcode ${PASSCODE} --oobi-alias GARs --oobi ${WITNESS_HOST}/oobi/${GARS_PRE}/witness/${WIT}
kli oobi resolve --name root2 --passcode ${PASSCODE} --oobi-alias GARs --oobi ${WITNESS_HOST}/oobi/${GARS_PRE}/witness/${WIT}

# ---- Clear 1.1.x escrow residue so 1.2.x can open the keystore ----------
# Even after kli delegate confirm, 1.1.x leaves <prefix>.<digest> entries in
# Root's `pdes` (and similar) that 1.2.x's OnIoDup readers crash on.
python3 ${KERI_DEMO_SCRIPT_DIR}/vLEI/clear-1.1-escrows.py root1
python3 ${KERI_DEMO_SCRIPT_DIR}/vLEI/clear-1.1-escrows.py root2
