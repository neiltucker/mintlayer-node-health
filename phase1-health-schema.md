# Phase 1 Node Health Schema

## Overview
This document defines the **Phase 1 Mintlayer Node Health Schema**.  
Phase 1 focuses on **read-only, low-risk, operational health signals** that can be safely exposed by node operators and consumed by dashboards, explorers, or monitoring systems.

**Design goals**
- Read-only
- No control-plane access
- Works with GUI or daemon deployments
- Pollable every 30 seconds
- Backward compatible

---

## Update Frequency
- Recommended polling interval: **30 seconds**
- Data is derived from logs and local system state

---

## Top-Level Structure

```json
{
  "timestamp": "ISO-8601 UTC",
  "overall_health": "healthy | degraded | initializing",
  "node": { ... },
  "chain": { ... },
  "peers": { ... },
  "consensus": { ... }
}
```

---

## Field Definitions

### timestamp
- **Type:** string (ISO-8601 UTC)
- **Description:** Time the health snapshot was generated

---

### overall_health
- **Type:** string
- **Allowed values:**
  - `healthy`
  - `degraded`
  - `initializing`
- **Derived from:**
  - Chain progress
  - Peer connectivity
  - Startup state
  - Fork compatibility

---

## node Object

```json
"node": {
  "version": "string | null",
  "network": "mainnet | testnet | null",
  "uptime_seconds": number | null
}
```

| Field | Description |
|------|------------|
| version | Node software version |
| network | Active network |
| uptime_seconds | Time since node startup |

---

## chain Object

```json
"chain": {
  "best_block": number | null,
  "last_block_seen_seconds_ago": number | null,
  "sync_stalled": boolean
}
```

| Field | Description |
|------|------------|
| best_block | Latest observed block height |
| last_block_seen_seconds_ago | Seconds since last new block |
| sync_stalled | True if block progress exceeds stall threshold |

**Recommended stall threshold:** 180 seconds

---

## peers Object

```json
"peers": {
  "count": number
}
```

| Field | Description |
|------|------------|
| count | Estimated connected peers |

---

## consensus Object

```json
"consensus": {
  "fork_compatible": boolean
}
```

| Field | Description |
|------|------------|
| fork_compatible | Whether node version is compatible with current network fork |

---

## Backward Compatibility
- New fields may be added
- Existing fields **must not be removed or renamed**
- Consumers should ignore unknown fields

---

## Phase 1 Scope Limitations
- No wallet data
- No balances
- No validator state
- No historical charts
- No write or RPC actions

---

## Intended Consumers
- Node operators
- Monitoring systems
- Mintlayer Explorer
- Network health dashboards
