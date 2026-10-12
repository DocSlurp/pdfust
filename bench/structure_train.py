"""Bounded local LoRA feasibility study; synthetic training never includes study PDFs."""

from __future__ import annotations

import argparse
import importlib
import json
import random
import time
from pathlib import Path
from typing import Any

import pdfust
from bench.feature_cases import page_pdf, text_op
from bench.structure import ARTIFACTS, PATCH_PROMPT, QWEN_MODEL, QWEN_REVISION, write_json
from bench.structure_core import score_tables, validate_patch

_TRAIN_COUNT = 36
_MAX_STEPS = 256
_MAX_NEW_TOKENS = 2048
_MIN_COLUMNS = 2
_MIDDLE_COLUMNS = 3


def build_dataset() -> list[dict[str, Any]]:  # noqa: C901, PLR0912
    """Make deterministic training/validation pages with independently planned cells."""
    root = ARTIFACTS / "training/dataset"
    root.mkdir(parents=True, exist_ok=True)
    examples = []
    for index in range(48):
        rng = random.Random(7100 + index)  # noqa: S311 - reproducible fixture variation.
        columns = 2 + index % 3
        count = rng.randint(3, 6)
        negative = index % 4 == 0
        headers = {
            2: ["Code", "Amount"],
            3: ["Code", "Description", "Amount"],
            4: ["Code", "Description", "Qty", "Amount"],
        }[columns]
        rows = [headers]
        for row in range(count):
            values = [f"Item{index:02d}{row:02d}", f"{rng.randint(1, 999)}.{rng.randint(0, 99):02d}"]
            if columns > _MIN_COLUMNS:
                values.insert(1, f"Service {row + 1}")
            if columns > _MIDDLE_COLUMNS:
                values.insert(2, str(rng.randint(1, 20)))
            rows.append(values)
        x_step = 500 / columns
        y_step = rng.choice([28, 36, 44])
        size = rng.choice([10, 11, 12])
        ops = []
        if negative:
            rows = [
                [f"This passage discusses topic {row} in section {column}." for column in range(2)] for row in range(5)
            ]
            columns, x_step, size = 2, 270, 10
        for row, values in enumerate(rows):
            for col, value in enumerate(values):
                ops.append(text_op(value, 35 + col * x_step, 700 - row * y_step, size=size))
        if index % 2 and not negative:
            for row in range(len(rows) + 1):
                ops.append(f"25 {715 - row * y_step} m {25 + columns * x_step} {715 - row * y_step} l")  # noqa: PERF401
            for col in range(columns + 1):
                ops.append(f"{25 + col * x_step} {715 - len(rows) * y_step} m {25 + col * x_step} 715 l")  # noqa: PERF401
            ops.append("S")
        data = page_pdf("\n".join(ops))
        directory = root / f"example-{index:02d}"
        directory.mkdir(exist_ok=True)
        (directory / "input.pdf").write_bytes(data)
        with pdfust.open(stream=data) as document:
            page = document[0]
            page.get_pixmap(dpi=72 * 640 / 792, background=(255, 255, 255)).save(directory / "page.png")
            words = [
                {"id": f"p0w{i}", "bbox": list(word[:4]), "text": word[4]}
                for i, word in enumerate(page.get_text("words"))
            ]
        cells: list[list[list[str]]] = [[[] for _ in range(columns)] for _ in rows]
        for word in sorted(words, key=lambda item: (item["bbox"][1], item["bbox"][0])):
            center_y = (word["bbox"][1] + word["bbox"][3]) / 2
            row = min(range(len(rows)), key=lambda r: abs(center_y - (92 + r * y_step - size * 0.3)))
            col = min(columns - 1, max(0, int((word["bbox"][0] - 35 + 1) / x_step)))
            cells[row][col].append(word["id"])
        target = {"tables": [] if negative else [{"rows": cells, "spans": []}]}
        if not negative:
            reconstructed, _ = validate_patch(target, words)
            if reconstructed != [rows]:
                msg = f"generated training source does not match independently planned cells: {index}"
                raise ValueError(msg)
        source = json.dumps(
            {
                "width": 612,
                "height": 792,
                "word_format": ["id", "x0", "y0", "x1", "y1", "text"],
                "words": [[word["id"], *[round(value, 1) for value in word["bbox"]], word["text"]] for word in words],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        example = {
            "index": index,
            "split": "validation" if index >= _TRAIN_COUNT else "train",
            "words": words,
            "prompt": PATCH_PROMPT + source,
            "target": target,
            "expected_tables": [] if negative else [rows],
            "image": str(directory / "page.png"),
            "directory": str(directory),
        }
        write_json(directory / "example.json", example)
        examples.append(example)
    write_json(root / "manifest.json", examples)
    return examples


def model_inputs(processor: Any, example: dict[str, Any], *, answer: bool) -> dict[str, Any]:  # noqa: ANN401
    """Apply exactly one template, masking every input token in training."""
    image = importlib.import_module("PIL.Image").open(example["image"]).convert("RGB")
    messages = [
        {"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": example["prompt"]}]}
    ]
    if answer:
        messages.append({"role": "assistant", "content": json.dumps(example["target"], separators=(",", ":"))})
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=not answer)
    return processor(text=[text], images=[image], return_tensors="pt")


def evaluate(model: Any, processor: Any, examples: list[dict[str, Any]], phase: str) -> list[dict[str, Any]]:  # noqa: ANN401
    """Compare source-backed grids on held-out generated pages, including rejected schemas."""
    torch = importlib.import_module("torch")
    model.eval()
    rows = []
    for example in examples:
        inputs = model_inputs(processor, example, answer=False).to("cuda:0")
        start = time.perf_counter()
        with torch.inference_mode():
            output = model.generate(**inputs, do_sample=False, max_new_tokens=_MAX_NEW_TOKENS)
        generated = output[0, inputs["input_ids"].shape[1] :]
        text = processor.decode(generated, skip_special_tokens=True)
        (Path(example["directory"]) / f"{phase}-raw.txt").write_text(text)
        result = {
            "index": example["index"],
            "seconds": time.perf_counter() - start,
            "output_tokens": len(generated),
            "truncated": len(generated) >= _MAX_NEW_TOKENS,
        }
        try:
            cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            matrices, used = validate_patch(json.loads(cleaned), example["words"])
            result.update({"score": score_tables(matrices, example["expected_tables"]), "used_ids": len(used)})
        except Exception as error:
            result["error"] = f"{type(error).__name__}: {error}"
        rows.append(result)
        write_json(ARTIFACTS / f"training/{phase}.json", rows)
        print(phase, example["index"], result.get("score", result.get("error")), flush=True)
    return rows


def main() -> None:
    """Run one small fixed training configuration, not an unrestricted tuning search."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=64)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.steps <= _MAX_STEPS:
        parser.error("steps must be 1..256 for this bounded pilot")
    examples = build_dataset()
    if args.prepare_only:
        return
    torch = importlib.import_module("torch")
    transformers = importlib.import_module("transformers")
    peft = importlib.import_module("peft")
    torch.manual_seed(7100)
    model = transformers.Qwen2_5_VLForConditionalGeneration.from_pretrained(
        QWEN_MODEL,
        torch_dtype=torch.bfloat16,
        device_map="cuda:0",
        attn_implementation="sdpa",
        quantization_config=transformers.BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        ),
        revision=QWEN_REVISION,
    )
    processor = transformers.AutoProcessor.from_pretrained(QWEN_MODEL, revision=QWEN_REVISION)
    validation = [example for example in examples if example["split"] == "validation"]
    before = evaluate(model, processor, validation, "before")
    model = peft.prepare_model_for_kbit_training(model)
    model = peft.get_peft_model(
        model,
        peft.LoraConfig(
            r=8,
            lora_alpha=16,
            lora_dropout=0,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            task_type="CAUSAL_LM",
        ),
    )
    model.config.use_cache = False
    optimizer = torch.optim.AdamW((parameter for parameter in model.parameters() if parameter.requires_grad), lr=1e-4)
    training = [example for example in examples if example["split"] == "train"]
    losses = []
    start = time.perf_counter()
    model.train()
    torch.cuda.reset_peak_memory_stats()
    for step in range(args.steps):
        example = training[step % len(training)]
        prefix = model_inputs(processor, example, answer=False)
        inputs = model_inputs(processor, example, answer=True).to("cuda:0")
        labels = inputs["input_ids"].clone()
        labels[:, : prefix["input_ids"].shape[1]] = -100
        inputs["labels"] = labels
        optimizer.zero_grad(set_to_none=True)
        loss = model(**inputs).loss
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        losses.append(float(loss.detach()))
        print("step", step + 1, "loss", losses[-1], flush=True)
        write_json(
            ARTIFACTS / "training/progress.json",
            {
                "steps": step + 1,
                "losses": losses,
                "seconds": time.perf_counter() - start,
                "peak_cuda_bytes": torch.cuda.max_memory_allocated(),
            },
        )
        if (step + 1) % 8 == 0:
            model.save_pretrained(ARTIFACTS / "training/checkpoint")
    seconds = time.perf_counter() - start
    model.save_pretrained(ARTIFACTS / "training/adapter")
    model.config.use_cache = True
    after = evaluate(model, processor, validation, "after")
    report = {
        "model": QWEN_MODEL,
        "model_revision": QWEN_REVISION,
        "steps": args.steps,
        "training_examples": len(training),
        "validation_examples": len(validation),
        "training_seconds": seconds,
        "losses": losses,
        "before": before,
        "after": after,
        "seed": 7100,
        "learning_rate": 1e-4,
        "lora_rank": 8,
        "training_image_longest": 640,
        "quantization": "NF4 with double quantization and BF16 compute",
        "scope": "fixed feasibility pilot; randomized generated-page validation, not template-family holdout",
    }
    write_json(ARTIFACTS / "training/report.json", report)


if __name__ == "__main__":
    main()
