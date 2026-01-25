## docs/Data_Schemas.md

# Data Schemas

## 1. Node Metadata Schema (`nodes`)

```sql
nodes (
    node_id              UUID PRIMARY KEY,
    pool_id              TEXT NOT NULL,
    pool_address         TEXT NOT NULL,
    node_name            TEXT,
    operator_name        TEXT,
    network              TEXT NOT NULL,
    rpc_endpoint         TEXT NOT NULL,
    p2p_endpoint         TEXT,
    first_seen_at        TIMESTAMP NOT NULL,
    last_metadata_update TIMESTAMP NOT NULL
)
```

## 2. Node Health State Schema (`node_health_current`)

```sql
node_health_current (
    node_id                    UUID PRIMARY KEY,
    node_version               TEXT,
    min_required_version       TEXT,
    fork_compatibility_status  TEXT,
    local_block_height         BIGINT,
    network_block_height       BIGINT,
    sync_lag_blocks            BIGINT,
    sync_status                TEXT,
    online_status              BOOLEAN,
    last_seen_at               TIMESTAMP,
    short_window_uptime_pct    NUMERIC(5,2),
    peer_count                 INTEGER,
    peer_status                TEXT,
    pool_active                BOOLEAN,
    has_delegations            BOOLEAN,
    last_poll_at               TIMESTAMP NOT NULL,
    poll_error                 TEXT
)
```

### Notes
- `nodes` table: static metadata updated infrequently
- `node_health_current`: overwritten every poll, stores all dynamic metrics

---
