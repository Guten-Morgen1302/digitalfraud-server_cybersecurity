from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fraud_sentinel.rag.knowledge_base import FraudKnowledgeBase


PATTERNS = [
    {
        "id": "npci_2025_001",
        "text": "Senior citizen ko call karke bola ki unka PAN card deactivate ho raha hai, Aadhaar link karne ke liye OTP batao",
        "fraud_type": "VISHING_AADHAAR_SCAM",
        "severity": "CRITICAL",
        "advice": "UIDAI ya koi bhi agency OTP phone pe nahi maangti. 1947 pe call karke verify karo.",
        "source": "CERT-In Advisory 2025",
    },
    {
        "id": "npci_2025_002",
        "text": "Telegram group mein stock tips milenge aur ek naya trading app download karo guaranteed 10x returns",
        "fraud_type": "PIG_BUTCHERING_INVESTMENT",
        "severity": "CRITICAL",
        "advice": "SEBI registered broker hi use karo. Koi guaranteed return nahi hota. Report at sebi.gov.in/complaints.",
        "source": "SEBI Advisory 2025",
    },
    {
        "id": "cert_2025_001",
        "text": "Your electricity bill is overdue. Pay INR 9 now or connection will be cut in 2 hours. Click to pay.",
        "fraud_type": "UTILITY_BILL_SCAM",
        "severity": "HIGH",
        "advice": "Utility payments hamesha official app ya website se karo. Link pe click mat karo.",
        "source": "CERT-In 2025",
    },
    {
        "id": "rbi_2025_001",
        "text": "Your account has been flagged for suspicious activity. Share screen with our executive to verify.",
        "fraud_type": "SCREEN_SHARE_OTP_THEFT",
        "severity": "CRITICAL",
        "advice": "Bank executive kabhi screen share nahi maangta. AnyDesk ya TeamViewer turant band karo.",
        "source": "RBI Circular DPSS 2025-26",
    },
]


def main() -> None:
    kb = FraudKnowledgeBase()
    for pattern in PATTERNS:
        kb.add_pattern(
            pattern_text=pattern["text"],
            fraud_type=pattern["fraud_type"],
            severity=pattern["severity"],
            advice=pattern["advice"],
            pattern_id=pattern["id"],
            source=pattern["source"],
        )
    print(f"RAG Knowledge Base total patterns: {kb.collection.count()}")


if __name__ == "__main__":
    main()
