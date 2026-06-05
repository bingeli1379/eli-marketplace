---
name: kafka-consumer-patterns
description: Use when building, reviewing, or debugging a Kafka consumer — delivery semantics, offset-commit strategy, consumer-group rebalancing, idempotent processing / dedup, poison-message / dead-letter handling, ordering, and backpressure. Load when a repo consumes from Kafka (any client: Confluent.Kafka, kafka-python/aiokafka, librdkafka, Spring Kafka, etc.).
user-invocable: false
---

# Kafka Consumer Patterns

Reliability patterns for the **consumer side** of Kafka. These are concept-level rules, independent of client library and version — translate them to the repo's actual client API by mirroring existing consumers (see `agent-guidelines` → "Match Existing Code"). Config names below are the canonical Kafka names; a given client may expose them under a slightly different key.

The single most important fact: **a correctly-built Kafka consumer is at-least-once, so it WILL see duplicates** (on rebalance, retry, or crash-before-commit). Reliability comes from making processing tolerate redelivery, not from trying to prevent it.

## 1. Delivery semantics — pick deliberately

| Semantic | How you get it | Use when |
|---|---|---|
| **At-most-once** | Commit offsets **before** processing | Rare — only if losing a message is acceptable and duplicates are not |
| **At-least-once** | Commit offsets **after** processing succeeds | **The default target.** Combine with idempotent processing (§4) |
| **Exactly-once** | Kafka transactions (§7) | Only for Kafka-to-Kafka consume-transform-produce; does NOT cover external side effects |

The common mistake is letting commit timing not match the semantic you actually want: committing **before** processing silently degrades to at-most-once (loss), while leaving auto-commit on **without** idempotent processing (§4) lets the guaranteed duplicates corrupt state.

## 2. Offset commits

- **Auto-commit (`enable.auto.commit=true`, default) is a trap for real processing.** It commits the offsets of the *previously polled* batch on a timer (`auto.commit.interval.ms`, default **5s**) during the next `poll()`. The headline risk is **duplicate reprocessing**: if you crash after processing a batch but before the next `poll()` commits it, the consumer resumes from the last committed position and re-reads those records. It still yields at-least-once **only if** you fully process every record from a `poll()` before calling the next `poll()`. **Silent message loss** is the narrower edge case — when offsets advance past records you have not finished handling (e.g. async/concurrent processing, or holding records across polls), the commit moves the position beyond unprocessed work.
- **For at-least-once: disable auto-commit and commit after processing.** Process the batch → commit. On crash before commit, the batch is redelivered (handled by §4 idempotency).
- **Sync vs async commit:**
  - `commitSync` — blocks, retries on retriable errors, lower throughput. Use on **shutdown** and in the **rebalance revocation callback** (you must not lose that commit).
  - `commitAsync` — fire-and-forget, higher throughput, **no retry**. Beware out-of-order: a failed async commit may be superseded by a later successful one. Pattern: `commitAsync` in the steady loop, `commitSync` once on close.
- Commit the offset of the **next** record to read (last-processed + 1) — most clients handle this, but verify when committing manually.
- Never commit past a record you have not successfully handled or routed to a DLQ (§5) — that is how "handled the error by skipping it" becomes data loss.

## 3. Consumer groups & rebalancing

- A topic's partitions are divided among the group's members; **effective parallelism is capped by partition count** (extra consumers sit idle).
- **Rebalance triggers:** a member joins, leaves, or is evicted (missed heartbeat / `max.poll.interval.ms` exceeded), or partitions/topics change.
- **Two phases: revocation → assignment.** The **revocation callback is your last chance to commit offsets** for partitions you are about to lose (`onPartitionsRevoked` / equivalent). Always commit there (`commitSync`).
- **Assignment strategy:** prefer **cooperative-sticky** (incremental rebalancing) over the legacy eager "stop-the-world" strategies — it avoids revoking all partitions on every membership change. Match what the consumer group already uses (all members must agree).
- **Liveness configs** (tune together):
  - `heartbeat.interval.ms` (~3s) — heartbeat cadence; keep ≲ 1/3 of `session.timeout.ms`.
  - `session.timeout.ms` (~45s since Kafka 3.0; was 10s pre-3.0) — coordinator evicts a member after this with no heartbeat. Larger = slower failure detection.
  - `max.poll.interval.ms` (~300s) — **max wall-clock between `poll()` calls.** Slow per-batch processing that blows this gets the consumer evicted → rebalance → the batch is reprocessed by someone else (duplicate work, possible livelock). Fixes: lower `max.poll.records`, move heavy work off the poll thread, or `pause()`/`resume()` (§6).

## 4. Idempotent processing / dedup (the core reliability pattern)

At-least-once guarantees duplicates, so **processing must be idempotent**. Options, in order of preference:

1. **Naturally idempotent writes** — upsert by a stable business key, `INSERT ... ON CONFLICT DO NOTHING`, set-to-value (not increment). Best: no extra state.
2. **Dedup on a business idempotency key** carried in the message (e.g. an event id) — check-and-record in the same transaction as the side effect.
3. **Dedup on `(topic, partition, offset)`** when there is no business key — durable, but only valid within one partition's stream.

Rules:
- Make the **side effect and the dedup record atomic** (same DB transaction). Recording "seen" but failing the write (or vice-versa) reintroduces the bug.
- Counters/aggregates must be idempotent (upsert absolute value, or dedup before incrementing) — naive `count += 1` double-counts on redelivery.
- External calls (HTTP, payment, email) are the danger zone: use the downstream's idempotency key if it has one; otherwise dedup before calling.

## 5. Poison messages & dead-letter handling

A record that always fails (bad payload, deserialization error, permanent downstream rejection) **must not block its partition forever**.

- Classify the failure: **transient** (network, timeout, 5xx) → retry with bounded backoff; **permanent** (validation, deserialization, 4xx) → do not retry in the loop.
- After bounded retries, **route to a dead-letter topic** (or a parking store) with context (original topic/partition/offset, error, timestamp), then commit past it so the partition progresses.
- **Never silently skip** a failed record without recording it somewhere and alerting — silent skip = invisible data loss.
- Handle **deserialization failures** before they crash the poll loop (many clients throw on poll); wrap deserialization and DLQ the raw bytes.

## 6. Ordering & backpressure

- **Ordering is per-partition only.** Records with the same **key** go to the same partition and are ordered; there is **no cross-partition ordering**. If order matters, key by the entity whose order must be preserved, and do not parallelize processing within a partition in a way that reorders.
- **Backpressure:** when a downstream is slow, do not just sit in processing and risk `max.poll.interval.ms`. Use `pause()`/`resume()` on partitions, or reduce `max.poll.records`, to keep polling (heartbeating) while bounding in-flight work.

## 7. Exactly-once (only when truly needed)

- For **Kafka-to-Kafka** consume-transform-produce: transactional producer (`transactional.id`, `enable.idempotence=true`), write output **and** consumed offsets in one transaction (`sendOffsetsToTransaction`), and set consumers downstream to `isolation.level=read_committed` so they never see aborted/uncommitted records.
- **EOS does not extend to external systems.** A DB write or HTTP call inside the consumer is still at-least-once — fall back to §4 idempotency for those. Do not claim exactly-once for a pipeline that touches a non-Kafka sink.

## 8. Operational must-knows

- **`auto.offset.reset`** (`latest` / `earliest` / `none`) decides where a **new** group or an expired offset starts — `latest` silently skips backlog, `earliest` reprocesses history. Choose per use case; `none` forces an explicit decision by erroring.
- **Monitor consumer lag** (committed offset vs log-end offset) — the primary health signal that a consumer is keeping up.
- **Schema evolution:** if a schema registry is used, respect its compatibility mode (backward/forward); consumers must tolerate the schemas producers will send. Deserialization of an unexpected schema is a poison-message case (§5).

## Anti-patterns (reject in review)

- Auto-commit left on for non-trivial processing → silent loss.
- Committing before processing succeeds (unless at-most-once is an explicit, documented choice).
- No idempotency on an at-least-once consumer → duplicates corrupt state.
- `catch (...) { /* skip */ }` in the poll loop → invisible data loss; route to DLQ instead.
- Heavy synchronous work on the poll thread exceeding `max.poll.interval.ms` → rebalance storms / livelock.
- Assuming global ordering across partitions.
- Claiming exactly-once for a pipeline with external (non-Kafka) side effects.

## Review checklist

- [ ] Delivery semantic is explicit and matches the commit timing
- [ ] Auto-commit disabled (or justified); offsets committed after processing
- [ ] `commitSync` on shutdown and in the revocation callback
- [ ] Processing is idempotent / dedups on a stable key; dedup + side effect are atomic
- [ ] Poison messages are bounded-retried then DLQ'd, never silently skipped
- [ ] Per-batch processing fits within `max.poll.interval.ms` (or uses pause/resume)
- [ ] Ordering assumptions hold given keying and partition count
- [ ] `auto.offset.reset` chosen deliberately; consumer lag is monitored

---

_Grounded in the Apache Kafka and Confluent consumer / delivery-semantics documentation. Config defaults (e.g. `auto.commit.interval.ms`=5s, `session.timeout.ms`≈45s since Kafka 3.0, `max.poll.interval.ms`=300s) are Kafka defaults — verify against the cluster/client version in use._
