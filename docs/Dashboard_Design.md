## docs/Dashboard_Design.md

# Dashboard Wireframe (Phase 1)

## Header / Global Info Bar
```
Mintlayer Node Health Dashboard | Last Updated: 12:34:56
Total Pools: 24 | Nodes Online: 21 | Nodes Offline: 3
Min Required Version: v1.2.0
```

## Node Table Columns
- Status Dot (🟢/🟡/🔴)
- Health Badge (Healthy / Caution / Unhealthy)
- Pool ID / Name (clickable)
- Node Version
- Fork Compatibility (🟢/🔴/⚪)
- Sync Status (Synced / Syncing / Stalled)
- Block Lag
- Peer Count
- Short Uptime (% over 15 min)
- Last Seen (timestamp)

## Node Detail Panel
- Critical Info: Online status, Fork compatibility, Sync status
- Chain / Sync Details: Local & network block heights, lag
- Connectivity: Peer count, peer status, short uptime, last seen
- Pool / Delegation Info: Pool active, has delegations
- Alerts: Active alerts with type, severity, first triggered, duration

## Layout Overview
```
Header / Global Info Bar
Node Table (sortable/filterable)
Node Detail Panel (click row to open)
```

## Color Coding
- Green: healthy
- Yellow: minor warning
- Red: critical
- Gray: unknown/missing

## Note
- Monitoring traffic is isolated to port 3033 to reduce risk to the main RPC port (3030).

---
