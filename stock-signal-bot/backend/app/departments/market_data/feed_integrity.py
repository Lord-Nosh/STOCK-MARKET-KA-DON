"""Market-feed provenance and freshness helpers."""
from __future__ import annotations

import enum
import time
from dataclasses import dataclass
from typing import Optional


class FeedMode(str, enum.Enum):
    LIVE = "LIVE"
    DELAYED = "DELAYED"
    HISTORICAL = "HISTORICAL"
    SIMULATED = "SIMULATED"
    CACHED = "CACHED"
    UNKNOWN = "UNKNOWN"


@dataclass
class FeedInfo:
    symbol: str
    source: str
    mode: FeedMode
    provider_timestamp: float
    received_at: float
    processed_at: float
    ui_updated_at: Optional[float] = None
    sequence_id: Optional[int] = None
    connection_status: str = "CONNECTED"
    last_successful_message_at: Optional[float] = None
    is_stale: bool = False
    stale_reason: Optional[str] = None


def build_feed_info(
    symbol: str,
    source: str,
    provider_ts: float,
    received_ts: float,
    processed_ts: float,
    sequence_id: Optional[int] = None,
    connection_ok: bool = True,
    last_msg_ts: Optional[float] = None,
    mode: FeedMode = FeedMode.UNKNOWN,
) -> FeedInfo:
    """Build feed metadata for one quote or candle."""
    return FeedInfo(
        symbol=symbol, source=source, mode=mode,
        provider_timestamp=provider_ts, received_at=received_ts,
        processed_at=processed_ts, sequence_id=sequence_id,
        connection_status="CONNECTED" if connection_ok else "DISCONNECTED",
        last_successful_message_at=last_msg_ts,
    )


def is_stale(
    info: FeedInfo, now_ts: float, stale_threshold: float = 30.0
) -> tuple[bool, str]:
    """Return freshness state based on provider timestamp and latest message."""
    if stale_threshold < 0:
        raise ValueError("stale_threshold must be non-negative")
    age = now_ts - info.provider_timestamp
    if age > stale_threshold:
        return True, f"PROVIDER_AGE_{int(age)}s"
    if info.last_successful_message_at is not None:
        gap = now_ts - info.last_successful_message_at
        if gap > stale_threshold:
            return True, f"NO_MESSAGE_FOR_{int(gap)}s"
    return False, ""


def classify_mode(
    info: FeedInfo, now_ts: float, market_open: bool, stale_threshold: float = 30.0
) -> FeedMode:
    """Classify mode; an unhealthy connection must never be called live."""
    if info.connection_status != "CONNECTED":
        return FeedMode.UNKNOWN
    if info.mode == FeedMode.SIMULATED:
        return FeedMode.SIMULATED
    stale, _ = is_stale(info, now_ts, stale_threshold)
    if stale:
        return FeedMode.DELAYED if market_open else FeedMode.CACHED
    if now_ts - info.provider_timestamp > 60:
        return FeedMode.HISTORICAL
    return FeedMode.LIVE


def enrich_with_provenance(
    symbol: str,
    raw: dict,
    source: str,
    mode: FeedMode = FeedMode.UNKNOWN,
    connection_ok: bool = True,
    last_msg_ts: Optional[float] = None,
) -> dict:
    """Return raw data plus consistent provenance metadata."""
    now = time.time()
    provider_ts = raw.get("exchange_timestamp", now)
    try:
        provider_ts = float(provider_ts)
    except (TypeError, ValueError):
        provider_ts = now
        connection_ok = False

    feed_info = build_feed_info(
        symbol=symbol, source=source, provider_ts=provider_ts,
        received_ts=now, processed_ts=now,
        sequence_id=raw.get("sequence_id"), connection_ok=connection_ok,
        last_msg_ts=last_msg_ts, mode=mode,
    )
    # Basic IST session heuristic; an exchange calendar is still needed for holidays.
    ist_now = time.gmtime(now + 5.5 * 3600)
    seconds_since_midnight = ist_now.tm_hour * 3600 + ist_now.tm_min * 60 + ist_now.tm_sec
    market_open = 9 * 3600 + 15 * 60 <= seconds_since_midnight <= 15 * 3600 + 30 * 60

    stale, reason = is_stale(feed_info, now, stale_threshold=30.0)
    feed_info.is_stale = stale
    feed_info.stale_reason = reason or None
    feed_info.mode = classify_mode(feed_info, now, market_open, stale_threshold=30.0)
    enriched = dict(raw)
    enriched["feed_provenance"] = {
        "source": feed_info.source, "mode": feed_info.mode.value,
        "provider_timestamp": feed_info.provider_timestamp,
        "received_at": feed_info.received_at, "processed_at": feed_info.processed_at,
        "sequence_id": feed_info.sequence_id,
        "connection_status": feed_info.connection_status,
        "last_successful_message_at": feed_info.last_successful_message_at,
        "is_stale": feed_info.is_stale, "stale_reason": feed_info.stale_reason,
    }
    return enriched
