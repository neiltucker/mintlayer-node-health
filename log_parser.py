import re
import time
import json
from pathlib import Path
from datetime import datetime

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

LOG_DIR = Path.home() / ".mintlayer" / "mainnet" / "logs"
NODE_LOG = LOG_DIR / "mintlayer-node-gui.log"
HEALTH_LOG = LOG_DIR / "mintlayer_health.log"


class MintlayerLogParser:
    def __init__(self, log_path):
        self.log_path = Path(log_path)
        self.offset = 0
        self.start_time = int(time.time())
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
            return self._health_snapshot()

        with self.log_path.open("r", encoding="utf-8", errors="ignore") as f:
            f.seek(self.offset)
            for line in f:
                self._process_line(line)
            self.offset = f.tell()

        return self._health_snapshot()

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

    def _health_snapshot(self):
        now = int(time.time())

        sync_stalled = (
            self.state["last_block_time"] is not None
            and now - self.state["last_block_time"] > 300
        )

        if self.state["panic"] or self.state["db_error"]:
            overall = "critical"
        elif sync_stalled or self.state["peer_count"] == 0:
            overall = "degraded"
        else:
            overall = "healthy"

        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "node": {
                "version": self.state["version"],
                "network": self.state["network"],
                "uptime_seconds": now - self.start_time,
            },
            "chain": {
                "best_block": self.state["best_block"],
                "last_block_seen_seconds_ago": (
                    None if self.state["last_block_time"] is None
                    else now - self.state["last_block_time"]
                ),
                "sync_stalled": sync_stalled,
            },
            "peers": {
                "count": self.state["peer_count"],
            },
            "consensus": {
                "fork_compatible": not self.state["fork_error"],
            },
            "errors": {
                "db_error": self.state["db_error"],
                "panic": self.state["panic"],
            },
            "overall_health": overall,
        }


def write_health_log(entry):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with HEALTH_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    parser = MintlayerLogParser(NODE_LOG)

    while True:
        health = parser.poll()
        write_health_log(health)
        time.sleep(30)
