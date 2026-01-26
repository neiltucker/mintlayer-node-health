import os

# Full logs path in the home directory
LOGS_DIR = os.path.expanduser("~/.mintlayer/mainnet/logs")
DAEMON_LOG = "mintlayer-node-daemon.log"
GUI_LOG = "mintlayer-node-gui.log"

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
            # New block tip entries
            if "NEW TIP in chainstate" in line:
                phase1_data["new_blocks"].append(line)
            # Peer connection entries
            elif "new peer accepted" in line:
                phase1_data["peers_connected"].append(line)
            # Connection failure/errors
            elif "Failed to establish connection" in line:
                phase1_data["errors"].append(line)

    return phase1_data

if __name__ == "__main__":
    most_recent_log = get_most_recent_log(LOGS_DIR)
    print(f"Parsing most recent log: {most_recent_log}")
    data = parse_log_for_phase1(most_recent_log)
    print("Phase 1 Data Summary:")
    print("New blocks:", len(data["new_blocks"]))
    print("Peers connected:", len(data["peers_connected"]))
    print("Errors:", len(data["errors"]))
