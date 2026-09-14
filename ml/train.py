"""Fine-tune a seq2seq summariser (default google/flan-t5-base). Runs on Kaggle GPUs, never on laptops.

    python ml/train.py --dataset samsum --push_to_hub --hub_model_id <user>/flan-t5-base-samsum
    python ml/train.py --dataset samsum --lora                      # LoRA r=16 on q/v (ablation)
    python ml/train.py ... --resume_from_checkpoint hub              # continue after a dead session

Validation ROUGE is computed every epoch and the best epoch by ROUGE-L is kept. With --push_to_hub
every epoch's checkpoint goes to the Hub (including `last-checkpoint/` for resuming), and the final
model plus run_info.json (settings, parameter counts, runtime, GPU, best validation scores) are
uploaded when training ends. LoRA runs are merged into the base weights before that upload, so
the backend always loads a plain seq2seq model.
"""

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ML_DIR))

import numpy as np  # noqa: E402
import torch  # noqa: E402
from data.format import build_input  # noqa: E402
from data.prepare import LOADERS, load_splits  # noqa: E402
from metrics import rouge  # noqa: E402
from transformers import (  # noqa: E402
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    set_seed,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--model", default="google/flan-t5-base", help="base model or a previous stage's checkpoint"
    )
    p.add_argument("--dataset", default="samsum", choices=sorted(LOADERS))
    p.add_argument("--max_input", type=int, default=1024)
    p.add_argument("--max_target", type=int, default=128)
    p.add_argument("--epochs", type=float, default=3)
    p.add_argument("--lr", type=float, default=None, help="default 5e-5 full fine-tuning, 1e-3 LoRA")
    p.add_argument("--batch_size", type=int, default=8)
    p.add_argument("--grad_accum", type=int, default=2)
    p.add_argument("--warmup_ratio", type=float, default=0.05)
    p.add_argument("--weight_decay", type=float, default=0.01)
    p.add_argument(
        "--precision",
        choices=["auto", "fp32", "fp16", "bf16"],
        default="auto",
        help="auto: bf16 on Ampere or newer, else fp32. T5 models are known to overflow to NaN loss in fp16.",
    )
    p.add_argument("--lora", action="store_true")
    p.add_argument("--lora_r", type=int, default=16)
    p.add_argument("--lora_alpha", type=int, default=32)
    p.add_argument("--no_speaker_tags", action="store_true", help="ablation: drop `Speaker:` from each line")
    p.add_argument("--remove_fillers", action="store_true", help="ablation: strip um/uh before training")
    p.add_argument("--eval_samples", type=int, default=300, help="validation examples scored each epoch")
    p.add_argument("--eval_beams", type=int, default=4)
    p.add_argument("--max_train_samples", type=int, default=None, help="smoke tests only")
    p.add_argument("--max_steps", type=int, default=-1, help="smoke tests only; overrides --epochs")
    p.add_argument("--output_dir", default=None, help="default ml/checkpoints/<run name>")
    p.add_argument("--run_name", default=None)
    p.add_argument("--push_to_hub", action="store_true")
    p.add_argument("--hub_model_id", default=None, help="<user>/<repo>; HF_TOKEN must be set")
    p.add_argument("--hub_public", action="store_true", help="create the Hub repo public (default private)")
    p.add_argument(
        "--resume_from_checkpoint",
        default=None,
        help="a checkpoint folder, `last` (newest in output_dir) or `hub` (last-checkpoint/ on the Hub)",
    )
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    if args.push_to_hub and not args.hub_model_id:
        p.error("--push_to_hub needs --hub_model_id")
    if args.lr is None:
        args.lr = 1e-3 if args.lora else 5e-5
    base = args.model.rstrip("/").split("/")[-1]
    args.run_name = args.run_name or f"{base}-{args.dataset}{'-lora' if args.lora else ''}"
    args.output_dir = args.output_dir or str(ML_DIR / "checkpoints" / args.run_name)
    return args


def resolve_precision(choice: str) -> str:
    if choice != "auto":
        return choice
    if torch.cuda.is_available() and torch.cuda.get_device_capability()[0] >= 8:
        return "bf16"
    return "fp32"


def resolve_resume(args: argparse.Namespace) -> str | bool | None:
    value = args.resume_from_checkpoint
    if value is None:
        return None
    if value == "last":
        return True
    if value == "hub":
        from huggingface_hub import snapshot_download

        if not args.hub_model_id:
            raise SystemExit("--resume_from_checkpoint hub needs --hub_model_id")
        snapshot_download(args.hub_model_id, allow_patterns=["last-checkpoint/*"], local_dir=args.output_dir)
        path = Path(args.output_dir) / "last-checkpoint"
        if not path.exists():
            raise SystemExit(f"no last-checkpoint/ found on {args.hub_model_id}")
        return str(path)
    return value


def count_parameters(model: torch.nn.Module) -> tuple[int, int]:
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return trainable, sum(p.numel() for p in model.parameters())


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    precision = resolve_precision(args.precision)
    print(f"run {args.run_name} · precision {precision} · output {args.output_dir}")

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model)
    if args.lora:
        from peft import LoraConfig, TaskType, get_peft_model

        config = LoraConfig(
            task_type=TaskType.SEQ_2_SEQ_LM,
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=0.05,
            target_modules=["q", "v"],
        )
        model = get_peft_model(model, config)
    trainable, total = count_parameters(model)
    print(f"parameters: {trainable:,} trainable of {total:,} ({100 * trainable / total:.2f}%)")

    ds = load_splits(args.dataset, speaker_tags=not args.no_speaker_tags, fillers=not args.remove_fillers)
    train = ds["train"].shuffle(seed=args.seed)
    if args.max_train_samples:
        train = train.select(range(min(args.max_train_samples, len(train))))
    validation = ds["validation"].select(range(min(args.eval_samples, len(ds["validation"]))))

    def tokenize(batch: dict) -> dict:
        enc = tokenizer(
            [build_input(d) for d in batch["dialogue"]], max_length=args.max_input, truncation=True
        )
        enc["labels"] = tokenizer(text_target=batch["summary"], max_length=args.max_target, truncation=True)[
            "input_ids"
        ]
        return enc

    columns = train.column_names
    train = train.map(tokenize, batched=True, remove_columns=columns)
    validation = validation.map(tokenize, batched=True, remove_columns=columns)
    truncated = sum(len(ids) >= args.max_input for ids in train["input_ids"])
    print(
        f"train {len(train)} · validation {len(validation)} · inputs truncated at {args.max_input}: {truncated}"
    )

    def compute_metrics(eval_pred) -> dict[str, float]:
        preds, labels = eval_pred
        if isinstance(preds, tuple):
            preds = preds[0]
        preds = np.where(preds < 0, tokenizer.pad_token_id, preds)
        labels = np.where(labels < 0, tokenizer.pad_token_id, labels)
        decoded_preds = [t.strip() for t in tokenizer.batch_decode(preds, skip_special_tokens=True)]
        decoded_labels = [t.strip() for t in tokenizer.batch_decode(labels, skip_special_tokens=True)]
        scores = rouge(decoded_preds, decoded_labels)
        scores["gen_len"] = round(
            float(np.mean([np.count_nonzero(p != tokenizer.pad_token_id) for p in preds])), 1
        )
        return scores

    training_args = Seq2SeqTrainingArguments(
        output_dir=args.output_dir,
        run_name=args.run_name,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size * 2,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        warmup_ratio=args.warmup_ratio,
        weight_decay=args.weight_decay,
        lr_scheduler_type="linear",
        fp16=precision == "fp16",
        bf16=precision == "bf16",
        eval_strategy="epoch" if args.max_steps < 0 else "steps",
        save_strategy="epoch" if args.max_steps < 0 else "steps",
        eval_steps=None if args.max_steps < 0 else args.max_steps,
        save_steps=None if args.max_steps < 0 else args.max_steps,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="rougeL",
        greater_is_better=True,
        predict_with_generate=True,
        generation_max_length=args.max_target,
        generation_num_beams=args.eval_beams,
        group_by_length=True,
        logging_steps=50,
        report_to="none",
        seed=args.seed,
        push_to_hub=args.push_to_hub,
        hub_model_id=args.hub_model_id,
        hub_strategy="checkpoint",
        hub_private_repo=not args.hub_public,
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train,
        eval_dataset=validation,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model, label_pad_token_id=-100),
        processing_class=tokenizer,
        compute_metrics=compute_metrics,
    )

    started = time.perf_counter()
    result = trainer.train(resume_from_checkpoint=resolve_resume(args))
    runtime = time.perf_counter() - started
    final_metrics = trainer.evaluate()
    print(json.dumps(final_metrics, indent=2))

    final_dir = Path(args.output_dir) / "final"
    final_model = trainer.model.merge_and_unload() if args.lora else trainer.model
    final_model.save_pretrained(final_dir)
    tokenizer.save_pretrained(final_dir)

    info = {
        "run_name": args.run_name,
        "date": date.today().isoformat(),
        "base_model": args.model,
        "dataset": args.dataset,
        "method": f"lora r={args.lora_r} alpha={args.lora_alpha} q,v" if args.lora else "full fine-tune",
        "trainable_parameters": trainable,
        "total_parameters": total,
        "precision": precision,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "gpu_count": torch.cuda.device_count(),
        "train_examples": len(train),
        "validation_examples_per_epoch": len(validation),
        "train_runtime_sec": round(runtime, 1),
        "global_steps": result.global_step,
        "best_checkpoint": trainer.state.best_model_checkpoint,
        "best_validation_rougeL": trainer.state.best_metric,
        "final_validation": {k: v for k, v in final_metrics.items() if isinstance(v, (int, float))},
        "log_history": trainer.state.log_history,
        "args": vars(args),
    }
    (final_dir / "run_info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(f"saved {final_dir}")

    if args.push_to_hub:
        from huggingface_hub import HfApi

        HfApi().upload_folder(
            folder_path=str(final_dir),
            repo_id=args.hub_model_id,
            commit_message=f"final model for {args.run_name}, validation rougeL {trainer.state.best_metric}",
        )
        print(f"uploaded to https://huggingface.co/{args.hub_model_id}")


if __name__ == "__main__":
    main()
