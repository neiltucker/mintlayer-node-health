import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

LOG_DIR = Path.home() / ".mintlayer" / "mainnet" / "logs"
HEALTH_LOG = LOG_DIR / "mintlayer-health.log"

app = FastAPI(
    title="Mintlayer Node Health API",
    description="Read-only Phase-1 health endpoint",
    version="0.1.0",
)

# Add CORS middleware if you need to access from browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def read_last_health_entry():
    """Read the most recent health entry from the log file"""
    if not HEALTH_LOG.exists():
        raise FileNotFoundError(f"Health log not found at {HEALTH_LOG}")

    try:
        with HEALTH_LOG.open("r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        raise Exception(f"Error reading health log: {e}")

    if not lines:
        raise ValueError("Health log is empty")

    # Read from the end to get the most recent entry
    for line in reversed(lines):
        line = line.strip()
        if line:  # Skip empty lines
            try:
                return json.loads(line)
            except json.JSONDecodeError as e:
                # Skip malformed lines and try the previous one
                continue
    
    raise ValueError("No valid JSON entries found in health log")


@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "service": "Mintlayer Node Health API",
        "version": "0.1.0",
        "endpoints": {
            "/health": "Latest health snapshot (structured)",
            "/health/raw": "Full raw health data",
            "/status": "Simple status check"
        }
    }


@app.get("/health")
def health():
    """
    Returns the latest evaluated health snapshot in structured format
    """
    try:
        data = read_last_health_entry()
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Health monitoring not available: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error reading health data: {str(e)}"
        )

    # Extract and structure the data
    node_data = data.get("node", {})
    
    return {
        "timestamp": data.get("timestamp"),
        "overall_health": data.get("overall_health"),
        "node": {
            "version": node_data.get("version"),
            "network": node_data.get("network"),
            "uptime_seconds": node_data.get("uptime_seconds"),
            "start_time": node_data.get("start_time")
        },
        "chain": data.get("chain", {}),
        "peers": data.get("peers", {}),
        "consensus": data.get("consensus", {}),
        "errors": data.get("errors", {}),
    }


@app.get("/health/raw")
def health_raw():
    """
    Returns the full last health log entry as-is
    """
    try:
        data = read_last_health_entry()
        return JSONResponse(data)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Health monitoring not available: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error reading health data: {str(e)}"
        )


@app.get("/status")
def status():
    """
    Simple status endpoint that returns just the overall health status
    """
    try:
        data = read_last_health_entry()
        return {
            "status": data.get("overall_health", "unknown"),
            "timestamp": data.get("timestamp")
        }
    except Exception:
        return {
            "status": "unavailable",
            "timestamp": None
        }


@app.get("/health/history")
def health_history(limit: int = 100):
    """
    Returns recent health entries (last N entries)
    """
    if not HEALTH_LOG.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Health log not found at {HEALTH_LOG}"
        )
    
    try:
        with HEALTH_LOG.open("r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error reading health log: {e}"
        )
    
    # Parse the last N valid JSON entries
    entries = []
    for line in reversed(lines):
        if len(entries) >= limit:
            break
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    # Return in chronological order (oldest first)
    return {
        "count": len(entries),
        "entries": list(reversed(entries))
    }


if __name__ == "__main__":
    print(f"Starting Mintlayer Health API on http://127.0.0.1:3033")
    print(f"Reading health data from: {HEALTH_LOG}")
    print(f"Endpoints:")
    print(f"  GET /health - Structured health data")
    print(f"  GET /health/raw - Raw health data")
    print(f"  GET /status - Simple status check")
    print(f"  GET /health/history?limit=100 - Recent history")
    
    uvicorn.run(
        "health_api:app",
        host="127.0.0.1",
        port=3033,
        log_level="info",
        reload=False
    )
