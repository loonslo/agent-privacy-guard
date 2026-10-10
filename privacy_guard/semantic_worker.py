"""Isolated, offline CPU worker. Only fixed classification labels are returned."""

import contextlib
import json
import os
import sys


def classify(request: dict) -> list[str]:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    options = {"local_files_only": True, "trust_remote_code": False}
    tokenizer = AutoTokenizer.from_pretrained(request["model"], **options)
    model = AutoModelForSequenceClassification.from_pretrained(
        request["model"],
        use_safetensors=True,
        **options,
    ).to("cpu")
    labels = model.config.id2label
    if set(labels.values()) != {"public", "private", "uncertain"} or len(labels) != 3:
        raise ValueError("Invalid model labels")
    model.eval()
    limit = min(
        512, tokenizer.model_max_length, getattr(model.config, "max_position_embeddings", 512)
    )
    results = []
    with torch.inference_mode():
        for text in request["texts"]:
            tokens = tokenizer(text, return_tensors="pt", truncation=False)
            if tokens["input_ids"].shape[-1] > limit:
                raise ValueError("Input exceeds model context")
            probabilities = torch.softmax(model(**tokens).logits, dim=-1)[0]
            if probabilities.shape[-1] != 3 or not torch.isfinite(probabilities).all():
                raise ValueError("Invalid model output")
            index = int(probabilities.argmax())
            label = labels[index]
            results.append(label if float(probabilities[index]) >= 0.8 else "uncertain")
    return results


def main() -> int:
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
    try:
        request = json.loads(sys.stdin.buffer.read(512 * 1024))
        with open(os.devnull, "w") as sink:
            with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
                result = classify(request)
        print(json.dumps(result))
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
