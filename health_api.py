import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

LOG_DIR = Path.home() / ".mintlayer" / "mainnet" / "logs"
HEALTH_LOG = LOG_DIR / "mintlayer_health.log"

app = FastAPI(
    title="Mintlayer Node Health API",
    description="Read-only Phase-1 health endpoint",
    version="0.1.0",
)


def read_last_health_entry():
    if not HEALTH_LOG.exists():
        raise FileNotFoundError("Health log not found")

    with HEALTH_LOG.open("rb") as f:
        try:
            f.seek(-4096, 2)  # read last ~4KB
        except OSError:
            f.seek(0)
        lines = f.read().splitlines()

    if not lines:
        raise ValueError("Health log is empty")

    return json.loads(lines[-1].decode("utf-8"))


@app.get("/health")
def health():
    """
    Returns the latest evaluated health snapshot
    """
    try:
        data = read_last_health_entry()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {
        "timestamp": data.get("timestamp"),
        "overall_health": data.get("overall_health"),
        "node": data.get("node"),
        "chain": data.get("chain"),
        "peers": data.get("peers"),
        "consensus": data.get("consensus"),
        "errors": data.get("errors"),
    }


@app.get("/health/raw")
def health_raw():
    """
    Returns the full last health log entry
    """
    try:
        return JSONResponse(read_last_health_entry())
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "health_api:app",
        host="127.0.0.1",
        port=3033,
        log_level="info",
    )
