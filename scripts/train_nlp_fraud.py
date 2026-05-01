from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def training_args_kwargs(**kwargs):
    from transformers import TrainingArguments

    signature = inspect.signature(TrainingArguments.__init__)
    if "eval_strategy" in signature.parameters and "evaluation_strategy" in kwargs:
        kwargs["eval_strategy"] = kwargs.pop("evaluation_strategy")
    return kwargs


def main() -> None:
    try:
        import evaluate
        import numpy as np
        import pandas as pd
        import torch
        from datasets import Dataset, load_dataset
        from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
    except ImportError as exc:
        raise SystemExit("Install ML dependencies first: pip install -r requirements-ml.txt") from exc

    os.makedirs("fraud_sentinel/models/bert_phishing", exist_ok=True)
    print("Loading PhreshPhish dataset...")
    phresh = load_dataset("phreshphish/phreshphish", split="train")

    india_fraud_samples = [
        {
            "text": "CBI officer bol raha hoon, aap money laundering case mein hai. Abhi INR 50000 UPI karo warna arrest hoga.",
            "label": 1,
        },
        {
            "text": "You are under digital arrest. Do not tell anyone. Transfer INR 2 lakh immediately to avoid FIR.",
            "label": 1,
        },
        {"text": "Ye Cyber Crime Cell se call hai, aapka SIM block ho raha hai, OTP batao.", "label": 1},
        {"text": "Your PhonePe account will be suspended. Complete KYC at phonepe-kyc-verify.xyz", "label": 1},
        {"text": "NPCI: Your UPI ID is expiring. Click here to renew: upi-renewal-npci.online/verify", "label": 1},
        {"text": "SBI: Account blocked due to incomplete KYC. Update at sbi-secure-kyc.in within 24 hours.", "label": 1},
        {"text": "Maine aapko INR 500 bheje hain. UPI collect request accept karo: pay.9876543210@ybl", "label": 1},
        {"text": "Your refund of INR 1299 has been initiated. Please approve the collect request.", "label": 1},
        {"text": "Scan this QR code to receive your cashback of INR 2000 from Amazon India.", "label": 1},
        {"text": "Customer care: To get refund, scan QR and enter UPI PIN to authenticate.", "label": 1},
        {"text": "Your HDFC Bank account has been credited with INR 5000.00 on 01-May-26.", "label": 0},
        {"text": "OTP for your SBI transaction is 847291. Valid for 10 minutes. Do NOT share.", "label": 0},
        {"text": "PhonePe: You have received INR 200 from Rahul Kumar 9876543210@ybl.", "label": 0},
    ]

    phresh_df = phresh.to_pandas()[["text", "label"]].sample(5000, random_state=42)
    combined_df = pd.concat([phresh_df, pd.DataFrame(india_fraud_samples)], ignore_index=True)
    combined_df = combined_df.sample(frac=1, random_state=42).reset_index(drop=True)
    dataset = Dataset.from_pandas(combined_df).train_test_split(test_size=0.15, seed=42)

    model_name = "ealvaradob/bert-finetuned-phishing"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=2,
        ignore_mismatched_sizes=True,
    )

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=256)

    dataset = dataset.map(tokenize, batched=True)
    dataset = dataset.rename_column("label", "labels")
    dataset.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

    accuracy_metric = evaluate.load("accuracy")
    f1_metric = evaluate.load("f1")

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        return {
            "accuracy": accuracy_metric.compute(predictions=preds, references=labels)["accuracy"],
            "f1": f1_metric.compute(predictions=preds, references=labels, average="weighted")["f1"],
        }

    args = TrainingArguments(
        **training_args_kwargs(
            output_dir="fraud_sentinel/models/bert_phishing",
            num_train_epochs=3,
            per_device_train_batch_size=16,
            per_device_eval_batch_size=32,
            learning_rate=2e-5,
            weight_decay=0.01,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="f1",
            logging_dir="logs",
            fp16=torch.cuda.is_available(),
            report_to="none",
        )
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        compute_metrics=compute_metrics,
    )
    trainer.train()
    trainer.save_model("fraud_sentinel/models/bert_phishing/final")
    tokenizer.save_pretrained("fraud_sentinel/models/bert_phishing/final")
    results = trainer.evaluate()
    print(f"Final Accuracy: {results['eval_accuracy']:.4f}")
    print(f"Final F1: {results['eval_f1']:.4f}")


if __name__ == "__main__":
    main()
