## docs/Alert_Thresholds.md

# Alert Thresholds

## Critical Alerts
| Alert | Trigger |
|-------|--------|
| Node Offline | 2–3 consecutive failed polls |
| Fork Incompatible | Version < required |
| Sync Stalled | Block height unchanged ≥ 3 polls |
| Zero Peers | Peer count = 0 ≥ 2 polls |

## Warning Alerts
| Alert | Trigger |
|-------|--------|
| Low Peer Count | < 5 peers |
| Sync Lagging | Lag > 10 blocks |
| Version Unknown | Version not reported |
| Flapping Node | Online/offline repeatedly |

## Stability Rules
- Trigger after N consecutive polls
- Clear after M successful polls (e.g., trigger=2, clear=3)

## Alert Data Structure (`node_alerts`)
```sql
node_alerts (
    alert_id          UUID PRIMARY KEY,
    node_id           UUID NOT NULL,
    alert_type        TEXT NOT NULL,
    severity          TEXT NOT NULL,
    first_triggered   TIMESTAMP NOT NULL,
    last_seen         TIMESTAMP NOT NULL,
    resolved          BOOLEAN DEFAULT FALSE,
    resolution_time   TIMESTAMP,
    details           TEXT
)
```

---

