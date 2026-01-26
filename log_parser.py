import os
import re
from datetime import datetime

# Full logs path in the home directory
LOGS_DIR = os.path.expanduser("~/.mintlayer/mainnet/logs")
DAEMON_LOG = "mintlayer-node-daemon.log"
GUI_LOG = "mintlayer-node-gui.log"
HEALTH_LOG = "mintlayer-health.log"

# Regex patterns for structured extraction
BLOCK_PATTERN = re.compile(
    r'NEW TIP in chainstate (\w+).*height (\d+), timestamp: (\d+)'
)
PEER_PATTERN = re.compile(
    r'new peer accepted, peer_id: (\d+), address: SocketAddress\((.*?)\), role: (\w+), protocol_version: (\w+)'
)
ERROR_PATTERN = re.compile(
    r'Failed to establish connection to SocketAddress\((.*?)\): (.*)'
)

def get_most_recent_log(logs_dir):
    daemon_path = os.path.join(logs_dir, DAEMON_LOG)
    gui_path = os.path.join(logs_dir, GUI_LOG)

    files = []
    if os.path.exists(daemon_path):
        files.append((daemon_path, os.path.getmtime(daemon_path)))
    if os.path.exists(gui_path):
        files.append((gui_path, os.path.getmtime(gui_path)))

    if not files:
        raise FileNotFoundError("No log files found in the logs folder.")

    # Pick the most recently modified file
    files.sort(key=lambda x: x[1], reverse=True)
    return files[0][0]

def parse_log_for_phase1(log_file):
    phase1_data = {
        "new_blocks": [],
        "peers_connected": [],
        "errors": []
    }

    with open(log_file, "r") as f:
        for line in f:
            line = line.strip()
            
            # New block entries
            block_match = BLOCK_PATTERN.search(line)
            if block_match:
                block_id, height, timestamp = block_match.groups()
                timestamp = datetime.utcfromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S UTC')
                phase1_data["new_blocks"].append({
                    "block_id": block_id,
                    "height": int(height),
                    "timestamp": timestamp
                })
                continue

            # Peer connections
            peer_match = PEER_PATTERN.search(line)
            if peer_match:
                peer_id, address, role, protocol = peer_match.groups()
                phase1_data["peers_connected"].append({
                    "peer_id": int(peer_id),
                    "address": address,
                    "role": role,
                    "protocol": protocol
                })
                continue

            # Connection errors
            error_match = ERROR_PATTERN.search(line)
            if error_match:
                address, message = error_match.groups()
                phase1_data["errors"].append({
                    "address": address,
                    "message": message
                })

    return phase1_data

def write_health_log(data, logs_dir):
    health_path = os.path.join(logs_dir, HEALTH_LOG)
    with open(health_path, "w") as f:
        f.write(f"Phase 1 Health Log - Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        
        f.write("=== New Blocks ===\n")
        for block in data["new_blocks"]:
            f.write(f"Block ID: {block['block_id']}, Height: {block['height']}, Timestamp: {block['timestamp']}\n")
        
        f.write("\n=== Peers Connected ===\n")
        for peer in data["peers_connected"]:
            f.write(f"Peer ID: {peer['peer_id']}, Address: {peer['address']}, Role: {peer['role']}, Protocol: {peer['protocol']}\n")
        
        f.write("\n=== Connection Errors ===\n")
        for error in data["errors"]:
            f.write(f"Address: {error['address']}, Message: {error['message']}\n")

    print(f"Health log created at {health_path}")

if __name__ == "__main__":
    most_recent_log = get_most_recent_log(LOGS_DIR)
    print(f"Parsing most recent log: {most_recent_log}")
    data = parse_log_for_phase1(most_recent_log)
    write_health_log(data, LOGS_DIR)
