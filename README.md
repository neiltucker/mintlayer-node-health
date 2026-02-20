# Mintlayer Node Health Monitoring (Phase 1)

This project provides a read-only health monitoring system for Mintlayer nodes.

It enables node operators and network observers to:
- Verify node health
- Detect stalled syncs
- Confirm version compatibility
- Safely expose health status

## Design Philosophy

Mintlayer Node Health Monitor is intentionally designed to read **ONLY from log files**. 
This "read-only, local-only" approach ensures:

✅ **Maximum Security** - No RPC configuration required, no authentication secrets stored <br>
✅ **Zero Network Footprint** - The monitor makes no network connections<br>
✅ **Immediate Operation** - Works right after node installation with zero configuration<br>
✅ **Complete Transparency** - Anyone can audit that it only reads log files<br>
✅ **Universal Compatibility** - Works with any Mintlayer node deployment<br><br>

This design choice means the monitor focuses on what it can observe safely and reliably
from the logs, providing essential health metrics without introducing any additional
risk to your node operation.

## What This Monitor Does not Do

❌ **Access wallet balances** - Never connects to RPC or reads wallet files<br>
❌ **Modify node configuration** - Read-only access only<br>
❌ **Require authentication** - No credentials needed or stored<br><br>

For wallet balances and staking information, use the official Mintlayer Wallet CLI or RPC
commands directly. This monitor focuses on what it can observe reliably from logs alone.

A node is considered healthy if:
- Network activity has occurred within the last 5 minutes
- Chain synchronization is not stalled (≤ 10 minutes)
- At least one peer is connected
- Node version is fork-compatible
- No fatal or database errors are present

Network health degrades progressively as inactivity increases, allowing early detection before full outage.

--- 

## Components

### log_parser.py
- Polls Mintlayer node logs every 30 seconds
- Supports GUI and daemon logs
- Produces structured health snapshots
- Writes JSON lines to `mintlayer-health.log`

### health_api.py
- Read-only FastAPI service
- Serves latest health snapshot
- Provides historical inspection endpoints

---

## Directory Layout

```text
~/.mintlayer/mainnet/logs/
├── mintlayer-node-gui.log
├── mintlayer-node-daemon.log
└── mintlayer-health.log
```

---

## Health API Endpoints

| Endpoint | Description |
|-------|-------------|
| `/health` | Latest health snapshot |
| `/health/raw` | Raw health log entries |
| `/health/history` | Bounded history |
| `/status` | Liveness check |

---

## Security Model
- Read-only
- No RPC exposure
- No command execution
- Local-first deployment
- Optional firewall restriction

---

## Phase 1 Goals
- Operational visibility
- Upgrade readiness detection
- Network stability monitoring
- Explorer integration readiness

---

## Installation
```bash
# Clone the repository
git clone https://github.com/neiltucker/mintlayer-node-health.git
cd mintlayer-node-health

# Install dependencies
pip install -r requirements.txt

# ⚠️  SECURITY WARNING  ⚠️
# The health API will expose port 3033.  Configure your firewall to secure network access to this port.

# Run the health monitor
python log_parser.py &

# Start the API server (choose ONE option below):
python health_api.py

# Test endpoints (after starting the API):
curl -s http://127.0.0.1:3033/health | jq .  # Requires jq for pretty JSON
curl -I http://127.0.0.1:3033/ui/mintlayer-health-ui.html  # Check if UI exists
```
---

## Roadmap

### Phase 1 (Completed)
- Health schema
- Log-based telemetry
- Read-only API

### Phase 2 (Planned)
- RPC-based authoritative data
- Wallet & staking state
- Disk and DB health
- Alerting integrations






