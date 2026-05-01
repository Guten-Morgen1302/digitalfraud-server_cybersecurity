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
        import torch
        from datasets import Audio, load_dataset
        from transformers import AutoFeatureExtractor, AutoModelForAudioClassification, Trainer, TrainingArguments
    except ImportError as exc:
        raise SystemExit("Install ML dependencies first: pip install -r requirements-ml.txt") from exc

    os.makedirs("fraud_sentinel/models/wav2vec2_deepfake", exist_ok=True)
    dataset = load_dataset("garystafford/deepfake-audio-detection")
    dataset = dataset.cast_column("audio", Audio(sampling_rate=16000))

    model_name = "facebook/wav2vec2-base"
    extractor = AutoFeatureExtractor.from_pretrained(model_name)

    def preprocess(examples):
        audio_arrays = [item["array"] for item in examples["audio"]]
        inputs = extractor(
            audio_arrays,
            sampling_rate=16000,
            padding=True,
            max_length=32000,
            truncation=True,
        )
        inputs["labels"] = examples["label"]
        return inputs

    remove_columns = [col for col in ["audio", "file_name"] if col in dataset["train"].column_names]
    dataset = dataset.map(preprocess, batched=True, batch_size=8, remove_columns=remove_columns)
    dataset = dataset["train"].train_test_split(test_size=0.2, seed=42)

    model = AutoModelForAudioClassification.from_pretrained(
        model_name,
        num_labels=2,
        id2label={0: "real", 1: "deepfake"},
        label2id={"real": 0, "deepfake": 1},
        ignore_mismatched_sizes=True,
    )
    model.freeze_feature_encoder()
    accuracy_metric = evaluate.load("accuracy")

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        return accuracy_metric.compute(predictions=preds, references=labels)

    args = TrainingArguments(
        **training_args_kwargs(
            output_dir="fraud_sentinel/models/wav2vec2_deepfake",
            num_train_epochs=5,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=16,
            learning_rate=3e-5,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="accuracy",
            fp16=torch.cuda.is_available(),
            report_to="none",
            logging_steps=10,
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
    trainer.save_model("fraud_sentinel/models/wav2vec2_deepfake/final")
    extractor.save_pretrained("fraud_sentinel/models/wav2vec2_deepfake/final")
    results = trainer.evaluate()
    print(f"Final Accuracy: {results['eval_accuracy']:.4f}")


if __name__ == "__main__":
    main()
