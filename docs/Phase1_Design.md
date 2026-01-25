## docs/Phase1_Design.md

# Phase 1 Design Overview

### Objectives
- Real-time monitoring of Mintlayer nodes
- Focused on critical metrics for node health, sync, fork compatibility, and availability
- Phase 1 only: No historical trends, no predictive alerts
- Refresh interval: 30 seconds for most metrics

### Phase 1 Scope
- Node identity & metadata
- Node software version & fork compatibility
- Sync & chain health
- Node availability & liveness
- Network connectivity
- Pool sanity checks
- Alerts for critical and warning conditions
- Delegator-facing health badges
- Polling is performed via a dedicated read-only HTTP endpoint on port 3033, leaving the primary node RPC port (3030) untouched.

### Phase 1 Benefits
- Prevents silent failures like the v1.2.0 incident
- Provides actionable data to operators and delegators
- Simple, lightweight, and ready for expansion in Phase 2

---
