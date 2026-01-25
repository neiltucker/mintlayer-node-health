## examples/Sample_JSON_Responses.md

# Sample JSON Responses (Note: the API is served on port 3033)

### Node Health
```json
{
  "node_id": "uuid-1234",
  "node_version": "v1.2.0",
  "fork_compatibility_status": "compatible",
  "local_block_height": 1234567,
  "network_block_height": 1234568,
  "sync_lag_blocks": 1,
  "sync_status": "synced",
  "online_status": true,
  "last_seen_at": "2026-01-25T12:34:56Z",
  "peer_count": 12,
  "peer_status": "healthy",
  "short_window_uptime_pct": 100,
  "pool_active": true,
  "has_delegations": true
}
```

### Node Alerts
```json
[
  {
    "alert_id": "uuid-5678",
    "node_id": "uuid-1234",
    "alert_type": "Low Peers",
    "severity": "warning",
    "first_triggered": "2026-01-25T12:30:00Z",
    "last_seen": "2026-01-25T12:34:56Z",
    "resolved": false
  }
]
```

---
