"""
IndicBERT Fine-Tuning Script — Hindi Vishing Detection
Base: ai4bharat/indic-bert
Target accuracy: 93%+
Run on Kaggle GPU (free T4) — ~2-3 hours
Usage: python fine_tuning/train_indicbert.py
"""
import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from sklearn.metrics import accuracy_score, f1_score
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

MODEL_NAME = "ai4bharat/indic-bert"
OUTPUT_DIR = "./fine_tuned/indicbert_vishing"
MAX_LEN = 256
EPOCHS = 5
BATCH_SIZE = 32

print(f"Loading data...")
train_df = pd.read_json("data/processed/train.jsonl", lines=True)
val_df = pd.read_json("data/processed/val.jsonl", lines=True)
print(f"Train: {len(train_df)} | Val: {len(val_df)}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def tokenize(batch):
    return tokenizer(batch["text"], truncation=True, max_length=MAX_LEN, padding="max_length")

train_ds = Dataset.from_pandas(train_df).map(tokenize, batched=True, remove_columns=["text"])
val_ds = Dataset.from_pandas(val_df).map(tokenize, batched=True, remove_columns=["text"])
train_ds = train_ds.rename_column("label", "labels")
val_ds = val_ds.rename_column("label", "labels")
train_ds.set_format("torch", columns=["input_ids", "attention_mask", "labels"])
val_ds.set_format("torch", columns=["input_ids", "attention_mask", "labels"])

model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1": f1_score(labels, preds, average="weighted"),
    }

args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=64,
    learning_rate=2e-5,
    warmup_ratio=0.1,
    weight_decay=0.01,
    evaluation_strategy="epoch",
    save_strategy="best",
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    greater_is_better=True,
    logging_steps=50,
    fp16=torch.cuda.is_available(),
    report_to="none",
    dataloader_num_workers=2,
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_ds,
    eval_dataset=val_ds,
    compute_metrics=compute_metrics,
)

print("Training IndicBERT...")
trainer.train()

# Evaluate on test set
test_df = pd.read_json("data/processed/test.jsonl", lines=True)
test_ds = Dataset.from_pandas(test_df).map(tokenize, batched=True, remove_columns=["text"])
test_ds = test_ds.rename_column("label", "labels")
test_ds.set_format("torch", columns=["input_ids", "attention_mask", "labels"])
test_results = trainer.evaluate(test_ds)
print(f"\n✅ Test Results: {test_results}")

trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"✅ Model saved to {OUTPUT_DIR}")
print("Update HINDI_MODEL in .env to use fine-tuned model:")
print(f"  HINDI_MODEL={OUTPUT_DIR}")
