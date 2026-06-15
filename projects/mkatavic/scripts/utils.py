"""Shared helpers for the semiconductor supply-chain project.

Provides:
  * canonical project paths (data/raw, data/processed, sources.csv)
  * a configured logger
  * Neo4j connection handling (password read from env / .env — never hardcoded)
  * source-logging helpers that enforce the project rule:
        "No data point without a source."

Importable from any script in scripts/ or any notebook in notebooks/.
"""

from __future__ import annotations

import csv
import logging
import os
from pathlib import Path
from typing import Iterable

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
SOURCES_CSV = DATA_DIR / "sources.csv"

for _d in (DATA_RAW, DATA_PROCESSED):
    _d.mkdir(parents=True, exist_ok=True)

SOURCES_HEADER = ["source_id", "url", "date_accessed", "covers", "notes"]


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
def get_logger(name: str = "supplychain") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s",
                              datefmt="%H:%M:%S")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


log = get_logger()


# --------------------------------------------------------------------------- #
# Environment / .env loading (no hard dependency on python-dotenv)
# --------------------------------------------------------------------------- #
def load_env(env_path: Path | None = None) -> None:
    """Populate os.environ from a .env file if present.

    Uses python-dotenv when available; otherwise falls back to a tiny parser
    so the scripts run even before dependencies are installed.
    """
    env_path = env_path or (PROJECT_ROOT / ".env")
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(env_path)
        return
    except ImportError:
        pass
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


# --------------------------------------------------------------------------- #
# Neo4j
# --------------------------------------------------------------------------- #
def get_driver():
    """Return a Neo4j driver using env vars (NEO4J_URI/USER/PASSWORD).

    The neo4j package is imported lazily so that data-collection scripts,
    which do not touch the database, run without it installed.
    """
    load_env()
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        raise RuntimeError(
            "NEO4J_PASSWORD is not set. Copy .env.example to .env and set it, "
            "or export the environment variable."
        )
    from neo4j import GraphDatabase  # lazy import
    from neo4j.exceptions import AuthError, ServiceUnavailable

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
    except ServiceUnavailable as e:
        driver.close()
        raise RuntimeError(
            f"Cannot reach Neo4j at {uri}. Is the database INSTANCE started in "
            "Neo4j Desktop (status 'Running'/'Active'), and is the Bolt port "
            "correct? Neo4j Desktop 2 may use a port other than 7687 — check the "
            "instance's connection details and update NEO4J_URI in .env."
        ) from e
    except AuthError as e:
        driver.close()
        raise RuntimeError(
            f"Neo4j rejected the credentials for user {user!r}. Check "
            "NEO4J_PASSWORD in .env matches the password set for this instance."
        ) from e
    return driver


# --------------------------------------------------------------------------- #
# Source logging  —  enforces "no data without a source"
# --------------------------------------------------------------------------- #
def _read_sources() -> dict[str, dict]:
    if not SOURCES_CSV.exists():
        return {}
    with SOURCES_CSV.open(newline="", encoding="utf-8") as fh:
        return {row["source_id"]: row for row in csv.DictReader(fh)}


def log_sources(rows: Iterable[dict]) -> int:
    """Upsert source rows into data/sources.csv, keyed by source_id.

    Each row must have: source_id, url, date_accessed, covers, (optional) notes.
    Returns the number of new source_ids added.
    """
    existing = _read_sources()
    before = len(existing)
    for row in rows:
        sid = row["source_id"]
        existing[sid] = {
            "source_id": sid,
            "url": row.get("url", ""),
            "date_accessed": row.get("date_accessed", ""),
            "covers": row.get("covers", ""),
            "notes": row.get("notes", ""),
        }
    with SOURCES_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SOURCES_HEADER)
        writer.writeheader()
        for sid in sorted(existing):
            writer.writerow(existing[sid])
    return len(existing) - before


def write_csv(path: Path, header: list[str], rows: Iterable[dict]) -> int:
    """Write list-of-dicts to CSV. Returns number of data rows written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in header})
            n += 1
    return n
