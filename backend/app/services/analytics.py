from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parents[2] / "usage.log"


def log_event(event: str, ip: str | None = None):
    timestamp = datetime.utcnow().isoformat()

    ip_part = f" | ip={ip}" if ip else ""

    line = f"{timestamp} | {event}{ip_part}\n"

    try:
        with open(LOG_FILE, "a") as f:
            f.write(line)
    except Exception:
        # analytics must NEVER crash the app
        pass
