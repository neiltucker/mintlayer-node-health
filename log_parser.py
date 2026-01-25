import re
import time
from pathlib import Path

LOG_PATTERNS = {
    "startup": re.compile(r"Starting.*Mintlayer.*v(?P<version>\d+\.\d+\.\d+)"),
    "network": re.compile(r"Network:\s+(?P<network>mainnet|testnet|regtest)"),
    "block": re.compile(r"Imported block.*#(?P<height>\d+)"),
    "peer_connect": re.compile(r"Peer connected:\s+(?P<peer_id>[a-f0-9]+)"),
    "peer_disconnect": re.compile(r"Peer disconnected:\s+(?P<peer_id>[a-f0-9]+)"),
    "fork_error": re.compile(r"Incompatible protocol version|Consensus error.*fork"),
    "db_error": re.compile(r"Database error|disk full|No space left on device"),
    "panic": re.compile(r"panicked|fatal error"),
}

class MintlayerLogParser:
    def __init__(self, log_path):
        self.log_path = Path(log_path)
        self.offset = 0
        self.state = {
            "version": None,
            "network": None,
            "best_block": None,
            "last_block_time": None,
            "peer_count": 0,
            "fork_error": False,
            "db_error": False,
            "panic": False,
        }

    def poll(self):
        if not self.log_path.exists():
            return self.state

        with self.log_path.open("r", encoding="utf-8", errors="ignore") as f:
            f.seek(self.offset)
            for line in f:
                self._process_line(line)
            self.offset = f.tell()

        return self.state

    def _process_line(self, line):
        now = int(time.time())

        if m := LOG_PATTERNS["startup"].search(line):
            self.state["version"] = m.group("version")

        elif m := LOG_PATTERNS["network"].search(line):
            self.state["network"] = m.group("network")

        elif m := LOG_PATTERNS["block"].search(line):
            self.state["best_block"] = int(m.group("height"))
            self.state["last_block_time"] = now

        elif LOG_PATTERNS["peer_connect"].search(line):
            self.state["peer_count"] += 1

        elif LOG_PATTERNS["peer_disconnect"].search(line):
            self.state["peer_count"] = max(0, self.state["peer_count"] - 1)

        elif LOG_PATTERNS["fork_error"].search(line):
            self.state["fork_error"] = True

        elif LOG_PATTERNS["db_error"].search(line):
            self.state["db_error"] = True

        elif LOG_PATTERNS["panic"].search(line):
            self.state["panic"] = True
