from datetime import datetime
from pathlib import Path

# Write logs into backend/logs/usage.log (clean + predictable)
LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_FILE = LOG_DIR / "usage.log"


def log_event(event: str, ip: str | None = None):
    """
    Append a line like:
    2026-01-29T02:20:26.483679 | resume_analysis | ip=127.0.0.1
    """
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().isoformat()
        ip_part = f" | ip={ip}" if ip else ""
        line = f"{timestamp} | {event}{ip_part}\n"

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        # analytics must NEVER crash the app
        return
