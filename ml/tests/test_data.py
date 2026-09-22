import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.format import build_input, format_dialogue, parse_dialogue, remove_fillers  # noqa: E402
from extractive_baseline import textrank  # noqa: E402
from metrics import rouge  # noqa: E402

SAMSUM_STYLE = (
    "Amanda: I baked  cookies. Do you want some?\r\nJerry: Sure!\r\nAmanda: I'll bring you tomorrow :-)"
)


def test_parse_dialogue_splits_speakers_and_keeps_emoticons():
    assert parse_dialogue(SAMSUM_STYLE) == [
        ("Amanda", "I baked  cookies. Do you want some?"),
        ("Jerry", "Sure!"),
        ("Amanda", "I'll bring you tomorrow :-)"),
    ]


def test_line_without_speaker_continues_previous_turn():
    assert parse_dialogue("Tom: see you at\n5 pm") == [("Tom", "see you at 5 pm")]


def test_format_dialogue_with_and_without_speaker_tags():
    turns = [("Ann", "Um, let's ship on Friday."), ("Bo", "uh okay")]
    assert format_dialogue(turns) == "Ann: Um, let's ship on Friday.\nBo: uh okay"
    assert format_dialogue(turns, speaker_tags=False) == "Um, let's ship on Friday.\nuh okay"
    assert format_dialogue(turns, fillers=False) == "Ann: Let's ship on Friday.\nBo: okay"


def test_remove_fillers_keeps_words_that_contain_them():
    assert remove_fillers("Uh, the umbrella is here, um, hmm.") == "The umbrella is here."
    assert remove_fillers("yeah umm") == "yeah umm"


def test_build_input_prefixes():
    assert build_input("A: hi") == "summarize:\nA: hi"
    assert build_input("A: hi", section="decisions") == "summarize decisions:\nA: hi"
    with pytest.raises(ValueError):
        build_input("A: hi", section="jokes")


def test_textrank_returns_k_turns_in_spoken_order():
    dialogue = "\n".join(
        [
            "Ann: the budget review for the marketing launch is on Friday",
            "Bo: ok",
            "Cy: marketing wants the launch budget approved before Friday",
            "Bo: lunch?",
            "Ann: approved, the launch budget review moves to Thursday",
        ]
    )
    summary = textrank(dialogue, k=2).split("\n")
    assert len(summary) == 2
    assert all(line.split(":")[0] in {"Ann", "Cy"} for line in summary)
    order = [dialogue.split("\n").index(line) for line in summary]
    assert order == sorted(order)


def test_textrank_skips_attachment_placeholders():
    dialogue = "Hannah: <file_gif>\nAmanda: sorry, cannot find his number\nHannah: <file_gif>\nAmanda: ask Larry"
    assert "<file_gif>" not in textrank(dialogue, k=2)


def test_textrank_short_dialogue_is_returned_whole():
    assert textrank("A: hello\nB: hi", k=3) == "A: hello\nB: hi"


def test_rouge_identical_and_disjoint():
    same = rouge(["Ann will send the report."], ["Ann will send the report."])
    assert same["rouge1"] == same["rougeL"] == 1.0
    assert rouge(["cats"], ["dogs"])["rouge1"] == 0.0
