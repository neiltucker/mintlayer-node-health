import os
import json
import time
import re
from datetime import datetime, timezone, timedelta
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

    return max(files, key=lambda x: x[1])[0]

def extract_timestamp_from_line(line):
    """Extract timestamp from log line - simplified and more robust"""
    try:
        # Look for ISO format timestamp at the beginning of the line (common in your logs)
        # Example: 2026-01-26T01:05:53.727505Z
        match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)', line)
        if match:
            dt = date_parser.parse(match.group(1))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
    except Exception:
        pass
    return None

def version_compare_simple(version_string):
    """Check if version is 1.2.0 or higher"""
    try:
        clean_version = version_string.lower().replace('v', '').strip()
        parts = clean_version.split('.')
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        return major > 1 or (major == 1 and minor >= 2)
    except Exception:
        return False

def calculate_network_status(process_block_seconds_ago):
    """Determine network status based on time since last process_block"""
    if process_block_seconds_ago is None:
        return "unknown"
    if process_block_seconds_ago < 300:
        return "optimal"
    elif process_block_seconds_ago < 600:
        return "normal"
    elif process_block_seconds_ago < 900:
        return "delayed"
    elif process_block_seconds_ago < 1800:
        return "degraded"
    else:
        return "offline"

def parse_log_file(file_path):
    """
    Parses the log file - simplified and more robust version
    """
    current_time = datetime.now(timezone.utc)
    
    # Initialize health data
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
        # Simple approach: read the whole file
        # For large files, this is still fine as log files are typically manageable
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading log file {file_path}: {e}")
        return health_data

    # Tracking variables
    active_peers = set()
    node_start_time = None
    latest_new_tip_time = None
    latest_new_tip_height = None
    latest_process_block_time = None
    
    # Track if we've seen any startup message
    startup_seen = False

    # Parse each line
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        line_timestamp = extract_timestamp_from_line(line_stripped)
        
        # DEBUG: Print first few lines to see what we're getting
        # Uncomment this to debug:
        # if len(lines) < 10 or lines.index(line) < 5:
        #     print(f"DEBUG - Line: {line_stripped[:100]}")

        # 1. PEER TRACKING
        # Look for peer connections in your specific log format
        # Example: "new peer accepted, peer_id: 37"
        if "new peer accepted" in line_stripped.lower():
            peer_match = re.search(r'peer_id:\s*(\d+)', line_stripped, re.IGNORECASE)
            if peer_match:
                active_peers.add(peer_match.group(1))
        
        # Look for disconnections
        if "peer disconnected" in line_stripped.lower():
            peer_match = re.search(r'peer_id:\s*(\d+)', line_stripped, re.IGNORECASE)
            if peer_match:
                peer_id = peer_match.group(1)
                if peer_id in active_peers:
                    active_peers.remove(peer_id)

        # 2. VERSION AND START TIME - CRITICAL FIX
        # Look for the exact startup message from your logs
        # Example: "Starting mintlayer-core version 1.2.0"
        if "starting mintlayer-core" in line_stripped.lower():
            startup_seen = True
            
            # Extract version
            version_match = re.search(r'version\s+([0-9.]+)', line_stripped, re.IGNORECASE)
            if version_match and health_data["node"]["version"] is None:
                health_data["node"]["version"] = version_match.group(1)
            
            # ALWAYS update start time when we see a startup message
            # This ensures we get the most recent one
            if line_timestamp:
                node_start_time = line_timestamp
                health_data["node"]["start_time"] = node_start_time.isoformat()
                print(f"DEBUG - Found startup at: {node_start_time}")  # Debug output

        # 3. CHAIN DATA
        # Look for NEW TIP messages from your logs
        # Example: "NEW TIP in chainstate ... with height 12345"
        if "new tip" in line_stripped.lower() and "height" in line_stripped.lower():
            height_match = re.search(r'height\s+(\d+)', line_stripped, re.IGNORECASE)
            if height_match and line_timestamp:
                latest_new_tip_height = height_match.group(1)
                latest_new_tip_time = line_timestamp
        
        # Look for process_block activity
        if "process_block" in line_stripped.lower() and line_timestamp:
            latest_process_block_time = line_timestamp

        # 4. ERROR DETECTION
        if "database error" in line_stripped.lower() or "db error" in line_stripped.lower() or "corruption" in line_stripped.lower():
            health_data["errors"]["db_error"] = True
        if "panic" in line_stripped.lower() or "fatal" in line_stripped.lower() or "crashed" in line_stripped.lower():
            health_data["errors"]["panic"] = True

    # Debug output
    if not startup_seen:
        print(f"WARNING: No startup message found in {file_path}")
    print(f"DEBUG - Found {len(active_peers)} active peers")
    print(f"DEBUG - Start time: {node_start_time}")

    # --- Calculations ---
    if node_start_time:
        uptime = current_time - node_start_time
        health_data["node"]["uptime_seconds"] = int(uptime.total_seconds())
    
    health_data["chain"]["best_block"] = latest_new_tip_height
    
    if latest_new_tip_time:
        age = int((current_time - latest_new_tip_time).total_seconds())
        health_data["chain"]["last_block_seen_seconds_ago"] = age
        health_data["chain"]["sync_stalled"] = age > STALL_THRESHOLD_SECONDS

    # Calculate network status based on process_block activity
    if latest_process_block_time:
        process_block_age = int((current_time - latest_process_block_time).total_seconds())
        health_data["node"]["network"] = calculate_network_status(process_block_age)
    else:
        # If no process_block found, use block time as fallback
        if latest_new_tip_time:
            process_block_age = int((current_time - latest_new_tip_time).total_seconds())
            health_data["node"]["network"] = calculate_network_status(process_block_age)
    
    # Set peers estimate
    health_data["peers"]["peers_estimate"] = len(active_peers)
    
    # Check fork compatibility
    if health_data["node"]["version"]:
        health_data["consensus"]["fork_compatible"] = version_compare_simple(health_data["node"]["version"])
    
    # Determine overall health
    health_data["overall_health"] = calculate_health_status(health_data)
    
    return health_data

def calculate_health_status(data):
    """Calculate overall health status based on all metrics"""
    if data["errors"]["panic"] or data["errors"]["db_error"]:
        return "critical"
    
    if not data["consensus"]["fork_compatible"] and data["node"]["version"] is not None:
        return "critical"
    
    if data["node"]["version"] is None:
        return "unknown"
    
    network_status = data["node"].get("network")
    if network_status == "offline":
        return "critical"
    
    if network_status in ["degraded", "delayed"] or data["chain"]["sync_stalled"] or data["peers"]["peers_estimate"] == 0:
        return "degraded"
    
    return "healthy"

def write_health_log(data):
    """Write health data to log file and console"""
    try:
        ensure_log_dir()
        with open(HEALTH_LOG, "a") as f:
            json.dump(data, f, separators=(',', ':'))
            f.write('\n')
        
        # Format uptime for display
        uptime = data["node"]["uptime_seconds"]
        if uptime:
            uptime_str = str(timedelta(seconds=uptime))
            # Simplify uptime string
            uptime_str = uptime_str.split('.')[0]  # Remove microseconds
        else:
            uptime_str = "N/A"
        
        fork_status = "✓" if data["consensus"]["fork_compatible"] else "✗"
        print(f"[{data['timestamp']}] Health: {data['overall_health']} | "
              f"Peers: {data['peers']['peers_estimate']} | "
              f"Fork: {fork_status} | "
              f"Uptime: {uptime_str}")
    except Exception as e:
        print(f"Error writing health log: {e}")

def main():
    ensure_log_dir()
    print(f"Mintlayer Node Health Monitor started (polling every {POLL_INTERVAL}s)")
    print(f"Monitoring logs in: {LOG_DIR}")
    
    while True:
        try:
            latest_file = get_latest_log_file()
            if latest_file:
                print(f"DEBUG - Reading log file: {latest_file}")
                data = parse_log_file(latest_file)
                write_health_log(data)
            else:
                print(f"No log files found in {LOG_DIR}")
            
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("\nShutting down...")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
