#!/bin/bash
# Optional follow-on to Phase A: rotate the Root multisig group TWICE, each time
# carrying ALL SEVEN members forward but signed by a DIFFERENT 3-signer quorum, to
# exercise the weighted ["1/3"]x7 threshold and the carry-forward of non-signers.
#
# Root is a 7-member group; any three signatures satisfy it. setup-root-gars.sh had
# all seven sign the inception, so every member already holds the Root group hab and
# can co-sign. Both rotations here pass all seven members in smids/rmids; only the
# quorum signs:
#   Rotation 1 (sn=1 -> sn=2): root1/root2/root7 sign.
#   Rotation 2 (sn=2 -> sn=3): root3/root4/root5 sign  (disjoint from rotation 1).
#
# Rotation 2 demonstrates the carry-forward property: root3/root4/root5 did not sign
# rotation 1, but because they were carried in rotation 1's rmids (and rotated their
# own locals), their pre-committed next keys are live, so they can drive the next
# rotation. A signer that sat out the prior rotation is behind on the group KEL, so
# each quorum first syncs the Root group event before building.
#
# A group rotation reveals every member's pre-committed next key, so ALL seven members
# rotate their own local hab before EACH rotation; the signers then re-query everyone's
# new key state. Root is its own root of trust (no delegator), so these rotations need
# no external approval. (Root is establishment-only, but a rotation is an establishment
# event, so it is allowed.)
#
# Run AFTER setup-root-gars.sh, under kli 1.1.4x. It advances Root from sn=1 to sn=3.
#
# Prerequisites:
#   source scripts/demo/demo-scripts.sh
#   kli witness demo                # in another terminal
#   ./setup-root-gars.sh            # already run

WITNESS_HOST="http://127.0.0.1:5642"
WIT="BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha"

PASSCODE="${PASSCODE:-DoB26Fj4x9LboAFWJra17O}"

ROOT_NAMES=(root1 root2 root3 root4 root5 root6 root7)
ROOT_PRES=(
    EF11YNn4i0r0dX1KNrWs_ATQH878L3blwCMOSgwQVi57
    ENBdaRLJH7JOBAZo6aZbXelFP_I9yMd-RFrJ6pJ7V3CY
    EMEmbjR7mw0LvPk8co4q8Ks_0iX2anSnFu0NXh2WI80U
    ELAxo784aHZUWnRyd44VlkruUmiqQWc-pPYnZT-NtxLT
    EDoJYSnGXF6C2ftkcAWr4pBDDOPy3p6UDDPw2Mkm957u
    EMBkecmXbrbX_MOZnjbLi5DT975gPaMywbu_xRx3GZEH
    EESfhafScg-EQcdvmSxDKBZ9tZ31gRVpg9uR4sKZy4GD
)
# Root group AID (delegator). Signers sync this KEL before building, so a quorum that
# sat out the previous rotation catches up to the latest group event.
ROOT_PRE="ENeFvERfrz5_7n3kElLVA5BcTnuBqE1hpc0OyuV_pKXc"

# The two disjoint 3-signer quorums (any 3 satisfy ["1/3"]x7).
ROTATION_1_SIGNERS=(root1 root2 root7)
ROTATION_2_SIGNERS=(root3 root4 root5)
# Union of signers across both rotations, for the trailing escrow cleanup.
ALL_SIGNERS=(root1 root2 root7 root3 root4 root5)

# Build the --smids/--rmids argument lists: every member, in inception order, so each
# rotation carries the whole group forward.
SMIDS_ARGS=""
RMIDS_ARGS=""
for pre in "${ROOT_PRES[@]}"; do
    SMIDS_ARGS+=" --smids ${pre}"
    RMIDS_ARGS+=" --rmids ${pre}"
done

# rotate_root <signer1> <signer2> <signer3>
# Perform one all-7-carried-forward Root group rotation signed by the three given
# members. Every member rotates locally first (revealing the next key the prior group
# event committed); the signers sync the group KEL and every member's new local key
# state, then build the identical rotation event for the Counselor to merge.
rotate_root() {
    local signers=("$@")

    # Refuse to run if a previous rotate is still alive — concurrent rotates on the
    # same group jam the multisig signature exchange.
    if pgrep -f "kli multisig rotate.*--alias Root" > /dev/null; then
        echo "Stale 'kli multisig rotate --alias Root' processes are still running." >&2
        echo "Kill them first: pkill -f 'kli multisig rotate.*--alias Root'" >&2
        exit 1
    fi

    # Signers sync the Root group KEL to its latest sn. Required when a signer sat out
    # the previous rotation (different quorum) and is therefore behind on the group
    # event it must chain the new rotation onto. Idempotent for already-current signers.
    for signer in "${signers[@]}"; do
        kli query --name "${signer}" --passcode ${PASSCODE} --alias "${signer}" --prefix ${ROOT_PRE}
    done

    # Pre-rotate ALL members locally to reveal the next key the prior group event committed.
    for name in "${ROOT_NAMES[@]}"; do
        kli rotate --name "${name}" --passcode ${PASSCODE} --alias "${name}"
    done

    # Signers re-query every other member's new local key state.
    for signer in "${signers[@]}"; do
        for j in "${!ROOT_NAMES[@]}"; do
            member="${ROOT_NAMES[$j]}"
            [ "${signer}" = "${member}" ] && continue
            kli query --name "${signer}" --passcode ${PASSCODE} --alias "${signer}" --prefix ${ROOT_PRES[$j]}
        done
    done

    # Each signer builds the identical rotation event and contributes a signature; the
    # Counselor merges them and, once three are collected, publishes to witnesses.
    local pids=""
    for signer in "${signers[@]}"; do
        kli multisig rotate --name "${signer}" --passcode ${PASSCODE} --alias Root ${SMIDS_ARGS} ${RMIDS_ARGS} &
        pids+=" $!"
    done
    wait $pids
}

# ---- Rotation 1: sn=1 -> sn=2, signed by root1/root2/root7 --------------
rotate_root "${ROTATION_1_SIGNERS[@]}"
kli status --name "${ROTATION_1_SIGNERS[0]}" --passcode ${PASSCODE} --alias Root

# ---- Rotation 2: sn=2 -> sn=3, signed by root3/root4/root5 --------------
# A disjoint quorum: these three carried forward through rotation 1 without signing it,
# and now drive the next rotation off their pre-committed next keys.
rotate_root "${ROTATION_2_SIGNERS[@]}"
kli status --name "${ROTATION_2_SIGNERS[0]}" --passcode ${PASSCODE} --alias Root

# ---- Clear 1.1.x escrow residue for the signers ------------------------
# Leave the signer keystores ready to hand to citadel 1.2.x if desired. Each member's
# group hab only advances when it co-signs, so the keystores sit at different sns:
# root3/root4/root5 (rotation 2) are at sn=3; root1/root2/root7 (rotation 1) at sn=2;
# root6 (signed neither) at sn=1. Open root3/root4/root5 in citadel to see Root at sn=3.
for signer in "${ALL_SIGNERS[@]}"; do
    python3 ${KERI_DEMO_SCRIPT_DIR}/vLEI/clear-1.1-escrows.py "${signer}"
done
