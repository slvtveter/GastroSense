"""Self-ping keep-alive for Render's free tier.

Render free web services spin down after ~15 minutes with no inbound HTTP
traffic, and waking one back up is slow (observed 5-6 minutes) and serves 502s
in the meantime - which is exactly what made the dashboard fail for anyone
visiting after an idle period.

Relying on an EXTERNAL pinger (a GitHub Actions cron) proved unreliable:
GitHub throttles short schedules heavily and our keepalive workflow never
actually fired (0 runs after 30+ minutes). So instead the service keeps
*itself* awake: a daemon thread periodically issues a plain HTTP GET to its own
public URL. That round-trip leaves the instance, goes through Render's edge,
and comes back as real inbound traffic, resetting the 15-minute idle timer. As
long as the instance is running it never goes idle, so it never spins down and
visitors always land on a warm server.

This has no external dependency and starts automatically on Render (where
RENDER_EXTERNAL_URL is injected); it is a no-op locally.
"""
import os
import threading
import time
import urllib.request

from app.logger import logger

# 10 min - comfortably under Render's ~15 min idle window, leaving margin for a
# slow request or minor scheduling drift.
_PING_INTERVAL_SECONDS = int(os.getenv("KEEPALIVE_INTERVAL_SECONDS", "600"))
_PING_TIMEOUT_SECONDS = 30


def _ping(url: str) -> None:
    try:
        req = urllib.request.Request(
            url, method="GET", headers={"User-Agent": "gastrosense-keepalive"}
        )
        with urllib.request.urlopen(req, timeout=_PING_TIMEOUT_SECONDS) as resp:
            logger.info(f"Keep-alive ping {url} -> HTTP {resp.status}")
    except Exception as e:
        # A failed ping is non-fatal: the next cycle will try again. We only log
        # it so it's visible if something is persistently wrong.
        logger.warning(f"Keep-alive ping {url} failed: {e}")


def _worker(urls: list[str]) -> None:
    while True:
        time.sleep(_PING_INTERVAL_SECONDS)
        for url in urls:
            _ping(url)


def start_keepalive() -> None:
    """Start the self-ping daemon thread.

    No-op when RENDER_EXTERNAL_URL is unset (local/dev), so it only runs on
    Render. Pings the backend's own URL plus the frontend, keeping both warm.
    """
    self_url = os.getenv("RENDER_EXTERNAL_URL")
    if not self_url:
        logger.info("RENDER_EXTERNAL_URL not set - keep-alive disabled (not on Render).")
        return

    urls = [self_url.rstrip("/") + "/"]

    # Keep the frontend warm too, so the first page load after an idle period
    # isn't slow either. Overridable via env; defaults to the known deploy URL.
    frontend_url = os.getenv("FRONTEND_URL", "https://gastrosense-frontend.onrender.com")
    if frontend_url:
        urls.append(frontend_url.rstrip("/") + "/")

    threading.Thread(target=_worker, args=(urls,), daemon=True, name="keepalive").start()
    logger.info(
        f"Keep-alive started: pinging {urls} every {_PING_INTERVAL_SECONDS}s to "
        "prevent free-tier spin-down."
    )
