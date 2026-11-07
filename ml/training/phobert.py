"""Optional fine-tuning from the same prepared snapshot used by baseline."""
import re
from backend.app.labels import SENTIMENT_LABELS, TOPIC_LABELS
from backend.app.preprocessing import normalize_text
from ml.core.config import get_config
from ml.core.runs import create_run, write_json
from ml.data.dataset import load_prepared


def train(data_dir, run_dir, task: str, model_revision: str) -> None:
    if not re.fullmatch(r"[0-9a-fA-F]{40}", model_revision):
        raise ValueError("Use the checkpoint's 40-character immutable commit hash.")
    import numpy as np
    import torch
    from datasets import Dataset
    from pyvi import ViTokenizer
    from transformers import (
        AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding,
        EarlyStoppingCallback, Trainer, TrainingArguments, set_seed,
    )
    from ml.evaluation.metrics import build_task_metrics

    data, manifest = load_prepared(data_dir)
    cfg = get_config()
    metadata = create_run(run_dir, "phobert", manifest, cfg.to_dict())
    metadata.update(task=task, model_revision=model_revision)
    write_json(run_dir / "run.json", metadata)
    set_seed(cfg.random_seed)
    labels = SENTIMENT_LABELS if task == "sentiment" else TOPIC_LABELS
    tokenizer = AutoTokenizer.from_pretrained(
        cfg.phobert.pretrained_model_name, revision=model_revision, use_fast=False,
    )

    def tokenize(batch):
        texts = [ViTokenizer.tokenize(normalize_text(s)) for s in batch["sentence"]]
        return tokenizer(texts, truncation=True, max_length=cfg.phobert.max_length)

    prepared = {}
    for split, rows in data.items():
        dataset = Dataset.from_list([
            {"sentence": r["sentence"], "labels": r[task]} for r in rows
        ])
        prepared[split] = dataset.map(tokenize, batched=True, remove_columns=["sentence"])
    model = AutoModelForSequenceClassification.from_pretrained(
        cfg.phobert.pretrained_model_name, revision=model_revision,
        num_labels=len(labels), id2label=labels, label2id={v: k for k, v in labels.items()},
    )

    def compute_metrics(result):
        logits, truth = result
        metrics = build_task_metrics(truth.tolist(), np.argmax(logits, axis=-1).tolist(), task)
        return {"macro_f1": metrics["macro_f1"], "accuracy": metrics["accuracy"]}

    args = TrainingArguments(
        output_dir=str(run_dir / "checkpoints"), eval_strategy="epoch", save_strategy="epoch",
        load_best_model_at_end=True, metric_for_best_model=cfg.phobert.metric_for_best_model,
        greater_is_better=True, save_total_limit=2,
        num_train_epochs=cfg.phobert.num_train_epochs,
        per_device_train_batch_size=cfg.phobert.batch_size,
        per_device_eval_batch_size=cfg.phobert.eval_batch_size,
        learning_rate=cfg.phobert.learning_rate, weight_decay=cfg.phobert.weight_decay,
        warmup_ratio=cfg.phobert.warmup_ratio, seed=cfg.random_seed, report_to="none",
    )
    trainer = Trainer(
        model=model, args=args, train_dataset=prepared["train"],
        eval_dataset=prepared["validation"], processing_class=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer), compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=cfg.phobert.early_stopping_patience)],
    )
    trainer.train()
    trainer.save_state()
    metrics = {"model": "phobert", "task": task, "dataset": manifest,
               "model_revision": model_revision, "config": cfg.to_dict(),
               "device": str(trainer.args.device)}
    predictions = {}
    for split in ("validation", "test"):
        result = trainer.predict(prepared[split])
        predictions[split] = result.predictions.argmax(axis=-1).tolist()
        metrics[split] = {task: build_task_metrics(
            result.label_ids.tolist(), predictions[split], task,
        )}
    trainer.save_model(str(run_dir / "best_model"))
    tokenizer.save_pretrained(str(run_dir / "best_model"))
    write_json(run_dir / "metrics.json", metrics)
    write_json(run_dir / "predictions.json", predictions)
    metadata.update(status="complete", device=str(trainer.args.device))
    write_json(run_dir / "run.json", metadata)
    print(f"PhoBERT {task} completed: {run_dir}. API promotion is not supported yet.")
