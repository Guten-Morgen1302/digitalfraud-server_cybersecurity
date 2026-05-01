from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone


def anchor_evidence(sha256_hash: str, dry_run: bool = True) -> dict[str, str | bool | None]:
    contract = os.getenv("CONTRACT_ADDRESS")
    private_key = os.getenv("PRIVATE_KEY")
    live_ready = bool(contract and private_key and not dry_run)
    if not live_ready:
        tx_hash = f"dryrun_{uuid.uuid5(uuid.NAMESPACE_URL, sha256_hash).hex[:24]}"
        return {
            "dry_run": True,
            "tx_hash": tx_hash,
            "polygonscan_url": None,
            "anchored_at": datetime.now(timezone.utc).isoformat(),
        }
    # Live web3 anchoring can be plugged here once hackathon keys are configured.
    tx_hash = f"pending_live_{uuid.uuid4().hex[:24]}"
    return {
        "dry_run": False,
        "tx_hash": tx_hash,
        "polygonscan_url": f"https://amoy.polygonscan.com/tx/{tx_hash}",
        "anchored_at": datetime.now(timezone.utc).isoformat(),
    }
