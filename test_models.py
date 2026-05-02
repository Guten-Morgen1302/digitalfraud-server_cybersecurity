import time
from transformers import pipeline

print("Testing Phishing model (PyTorch)...")
try:
    pipe = pipeline(
        "text-classification",
        model="Auguzcht/securisense-phishing-detection",
        framework="pt",
        device=-1,
        truncation=True,
        max_length=512
    )
    print("Phishing model loaded!")
    res = pipe("warmup")
    print(f"Result: {res}")
except Exception as e:
    print(f"Phishing model failed: {e}")

print("Testing SMS model (PyTorch)...")
try:
    pipe = pipeline(
        "text-classification",
        model="distilbert-base-uncased-finetuned-sst-2-english",
        framework="pt",
        device=-1,
        truncation=True,
        max_length=512
    )
    print("SMS model loaded!")
    res = pipe("warmup")
    print(f"Result: {res}")
except Exception as e:
    print(f"SMS model failed: {e}")
