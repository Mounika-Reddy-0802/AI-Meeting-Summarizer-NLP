"""Turn dialogues into model inputs: one `Speaker: text` line per turn, optional filler cleanup,
and the task prefix the model is trained with.

The backend formats live transcripts the same way (backend/app/services/summarize.py), so a change
to the line format or the prefix here must be mirrored there.
"""

import re

# Hesitations only. Backchannels ("yeah", "okay", "right") carry meaning and are left for the
# dialogue-act filter in Week 3.
FILLERS = ("um", "uh", "erm", "er", "hmm", "mm", "mhm", "uhm", "ah")
_FILLER_RE = re.compile(r"(?<![\w'])(?:" + "|".join(FILLERS) + r")(?![\w'])\s*,?\s*", re.IGNORECASE)
_TURN_RE = re.compile(r"^\s*([^:\n]{1,60}?)\s*:\s*(.*)$")

SECTIONS = ("decisions", "actions", "problems")

Turn = tuple[str, str]


def remove_fillers(text: str) -> str:
    """Drop um/uh-style hesitations and tidy the spacing they leave behind."""
    cleaned = _FILLER_RE.sub("", text)
    # "here, um." leaves "here, ." behind
    cleaned = re.sub(r"[\s,]+([.!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip().rstrip(",").strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned and text[:1].isupper() else cleaned


def parse_dialogue(text: str) -> list[Turn]:
    """Split `Name: text` lines into turns. A line without a speaker continues the previous turn."""
    turns: list[Turn] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.strip()
        if not line:
            continue
        match = _TURN_RE.match(line)
        if match:
            turns.append((match.group(1), match.group(2).strip()))
        elif turns:
            speaker, previous = turns[-1]
            turns[-1] = (speaker, f"{previous} {line}".strip())
        else:
            turns.append(("", line))
    return turns


def format_dialogue(turns: list[Turn], speaker_tags: bool = True, fillers: bool = True) -> str:
    """Join turns as lines. `speaker_tags=False` keeps only the text; `fillers=False` removes them."""
    lines = []
    for speaker, text in turns:
        if not fillers:
            text = remove_fillers(text)
        if not text:
            continue
        lines.append(f"{speaker}: {text}" if speaker_tags and speaker else text)
    return "\n".join(lines)


def build_input(dialogue: str, section: str | None = None) -> str:
    """Prefix the task. One model, one prefix per output: `summarize:` or `summarize decisions:`."""
    if section is not None and section not in SECTIONS:
        raise ValueError(f"unknown section {section!r}; use one of {SECTIONS}")
    prefix = f"summarize {section}:" if section else "summarize:"
    return f"{prefix}\n{dialogue}"
