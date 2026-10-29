# Draft: witness query ownership and completion

This draft extends the HTTP connection cleanup in PR #62 with a per-query
`QueryAttempt`. It is an API and lifecycle proposal, **not ready to merge as a
complete migration of all query callers**.

## Ownership

```text
WitnessInquisitor
  ├─ queued requests and terminal results
  └─ QueryAttempt (one per dispatched request)
       ├─ explicit completion target
       ├─ 20-second dispatch + verification deadline
       └─ messenger, socket, and parser lifetime
```

The caller describes the state it needs. The attempt owns cleanup. Targets
inspect verified local state without consuming shared parser cues. They can be
satisfied by another receiver processing the same requested data; they do not
claim that this particular connection delivered it.

A target already satisfied at admission produces a `satisfied` result without
opening a connection or adding a synthetic `sent` notification. Otherwise the
attempt has one deadline, beginning when it is scheduled, covering both dispatch
and the response wait. Sending includes the introduction and query. After
successful dispatch, later requests can proceed while this attempt waits.

For HTTP, the messenger is removed once its response completes. The attempt can
continue watching state populated by the existing mailbox/parser. For TCP, the
messenger and parser remain scheduled until the target succeeds, transport
fails, the deadline expires, or the owner cancels the attempt. The teardown
runs in `finally`; completed attempts are also removed from the inquisitor.

## Call site

```python
from keri.app import agenting, querying

inquisitor = agenting.WitnessInquisitor(hby=hby, queryTimeout=20.0)
request = inquisitor.query(
    src=hab.pre,
    pre=issuer,
    sn=f"{required_sn:x}",
    completion=querying.KelTarget(
        pre=issuer, sn=required_sn, said=required_digest,
    ),
)
```

The existing `sent` queue still means local TCP send completion or an HTTP
response. It never means that the requested state was verified. A consumer
reads `results` for a terminal result, correlated by the original request:

```python
result = inquisitor.results.popleft()
assert result["query"] is request
# status: satisfied, failed, timed_out, cancelled, or legacy HTTP dispatched
# error: retained on failed/timed_out results, also exposed through failures
```

The caller must handle failures; scheduler completion alone is not success.
Removing a running attempt (or shutting down its inquisitor) cancels it and
closes its messenger. Cancellation does not erase data already accepted locally.

## Explicit targets

| Target | Accepted state inspected |
| --- | --- |
| `KelTarget(pre, sn, said=None)` | Local KEL has reached the position, and its accepted event matches the digest when specified |
| `AnchorTarget(pre, seal)` | Exact seal is present in an accepted, fully witnessed anchoring event |
| `KeyStateTarget(pre, source, sn, said)` | Saved notice from that source describes that exact state |
| `TelTarget(pre, sn, said)` | Exact event is in the verified TEL index; requires the inquisitor's `reger` |

These checks do not treat raw messages, parser buffers, or escrow entries as
completion. The key-state target is deliberately a pinned-state check. A cached
notice does not establish freshness. A TEL target describes a particular event,
not a claim that no later revocation exists.

## Compatibility and work remaining before merge

- Legacy HTTP requests without targets retain dispatch-only behavior and emit
  `dispatched`, never `satisfied`. TCP requests without a target now fail before
  opening the connection. This is an intentional, visible compatibility break.
- `LogQuerier`, `SeqNoQuerier`, and `AnchorQuerier` now supply concrete targets
  and reuse their predicates. Their outer completion/failure handling still
  needs conversion to the terminal-result contract.
- Audit and migrate direct callers in delegation, grouping, multisig CLI, IPEX,
  and downstream KERIA. Some already know an anchor or required event; others
  currently request an unspecified "latest" state.
- Define the freshness/discovery policy for "latest" and `KeyStateNoticer`.
  Do not interpret the existing default sequence zero as a sufficient target.
- This draft does not add reply/TEL dispatchers or escrow processing to
  `TCPMessenger`'s KEL parser. Key-state and TEL predicates are tested with the
  native validation paths, but their TCP query/response integration remains to
  be wired and tested. Existing external mailbox/validator ownership remains.
- Bound in-flight attempt admission for sustained concurrent workloads and
  qualify downstream load behavior. A deadline bounds lifetime, not concurrency.
- No automatic retry, endpoint failover, or wire-level replay terminator is added.

## Regression evidence

Real loopback TCP tests split a replay across reads, verify the connection
survives the gap, and check that three successive queries release sockets and
scheduled children. Other tests cover timeout after a successful send, terminal
transport failure, cancellation, HTTP socket cleanup before state completion,
progress of a later query during an earlier response wait, missing TCP targets,
and already-satisfied targets.

Target tests use accepted KEL events, a signed key-state reply through the native
parser, and TEL validation that first fails for a missing anchor and then
succeeds after anchoring. Existing HTTP and TCP witness tests remain included.
