## docs/Polling_Design.md

# Polling Scheduler Design

## Architecture
```
Scheduler
 ├── Version & Fork Poller        (slow-changing)
 ├── Sync & Chain Poller          (frequent)
 ├── Availability Poller          (frequent)
 ├── Peer Poller                  (frequent)
 └── Pool Sanity Poller           (infrequent)
```

## Polling Intervals
| Metric Group | Interval |
|-------------|----------|
| Availability / Online | 30s |
| Sync status / block height | 30s |
| Peer count | 30s |
| Node version | 5–10 min |
| Pool active / delegations | 2–5 min |

## Failure Handling
- Timeout: 3–5 seconds per poll
- Node marked offline after 2–3 consecutive failures
- Each poller fails independently

## Flow
```
for node in nodes:
    parallel:
        poll_availability()
        poll_sync()
        poll_peers()
        poll_version_if_needed()
        poll_pool_sanity_if_needed()
    update node_health_current
```

---
