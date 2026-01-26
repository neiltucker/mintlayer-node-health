import os
import json
import time
from datetime import datetime, timezone

# Location of the logs and output
LOG_DIR = os.path.expanduser("~/.mintlayer/mainnet/logs")
HEALTH_LOG = os.path.join(LOG_DIR, "mintlayer-health.log")
POLL_INTERVAL = 30  # seconds

def get_latest_log_file():
    daemon_log = os.path.join(LOG_DIR, "mintlayer-node-daemon.log")
    gui_log = os.path.join(LOG_DIR, "mintlayer-node-gui.log")

    files = []
    if os.path.exists(daemon_log):
        files.append(daemon_log)
    if os.path.exists(gui_log):
        files.append(gui_log)

    if not files:
        return None

    # Return the file with the latest modification time
    return max(files, key=os.path.getmtime)

def parse_log_file(file_path):
    """
    Parses the latest log file and extracts Phase 1 data.
    """
    # Initialize default JSON structure
    health_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_health": "initializing",
        "node": {
            "version": None,
            "network": None,
            "uptime_seconds": None
        },
        "chain": {
            "best_block": None,
            "last_block_seen_seconds_ago": None,
            "sync_stalled": False
        },
        "peers": {
            "count": 0
        },
        "consensus": {
            "fork_compatible": True
        },
        "errors": {
            "db_error": False,
            "panic": False
        }
    }

    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
    except Exception:
        return health_data

    # Example parsing logic (adjust regex or string matching as needed)
    for line in reversed(lines):  # Reverse to get the most recent entries first
        line = line.strip()

        # Node version
        if "Node version:" in line and health_data["node"]["version"] is None:
            health_data["node"]["version"] = line.split("Node version:")[-1].strip()

        # Network type
        if "Network:" in line and health_data["node"]["network"] is None:
            health_data["node"]["network"] = line.split("Network:")[-1].strip()

        # Uptime (in seconds)
        if "Uptime seconds:" in line and health_data["node"]["uptime_seconds"] is None:
            try:
                health_data["node"]["uptime_seconds"] = int(line.split("Uptime seconds:")[-1].strip())
            except ValueError:
                pass

        # Best block
        if "Best block:" in line and health_data["chain"]["best_block"] is None:
            health_data["chain"]["best_block"] = line.split("Best block:")[-1].strip()

        # Last block seen (seconds ago)
        if "Last block seen seconds ago:" in line and health_data["chain"]["last_block_seen_seconds_ago"] is None:
            try:
                health_data["chain"]["last_block_seen_seconds_ago"] = int(line.split("Last block seen seconds ago:")[-1].strip())
            except ValueError:
                pass

        # Peers count
        if "Connected peers:" in line and health_data["peers"]["count"] == 0:
            try:
                health_data["peers"]["count"] = int(line.split("Connected peers:")[-1].strip())
            except ValueError:
                pass

        # Sync stalled detection
        if "Sync stalled" in line:
            health_data["chain"]["sync_stalled"] = "true" in line.lower()

        # Optional: Detect overall health changes based on conditions
        if health_data["node"]["uptime_seconds"] is not None:
            if health_data["chain"]["last_block_seen_seconds_ago"] is not None:
                if health_data["chain"]["last_block_seen_seconds_ago"] > 60:
                    health_data["overall_health"] = "degraded"
                else:
                    health_data["overall_health"] = "healthy"

    return health_data

def write_health_log(data):
    try:
        with open(HEALTH_LOG, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error writing health log: {e}")

def main():
    while True:
        latest_file = get_latest_log_file()
        if latest_file:
            data = parse_log_file(latest_file)
            write_health_log(data)
        else:
            print("No log files found in:", LOG_DIR)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
