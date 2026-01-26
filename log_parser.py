import os
import json
import time
import re
from datetime import datetime, timezone
from dateutil import parser as date_parser

# Location of the logs and output
LOG_DIR = os.path.expanduser("~/.mintlayer/mainnet/logs")
HEALTH_LOG = os.path.join(LOG_DIR, "mintlayer-health.log")
POLL_INTERVAL = 30  # seconds

# Thresholds
STALL_THRESHOLD_SECONDS = 600  # 10 minutes

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

def extract_timestamp_from_line(line):
    """
    Extract timestamp from log line.
    Assumes format like: 2025-01-26 14:30:45 [INFO] message
    or ISO format timestamps
    """
    try:
        # Try to find ISO format or common log timestamp patterns
        timestamp_patterns = [
            r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)',
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
        ]
        
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                timestamp_str = match.group(1)
                # Parse the timestamp
                dt = date_parser.parse(timestamp_str)
                # Ensure it's timezone-aware (assume UTC if not specified)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
    except Exception:
        pass
    return None

def version_compare_simple(version_string):
    """
    Check if version >= 1.2.0
    Returns True if version >= 1.2.0, False otherwise.
    """
    try:
        # Remove 'v' prefix if present and extract numbers
        clean_version = version_string.lower().replace('v', '').strip()
        parts = clean_version.split('.')
        
        # Parse major, minor, patch
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        
        # Compare against 1.2.0
        if major > 1:
            return True
        elif major == 1 and minor >= 2:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error parsing version '{version_string}': {e}")
        return False

def calculate_network_status(process_block_seconds_ago):
    """
    Calculate network status based on time since last process_block
    < 60 seconds: Optimal
    1-2 minutes: Normal
    2-5 minutes: Delayed
    5-10 minutes: Degraded
    > 10 minutes: Offline
    """
    if process_block_seconds_ago is None:
        return "unknown"
    
    if process_block_seconds_ago < 60:
        return "optimal"
    elif process_block_seconds_ago < 120:
        return "normal"
    elif process_block_seconds_ago < 300:
        return "delayed"
    elif process_block_seconds_ago < 600:
        return "degraded"
    else:
        return "offline"

def parse_log_file(file_path):
    """
    Parses the latest log file and extracts Phase 1 data using robust criteria.
    """
    current_time = datetime.now(timezone.utc)
    
    # Initialize default JSON structure
    health_data = {
        "timestamp": current_time.isoformat(),
        "overall_health": "initializing",
        "node": {
            "version": None,
            "network": None,
            "uptime_seconds": None,
            "start_time": None
        },
        "chain": {
            "best_block": None,
            "last_block_seen_seconds_ago": None,
            "sync_stalled": False
        },
        "peers": {
            "peers_estimate": 0
        },
        "consensus": {
            "fork_compatible": False
        },
        "errors": {
            "db_error": False,
            "panic": False
        }
    }

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading log file {file_path}: {e}")
        return health_data

    # Track peer connections for estimate
    peer_accepted_count = 0
    peer_disconnected_count = 0
    
    # Variables to track
    node_start_time = None
    latest_new_tip_time = None
    latest_new_tip_height = None
    latest_process_block_time = None

    # Parse through all lines
    for line in lines:
        line_stripped = line.strip()
        
        # Extract line timestamp for time-based calculations
        line_timestamp = extract_timestamp_from_line(line)
        
        # 1. VERSION: "Starting mintlayer-core version 1.2.0"
        if health_data["node"]["version"] is None:
            version_match = re.search(r'Starting\s+mintlayer-core\s+version\s+([0-9.]+)', line_stripped, re.IGNORECASE)
            if version_match:
                health_data["node"]["version"] = version_match.group(1)
        
        # 2. START TIME: Look for node start indicators
        if node_start_time is None:
            if re.search(r'Starting\s+mintlayer', line_stripped, re.IGNORECASE):
                node_start_time = line_timestamp
                if node_start_time:
                    health_data["node"]["start_time"] = node_start_time.isoformat()
        
        # 3. BEST BLOCK: "NEW TIP in chainstate ... with height 518564"
        new_tip_match = re.search(r'NEW\s+TIP\s+in\s+chainstate\s+\w+\s+with\s+height\s+(\d+)', line_stripped, re.IGNORECASE)
        if new_tip_match:
            height = new_tip_match.group(1)
            # Keep the latest one (last in file)
            latest_new_tip_height = height
            latest_new_tip_time = line_timestamp
        
        # 4. NETWORK STATUS: Look for process_block timestamps
        if re.search(r'process_block', line_stripped, re.IGNORECASE):
            if line_timestamp:
                latest_process_block_time = line_timestamp
        
        # 5. PEER TRACKING
        if re.search(r'new\s+peer\s+accepted|peer\s+connection\s+accepted', line_stripped, re.IGNORECASE):
            peer_accepted_count += 1
        
        if re.search(r'peer\s+disconnected|connection\s+closed', line_stripped, re.IGNORECASE):
            peer_disconnected_count += 1
        
        # 6. ERROR DETECTION
        if re.search(r'database\s+error|db\s+error|corruption|database.*fail', line_stripped, re.IGNORECASE):
            health_data["errors"]["db_error"] = True
        
        if re.search(r'panic|fatal|crashed|thread.*panicked', line_stripped, re.IGNORECASE):
            health_data["errors"]["panic"] = True

    # Calculate derived values
    
    # UPTIME: Current time - start time
    if node_start_time:
        uptime_delta = current_time - node_start_time
        health_data["node"]["uptime_seconds"] = int(uptime_delta.total_seconds())
    
    # BEST BLOCK
    if latest_new_tip_height:
        health_data["chain"]["best_block"] = latest_new_tip_height
    
    # LAST BLOCK SEEN SECONDS AGO
    if latest_new_tip_time:
        time_since_tip = current_time - latest_new_tip_time
        health_data["chain"]["last_block_seen_seconds_ago"] = int(time_since_tip.total_seconds())
    
    # SYNC STALLED
    if health_data["chain"]["last_block_seen_seconds_ago"] is not None:
        if health_data["chain"]["last_block_seen_seconds_ago"] > STALL_THRESHOLD_SECONDS:
            health_data["chain"]["sync_stalled"] = True
        else:
            health_data["chain"]["sync_stalled"] = False
    
    # NETWORK STATUS (based on process_block activity)
    process_block_age = None
    if latest_process_block_time:
        time_since_process = current_time - latest_process_block_time
        process_block_age = int(time_since_process.total_seconds())
    
    health_data["node"]["network"] = calculate_network_status(process_block_age)
    
    # PEERS ESTIMATE
    health_data["peers"]["peers_estimate"] = min(max(0, peer_accepted_count - peer_disconnected_count),12)
    
    # FORK COMPATIBLE (version must be >= 1.2.0)
    if health_data["node"]["version"]:
        health_data["consensus"]["fork_compatible"] = version_compare_simple(
            health_data["node"]["version"]
        )
    else:
        health_data["consensus"]["fork_compatible"] = False
    
    # OVERALL HEALTH
    health_data["overall_health"] = calculate_health_status(health_data)

    return health_data

def calculate_health_status(data):
    """Calculate overall health status based on metrics"""
    # Critical errors take priority
    if data["errors"]["panic"]:
        return "critical"
    if data["errors"]["db_error"]:
        return "critical"
    
    # Fork compatibility is critical
    if not data["consensus"]["fork_compatible"]:
        return "critical"
    
    # Check if we have basic data
    if data["node"]["version"] is None:
        return "unknown"
    
    # Network status affects health
    network_status = data["node"].get("network")
    if network_status == "offline":
        return "critical"
    elif network_status in ["degraded", "delayed"]:
        return "degraded"
    
    # Sync stalled
    if data["chain"]["sync_stalled"]:
        return "degraded"
    
    # Low peer count
    if data["peers"]["peers_estimate"] == 0:
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
        
        # Print summary
        fork_status = "✓" if data["consensus"]["fork_compatible"] else "✗"
        error_flags = []
        if data["errors"]["db_error"]:
            error_flags.append("DB_ERROR")
        if data["errors"]["panic"]:
            error_flags.append("PANIC")
        error_str = " [" + ",".join(error_flags) + "]" if error_flags else ""
        
        print(f"[{data['timestamp']}]")
        print(f"  Health: {data['overall_health']} | Version: {data['node']['version']} | Fork: {fork_status}")
        print(f"  Network: {data['node']['network']} | Block: {data['chain']['best_block']} | "
              f"Peers: {data['peers']['peers_estimate']}{error_str}")
        print()
    except Exception as e:
        print(f"Error writing health log: {e}")

def main():
    """Main polling loop"""
    ensure_log_dir()
    print("=" * 70)
    print("Mintlayer Node Health Monitor - Log Parser (Enhanced)")
    print("=" * 70)
    print(f"Polling interval: {POLL_INTERVAL} seconds")
    print(f"Log directory: {LOG_DIR}")
    print(f"Health log: {HEALTH_LOG}")
    print(f"Stall threshold: {STALL_THRESHOLD_SECONDS} seconds")
    print("=" * 70)
    print("\nMETRICS CALCULATED:")
    print("  - version: From 'Starting mintlayer-core version X.X.X'")
    print("  - network: Based on process_block timestamp age")
    print("  - uptime_seconds: Current time - node start time")
    print("  - best_block: Height from most recent 'NEW TIP in chainstate'")
    print("  - last_block_seen_seconds_ago: Current time - NEW TIP timestamp")
    print("  - sync_stalled: True if last_block_seen > 600 seconds")
    print("  - peers_estimate: 'peer accepted' - 'peer disconnected'")
    print("  - fork_compatible: True if version >= 1.2.0")
    print("=" * 70)
    print()
    
    while True:
        try:
            latest_file = get_latest_log_file()
            if latest_file:
                print(f"Parsing: {latest_file}")
                data = parse_log_file(latest_file)
                write_health_log(data)
            else:
                print(f"No log files found in: {LOG_DIR}")
                # Write unknown status
                data = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "overall_health": "unknown",
                    "node": {"version": None, "network": "unknown", "uptime_seconds": None, "start_time": None},
                    "chain": {"best_block": None, "last_block_seen_seconds_ago": None, "sync_stalled": False},
                    "peers": {"peers_estimate": 0},
                    "consensus": {"fork_compatible": False},
                    "errors": {"db_error": False, "panic": False}
                }
                write_health_log(data)
        except Exception as e:
            print(f"Error in main loop: {e}")
            import traceback
            traceback.print_exc()
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
