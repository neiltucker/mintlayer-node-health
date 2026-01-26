import os
import json
import time
import re
from datetime import datetime, timezone

# Location of the logs and output
LOG_DIR = os.path.expanduser("~/.mintlayer/mainnet/logs")
HEALTH_LOG = os.path.join(LOG_DIR, "mintlayer-health.log")
POLL_INTERVAL = 30  # seconds

def ensure_log_dir():
    """Ensure the log directory exists"""
    os.makedirs(LOG_DIR, exist_ok=True)

def get_latest_log_file():
    """Get the most recently modified log file"""
    daemon_log = os.path.join(LOG_DIR, "mintlayer-node-daemon.log")
    gui_log = os.path.join(LOG_DIR, "mintlayer-node-gui.log")

    files = []
    if os.path.exists(daemon_log):
        files.append((daemon_log, os.path.getmtime(daemon_log)))
    if os.path.exists(gui_log):
        files.append((gui_log, os.path.getmtime(gui_log)))

    if not files:
        return None

    # Return the file with the latest modification time
    return max(files, key=lambda x: x[1])[0]

def parse_log_file(file_path):
    """
    Parses the latest log file and extracts Phase 1 data.
    Uses flexible regex patterns to match various log formats.
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
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            # Read last 50KB to avoid loading huge files
            try:
                f.seek(-51200, 2)
            except OSError:
                f.seek(0)
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading log file {file_path}: {e}")
        return health_data

    # Patterns to match various log formats
    patterns = {
        "version": [
            r"(?:Node\s+)?version[:\s]+([v\d\.]+)",
            r"mintlayer.*?([v\d\.]+)",
        ],
        "network": [
            r"Network[:\s]+(\w+)",
            r"network[=:\s]+(\w+)",
        ],
        "uptime": [
            r"(?:Uptime|uptime)[:\s]+(\d+)(?:\s*seconds?)?",
            r"running\s+for\s+(\d+)\s*sec",
        ],
        "block": [
            r"(?:Best|Current|Latest)\s+block[:\s#]+(\d+)",
            r"block\s+height[:\s]+(\d+)",
        ],
        "block_time": [
            r"(?:Last\s+block\s+seen|Block\s+age)[:\s]+(\d+)(?:\s*seconds?)?",
            r"seconds?\s+since\s+last\s+block[:\s]+(\d+)",
        ],
        "peers": [
            r"(?:Connected\s+)?peers?[:\s]+(\d+)",
            r"peer\s+count[:\s]+(\d+)",
        ],
    }

    # Parse from most recent entries first
    for line in reversed(lines[-500:]):  # Check last 500 lines
        line = line.strip()
        
        # Node version
        if health_data["node"]["version"] is None:
            for pattern in patterns["version"]:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    health_data["node"]["version"] = match.group(1)
                    break

        # Network type
        if health_data["node"]["network"] is None:
            for pattern in patterns["network"]:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    health_data["node"]["network"] = match.group(1)
                    break

        # Uptime
        if health_data["node"]["uptime_seconds"] is None:
            for pattern in patterns["uptime"]:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        health_data["node"]["uptime_seconds"] = int(match.group(1))
                    except ValueError:
                        pass
                    break

        # Best block
        if health_data["chain"]["best_block"] is None:
            for pattern in patterns["block"]:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    health_data["chain"]["best_block"] = match.group(1)
                    break

        # Last block time
        if health_data["chain"]["last_block_seen_seconds_ago"] is None:
            for pattern in patterns["block_time"]:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        health_data["chain"]["last_block_seen_seconds_ago"] = int(match.group(1))
                    except ValueError:
                        pass
                    break

        # Peers count
        if health_data["peers"]["count"] == 0:
            for pattern in patterns["peers"]:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        health_data["peers"]["count"] = int(match.group(1))
                    except ValueError:
                        pass
                    break

        # Error detection
        if re.search(r"database\s+error|db\s+error|corruption", line, re.IGNORECASE):
            health_data["errors"]["db_error"] = True
        
        if re.search(r"panic|fatal|crashed", line, re.IGNORECASE):
            health_data["errors"]["panic"] = True
        
        # Sync stalled detection
        if re.search(r"sync\s+stall", line, re.IGNORECASE):
            health_data["chain"]["sync_stalled"] = True

    # Determine overall health status
    health_data["overall_health"] = calculate_health_status(health_data)

    return health_data

def calculate_health_status(data):
    """Calculate overall health status based on metrics"""
    # Check for critical errors
    if data["errors"]["panic"]:
        return "critical"
    if data["errors"]["db_error"]:
        return "critical"
    
    # Check if we have basic data
    if data["node"]["version"] is None:
        return "unknown"
    
    # Check sync status
    last_block_time = data["chain"]["last_block_seen_seconds_ago"]
    if last_block_time is not None:
        if last_block_time > 300:  # 5 minutes
            return "degraded"
        elif last_block_time > 600:  # 10 minutes
            return "critical"
    
    # Check if sync is stalled
    if data["chain"]["sync_stalled"]:
        return "degraded"
    
    # Check peer count
    if data["peers"]["count"] == 0:
        return "degraded"
    
    # All checks passed
    return "healthy"

def write_health_log(data):
    """Append health data as a new JSON line to the log file"""
    try:
        ensure_log_dir()
        # Append mode - each entry is a complete JSON object on its own line
        with open(HEALTH_LOG, "a") as f:
            json.dump(data, f, separators=(',', ':'))
            f.write('\n')
        print(f"Health data written at {data['timestamp']}: {data['overall_health']}")
    except Exception as e:
        print(f"Error writing health log: {e}")

def main():
    """Main polling loop"""
    ensure_log_dir()
    print(f"Starting Mintlayer log parser. Polling every {POLL_INTERVAL} seconds...")
    print(f"Looking for logs in: {LOG_DIR}")
    print(f"Writing health data to: {HEALTH_LOG}")
    
    while True:
        try:
            latest_file = get_latest_log_file()
            if latest_file:
                print(f"Parsing: {latest_file}")
                data = parse_log_file(latest_file)
                write_health_log(data)
            else:
                print(f"No log files found in: {LOG_DIR}")
                # Still write a log entry indicating no data
                data = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "overall_health": "unknown",
                    "node": {"version": None, "network": None, "uptime_seconds": None},
                    "chain": {"best_block": None, "last_block_seen_seconds_ago": None, "sync_stalled": False},
                    "peers": {"count": 0},
                    "consensus": {"fork_compatible": True},
                    "errors": {"db_error": False, "panic": False}
                }
                write_health_log(data)
        except Exception as e:
            print(f"Error in main loop: {e}")
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
