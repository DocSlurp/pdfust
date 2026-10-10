# Independent concurrent metering review

Reviewed commit: `7725f44` (`bench/decision_concurrent.py` SHA-256
`21f8511b541c45b03bcb74ce0705181d78c85111f17ca406cc75928edc03ff31`).
The read-only review found no blocking financial race, automatic retry, secret
logging, or lost-charge path within the documented concurrent-wrapper contract.
This is a bounded review, not a production transport or provider billing test.

`tests/test_decision_concurrent_process.py` independently exercises two forked
processes sharing one persistent ledger. Both reserve USD 0.30 before overlapping
mock transports; the USD 0.60 wave cap blocks a third admission. Distinct indices
and reservation UUIDs survive settlement, and both positive USD 0.01 mock charges
remain recorded. The test bypasses client initialization, uses a fabricated key,
and performs no credential reads or network calls. Bounded synchronization and
cleanup prevent orphaned workers. Platforms without Unix fork skip this proof;
it does not demonstrate Windows locking semantics.

Measured on Linux 7.2.5-3-omarchy x86_64, glibc 2.44, Python 3.14.7, with one
pytest process and two forked workers: one test passed in 0.09 seconds; external
subprocess elapsed time was 0.3074 seconds. Python `resource.getrusage` for waited
children reported 0.273753 user CPU seconds, 0.036555 system CPU seconds, and
43,444 KiB maximum RSS. This is kernel process accounting without RSS sampling;
RSS is a maximum, not a sum of simultaneous process memory. These small mocked
measurements make no inference throughput or production memory claim.

Admission requires every participant in a wave to use the concurrent wrapper;
legacy admission does not enforce its wave policy. Historical prior-cost inputs
must remain immutable during the wave. Reservations must cover worst-case actual
charges: detecting an overrun blocks future admission but cannot undo requests
already in flight. Unresolved reservations remain charged against admission and
are never automatically expired or retransmitted. The retained test covers
successful settlement and cap contention; existing client tests separately cover
failure and recovery paths. No client implementation or existing test was edited.
