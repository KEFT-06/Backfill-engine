"""GitHub Archive source — one ``.json.gz`` per hour, from 2011 onward.

Plumbing: build the URL for an hour, download it to a temp file, and (crucially,
given the 16 GB / <256 GB machine) delete it right after processing. We never
retain raw data — only the transformed Parquet output.
"""

from __future__ import annotations

import shutil
import urllib.request
from datetime import datetime
from pathlib import Path

# GH Archive's CDN rejects the default Python-urllib User-Agent (403). Send a normal one.
_USER_AGENT = "backfill-hell/0.1 (+https://github.com/data-eng-portfolio)"

# A network call MUST always be bounded: without this, a dead/slow connection hangs
# the whole worker forever (INC-005). A timeout turns a hang into a retryable failure.
_TIMEOUT_SECONDS = 30


def url_for(hour: datetime, base_url: str = "https://data.gharchive.org") -> str:
    """Build the GH Archive URL for a given hour.

    Note the format quirk: month and day are zero-padded, but the HOUR is NOT.
    Hour 5 -> ``2015-01-01-5.json.gz``, hour 15 -> ``2015-01-01-15.json.gz``.
    """
    stem = f"{hour.year}-{hour.month:02d}-{hour.day:02d}-{hour.hour}"
    return f"{base_url}/{stem}.json.gz"


def download(hour: datetime, dest_dir: Path, base_url: str = "https://data.gharchive.org") -> Path:
    """Download one hourly file into ``dest_dir`` and return its local path."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    url = url_for(hour, base_url)
    local_path = dest_dir / f"{hour.year}-{hour.month:02d}-{hour.day:02d}-{hour.hour}.json.gz"
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with (
        urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp,  # noqa: S310
        local_path.open("wb") as fh,
    ):
        shutil.copyfileobj(resp, fh)
    return local_path
