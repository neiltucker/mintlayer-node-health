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

    return max(files, key=lambda x: x[1])[0]

def extract_timestamp_from_line(line):
    try:
        timestamp_patterns = [
            r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)',
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
        ]
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                dt = date_parser.parse(match.group(1))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
    except Exception:
        pass
    return None

def version_compare_simple(version_string):
    try:
        clean_version = version_string.lower().replace('v', '').strip()
        parts = clean_version.split('.')
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        return major > 1 or (major == 1 and minor >= 2)
    except Exception:
        return False

def calculate_network_status(process_block_seconds_ago):
    if process_block_seconds_ago is None: return "unknown"
    if process_block_seconds_ago < 300: return "optimal"
    elif process_block_seconds_ago < 600: return "normal"
    elif process_block_seconds_ago < 900: return "delayed"
    elif process_block_seconds_ago < 1800: return "degraded"
    else: return "offline"

def parse_log_file(file_path):
    """
    Parses the log file using peer_id tracking for higher accuracy.
    """
    current_time = datetime.now(timezone.utc)
    
    health_data = {
        "timestamp": current_time.isoformat(),
        "overall_health": "initializing",
        "node": {"version": None, "network": None, "uptime_seconds": None, "start_time": None},
        "chain": {"best_block": None, "last_block_seen_seconds_ago": None, "sync_stalled": False},
        "peers": {"peers_estimate": 0},
        "consensus": {"fork_compatible": False},
        "errors": {"db_error": False, "panic": False}
    }

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading log file {file_path}: {e}")
        return health_data

    # --- Tracking Unique Peers ---
    active_peers = set()
    
    node_start_time = None
    latest_new_tip_time = None
    latest_new_tip_height = None
    latest_process_block_time = None

    for line in lines:
        line_stripped = line.strip()
        line_timestamp = extract_timestamp_from_line(line)
        
        # 1. PEER TRACKING (Updated Logic)
        # Search for: "new peer accepted, peer_id: 1"
        connect_match = re.search(r'new\s+peer\s+accepted,\s+peer_id:\s+(\d+)', line_stripped)
        if connect_match:
            active_peers.add(connect_match.group(1))

        # Search for: "peer disconnected, peer_id: 1" OR "Connection closed for peer 1"
        disconnect_match = re.search(r'(?:peer\s+disconnected,\s+peer_id:|Connection\s+closed\s+for\s+peer)\s+(\d+)', line_stripped)
        if disconnect_match:
            peer_id = disconnect_match.group(1)
            if peer_id in active_peers:
                active_peers.remove(peer_id)

        # 2. VERSION & START TIME
        if health_data["node"]["version"] is None:
            version_match = re.search(r'Starting\s+mintlayer-core\s+version\s+([0-9.]+)', line_stripped, re.IGNORECASE)
            if version_match:
                health_data["node"]["version"] = version_match.group(1)
        
        if node_start_time is None and re.search(r'Starting\s+mintlayer', line_stripped, re.IGNORECASE):
            node_start_time = line_timestamp
            if node_start_time:
                health_data["node"]["start_time"] = node_start_time.isoformat()
        
        # 3. CHAIN DATA
        new_tip_match = re.search(r'NEW\s+TIP\s+in\s+chainstate\s+\w+\s+with\s+height\s+(\d+)', line_stripped, re.IGNORECASE)
        if new_tip_match:
            latest_new_tip_height = new_tip_match.group(1)
            latest_new_tip_time = line_timestamp
        
        if re.search(r'process_block', line_stripped, re.IGNORECASE):
            if line_timestamp:
                latest_process_block_time = line_timestamp
        
        # 4. ERROR DETECTION
        if re.search(r'database\s+error|db\s+error|corruption|database.*fail', line_stripped, re.IGNORECASE):
            health_data["errors"]["db_error"] = True
        if re.search(r'panic|fatal|crashed|thread.*panicked', line_stripped, re.IGNORECASE):
            health_data["errors"]["panic"] = True

    # --- Calculations ---
    if node_start_time:
        health_data["node"]["uptime_seconds"] = int((current_time - node_start_time).total_seconds())
    
    health_data["chain"]["best_block"] = latest_new_tip_height
    
    if latest_new_tip_time:
        age = int((current_time - latest_new_tip_time).total_seconds())
        health_data["chain"]["last_block_seen_seconds_ago"] = age
        health_data["chain"]["sync_stalled"] = age > STALL_THRESHOLD_SECONDS

    process_block_age = int((current_time - latest_process_block_time).total_seconds()) if latest_process_block_time else None
    health_data["node"]["network"] = calculate_network_status(process_block_age)
    
    # PEERS ESTIMATE (Now based on the set of unique IDs)
    health_data["peers"]["peers_estimate"] = len(active_peers)
    
    if health_data["node"]["version"]:
        health_data["consensus"]["fork_compatible"] = version_compare_simple(health_data["node"]["version"])
    
    health_data["overall_health"] = calculate_health_status(health_data)
    return health_data

def calculate_health_status(data):
    if data["errors"]["panic"] or data["errors"]["db_error"] or not data["consensus"]["fork_compatible"]:
        return "critical"
    if data["node"]["version"] is None:
        return "unknown"
    
    network_status = data["node"].get("network")
    if network_status == "offline": return "critical"
    if network_status in ["degraded", "delayed"] or data["chain"]["sync_stalled"] or data["peers"]["peers_estimate"] == 0:
        return "degraded"
    
    return "healthy"

def write_health_log(data):
    try:
        ensure_log_dir()
        with open(HEALTH_LOG, "a") as f:
            json.dump(data, f, separators=(',', ':'))
            f.write('\n')
        
        fork_status = "✓" if data["consensus"]["fork_compatible"] else "✗"
        print(f"[{data['timestamp']}] Health: {data['overall_health']} | Peers: {data['peers']['peers_estimate']} | Fork: {fork_status}")
    except Exception as e:
        print(f"Error writing health log: {e}")

def main():
    ensure_log_dir()
    while True:
        latest_file = get_latest_log_file()
        if latest_file:
            data = parse_log_file(latest_file)
            write_health_log(data)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
