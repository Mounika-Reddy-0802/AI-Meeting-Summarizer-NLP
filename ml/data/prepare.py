"""Dataset loaders. Every loader returns a DatasetDict with `train`, `validation` and `test`
splits and the columns `id`, `dialogue` (`Speaker: text` lines) and `summary`.

    python ml/data/prepare.py --dataset samsum      # download, normalise, print split stats

Sources and licences are recorded in data/README.md.
"""

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datasets import DatasetDict, load_dataset  # noqa: E402

from data.format import format_dialogue, parse_dialogue  # noqa: E402

# Samsung/samsum was removed from the Hub; this mirror has 14,731 / 818 / 819 (the paper: 14,732)
SAMSUM_REPO = "knkarthick/samsum"
DIALOGSUM_REPO = "knkarthick/dialogsum"
AMI_REPO = "knkarthick/AMI"


def _normalise(example: dict, speaker_tags: bool, fillers: bool) -> dict:
    turns = parse_dialogue(example["dialogue"] or "")
    return {
        "dialogue": format_dialogue(turns, speaker_tags=speaker_tags, fillers=fillers),
        "summary": (example["summary"] or "").strip(),
    }


def load_samsum(speaker_tags: bool = True, fillers: bool = True, cache_dir: str | None = None) -> DatasetDict:
    """SAMSum messenger dialogues with one abstractive summary each.

    A handful of rows have an empty dialogue or summary; they are dropped from every split.
    """
    raw = load_dataset(SAMSUM_REPO, cache_dir=cache_dir)
    columns = ["id", "dialogue", "summary"]
    ds = DatasetDict(
        {
            split: raw[split]
            .select_columns(columns)
            .map(_normalise, fn_kwargs={"speaker_tags": speaker_tags, "fillers": fillers})
            .filter(lambda ex: bool(ex["dialogue"]) and bool(ex["summary"]))
            for split in ("train", "validation", "test")
        }
    )
    return ds


def load_dialogsum(**_kwargs) -> DatasetDict:
    """DialogSum (knkarthick/dialogsum): spoken daily-life dialogues with #Person1#-style speakers."""
    # TODO(Lahari, W2): map #Person1#/#Person2# to speaker names and reuse _normalise
    raise NotImplementedError("load_dialogsum arrives in Week 2")


def load_ami(**_kwargs) -> DatasetDict:
    """AMI meetings with abstractive summaries (gated knkarthick/AMI, accept the terms first)."""
    # TODO(Lahari, W2): load plain AMI summaries and hold out the AMI test meeting ids everywhere
    raise NotImplementedError("load_ami arrives in Week 2")


LOADERS = {"samsum": load_samsum, "dialogsum": load_dialogsum, "ami": load_ami}


def load_splits(name: str, **kwargs) -> DatasetDict:
    if name not in LOADERS:
        raise ValueError(f"unknown dataset {name!r}; use one of {sorted(LOADERS)}")
    return LOADERS[name](**kwargs)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--dataset", default="samsum", choices=sorted(LOADERS))
    parser.add_argument("--no_speaker_tags", action="store_true")
    parser.add_argument("--remove_fillers", action="store_true")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # dialogues contain emoji

    ds = load_splits(args.dataset, speaker_tags=not args.no_speaker_tags, fillers=not args.remove_fillers)
    for split, rows in ds.items():
        words = [len(d.split()) for d in rows["dialogue"]]
        summary_words = [len(s.split()) for s in rows["summary"]]
        print(
            f"{split:<10} {len(rows):>6} dialogues · dialogue words mean {sum(words) / len(words):.0f} "
            f"max {max(words)} · summary words mean {sum(summary_words) / len(summary_words):.0f}"
        )
    example = ds["test"][0]
    print(f"\n--- test[0] {example['id']} ---\n{example['dialogue']}\n--- summary ---\n{example['summary']}")


if __name__ == "__main__":
    main()
