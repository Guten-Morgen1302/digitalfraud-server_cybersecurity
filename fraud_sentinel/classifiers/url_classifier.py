from __future__ import annotations

import re
from datetime import datetime
from functools import lru_cache


class URLFraudClassifier:
    """ONNX URL phishing detector with feature-engineering boost.

    Uses `pirocheto/phishing-url-detection` when optional ML dependencies are
    installed. The feature fallback remains deterministic for offline demos.
    """

    REPO_ID = "pirocheto/phishing-url-detection"
    TRUSTED_DOMAINS = {
        "npci.org.in",
        "bhimupi.org.in",
        "upi.npci.org.in",
        "paytm.com",
        "phonepe.com",
        "gpay.app",
        "sbi.co.in",
        "hdfcbank.com",
        "icicibank.com",
        "axisbank.com",
        "kotak.com",
        "rbi.org.in",
        "incometax.gov.in",
        "uidai.gov.in",
        "india.gov.in",
    }
    RISKY_TLDS = {
        ".xyz",
        ".top",
        ".click",
        ".loan",
        ".work",
        ".online",
        ".site",
        ".live",
        ".tk",
        ".ml",
        ".ga",
        ".cf",
        ".gq",
        ".pw",
        ".cc",
    }

    def __init__(self, use_onnx: bool = True) -> None:
        self.sess = None
        self.input_name = "inputs"
        self.onnx_enabled = False
        if use_onnx:
            self._load_onnx()

    def _load_onnx(self) -> None:
        try:
            import onnxruntime
            from huggingface_hub import hf_hub_download
        except ImportError:
            return

        try:
            model_path = hf_hub_download(repo_id=self.REPO_ID, filename="model.onnx")
            self.sess = onnxruntime.InferenceSession(model_path, providers=["CPUExecutionProvider"])
            self.input_name = self.sess.get_inputs()[0].name
            self.onnx_enabled = True
        except Exception:
            self.sess = None
            self.onnx_enabled = False

    def analyze(self, url: str) -> dict:
        ext = self._extract(url)
        domain = f"{ext['domain']}.{ext['suffix']}".strip(".")

        if domain in self.TRUSTED_DOMAINS:
            return {
                "url": url,
                "is_phishing": False,
                "risk_score": 0.0,
                "label": "TRUSTED",
                "conf": 1.0,
                "boost": 0.0,
                "model": "trusted-domain",
            }

        model_prob = self._onnx_probability(url) if self.sess else self._fallback_probability(url, ext)
        boost = self._risk_boost(url, ext, domain)
        final = min(1.0, model_prob + boost)
        label = "PHISHING" if final > 0.75 else ("SUSPICIOUS" if final > 0.5 else "SAFE")
        return {
            "url": url,
            "is_phishing": final > 0.75,
            "risk_score": round(final * 100, 1),
            "label": label,
            "conf": round(model_prob, 4),
            "boost": round(boost, 4),
            "model": self.REPO_ID if self.onnx_enabled else "feature-fallback",
        }

    def _onnx_probability(self, url: str) -> float:
        import numpy as np

        results = self.sess.run(None, {self.input_name: np.array([url], dtype=object)})
        output = results[0]
        if hasattr(output, "shape") and len(output.shape) == 2 and output.shape[1] > 1:
            return float(output[0][1])
        if isinstance(output, list) and output and isinstance(output[0], dict):
            return float(output[0].get("phishing", output[0].get("LABEL_1", 0.0)))
        return float(output[0])

    def _fallback_probability(self, url: str, ext: dict[str, str]) -> float:
        score = 0.08
        lowered = url.lower()
        if any(token in lowered for token in ["verify", "kyc", "login", "secure", "renewal"]):
            score += 0.18
        if any(token in lowered for token in ["upi", "bank", "sbi", "phonepe", "paytm", "npci"]):
            score += 0.14
        if any(token in lowered for token in ["verify", "kyc", "login", "renewal"]) and any(
            brand in lowered for brand in ["upi", "bank", "sbi", "phonepe", "paytm", "npci"]
        ):
            score += 0.12
        if ext["subdomain"] and len(ext["subdomain"].split(".")) >= 2:
            score += 0.10
        return min(score, 0.60)

    def _risk_boost(self, url: str, ext: dict[str, str], domain: str) -> float:
        boost = 0.0
        tld = f".{ext['suffix']}"
        try:
            import whois

            record = whois.whois(domain)
            created = record.creation_date
            if isinstance(created, list):
                created = created[0]
            if created and (datetime.now() - created.replace(tzinfo=None)).days < 30:
                boost += 0.25
        except Exception:
            boost += 0.10

        if tld in self.RISKY_TLDS:
            boost += 0.15
        if re.search(r"\d+\.\d+\.\d+\.\d+", url):
            boost += 0.20
        if any(shortener in url for shortener in ["bit.ly", "tinyurl", "ow.ly", "t.co"]):
            boost += 0.15
        if "@" in url:
            boost += 0.20
        if len(url) > 100:
            boost += 0.10
        if ext["subdomain"] and len(ext["subdomain"].split(".")) > 3:
            boost += 0.10
        return min(0.40, boost)

    def _extract(self, url: str) -> dict[str, str]:
        try:
            import tldextract

            ext = tldextract.extract(url)
            return {"subdomain": ext.subdomain, "domain": ext.domain, "suffix": ext.suffix}
        except ImportError:
            match = re.search(r"https?://([^/]+)", url)
            host = match.group(1) if match else url.split("/")[0]
            parts = host.lower().split(".")
            suffix = parts[-1] if len(parts) > 1 else ""
            domain = parts[-2] if len(parts) > 1 else parts[0]
            subdomain = ".".join(parts[:-2]) if len(parts) > 2 else ""
            return {"subdomain": subdomain, "domain": domain, "suffix": suffix}


@lru_cache(maxsize=1)
def get_url_classifier() -> URLFraudClassifier:
    return URLFraudClassifier()
