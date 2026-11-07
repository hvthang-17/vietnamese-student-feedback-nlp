"""Shared offline CPU runtime for serving and evaluation; heavy imports are lazy."""
from .preprocessing import normalize_text


class PhoBERTCPU:
    """Load only local safetensors; mirror training normalization and segmentation."""

    def __init__(self, run_dirs: dict, runs: dict, threads: int):
        import torch
        from pyvi import ViTokenizer
        from transformers import AutoTokenizer, RobertaForSequenceClassification

        torch.set_num_threads(threads)
        if torch.get_num_interop_threads() != 1:
            torch.set_num_interop_threads(1)
        self.torch = torch
        self.segment = ViTokenizer.tokenize
        self.models = {}
        self.tokenizers = {}
        self.max_lengths = {}
        for task, path in run_dirs.items():
            local = path / "best_model"
            self.tokenizers[task] = AutoTokenizer.from_pretrained(
                local, local_files_only=True, use_fast=False, trust_remote_code=False,
            )
            self.models[task] = RobertaForSequenceClassification.from_pretrained(
                local, local_files_only=True, use_safetensors=True,
            ).to("cpu").eval()
            self.max_lengths[task] = runs[task]["config"]["phobert"]["max_length"]

    def predict(self, text: str) -> dict:
        text = self.segment(normalize_text(text))
        result = {}
        with self.torch.inference_mode():
            for task, model in self.models.items():
                encoded = self.tokenizers[task](
                    text, truncation=True, max_length=self.max_lengths[task], return_tensors="pt",
                )
                probabilities = model(**encoded).logits.softmax(dim=-1)[0]
                result[task] = {"label_id": int(probabilities.argmax()),
                                "probabilities": probabilities.tolist()}
        return result

