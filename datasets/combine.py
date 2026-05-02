"""
Dataset Combine + Format Script
Run: python datasets/combine.py
Merges all sources → balanced train/val/test JSONL splits.
"""
import json, random
import pandas as pd
from sklearn.model_selection import train_test_split

os._exists = __import__("os").path.exists
import os

os.makedirs("data/processed", exist_ok=True)

SOURCES = [
    ("data/raw/phishing_emails.csv",    "text",  "label"),
    ("data/raw/sms_phishing.csv",       "text",  "label"),
    ("data/raw/synthetic_hinglish.csv", "text",  "label"),
    # Add after Kaggle download:
    # ("data/raw/india-spam-sms-classification/spam.csv", "Message", "Category"),
]

dfs = []
for path, text_col, label_col in SOURCES:
    if not os.path.exists(path):
        print(f"⚠ Skipping {path} (not found)")
        continue
    try:
        df = pd.read_csv(path)
        # Normalize columns
        if text_col not in df.columns or label_col not in df.columns:
            print(f"⚠ Wrong columns in {path}: {list(df.columns)}")
            continue
        df = df[[text_col, label_col]].copy()
        df.columns = ["text", "label"]
        df = df.dropna().drop_duplicates(subset=["text"])
        # Normalize labels to 0/1
        df["label"] = df["label"].apply(
            lambda x: 1 if str(x).lower() in ("1", "spam", "phishing", "scam", "true") else 0
        )
        dfs.append(df)
        print(f"✓ {path}: {len(df)} samples ({df.label.sum()} scam)")
    except Exception as e:
        print(f"✗ {path}: {e}")

if not dfs:
    print("No datasets found. Run prepare_all.py first.")
    exit(1)

combined = pd.concat(dfs, ignore_index=True)
combined["label"] = combined["label"].astype(int)
print(f"\nTotal before balance: {len(combined)} ({combined.label.sum()} scam)")

# Balance classes
min_count = min(combined["label"].value_counts())
balanced = pd.concat([
    combined[combined.label == 0].sample(min_count, random_state=42),
    combined[combined.label == 1].sample(min_count, random_state=42),
]).sample(frac=1, random_state=42).reset_index(drop=True)
print(f"Balanced: {len(balanced)} ({min_count} per class)")

# 80/10/10 split
train, temp = train_test_split(balanced, test_size=0.2, random_state=42, stratify=balanced["label"])
val, test = train_test_split(temp, test_size=0.5, random_state=42, stratify=temp["label"])

for split_name, split_df in [("train", train), ("val", val), ("test", test)]:
    path = f"data/processed/{split_name}.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for _, row in split_df.iterrows():
            f.write(json.dumps({"text": str(row["text"]), "label": int(row["label"])}, ensure_ascii=False) + "\n")
    print(f"✓ {split_name}.jsonl: {len(split_df)} samples")

print("\n✅ Done! Next: python fine_tuning/train_indicbert.py")
