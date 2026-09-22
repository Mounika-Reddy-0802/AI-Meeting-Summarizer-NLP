"""TextRank extractive baseline: rank the dialogue's turns and return the top k in original order.

Similarity between two turns is the TextRank word-overlap measure (Mihalcea & Tarau, 2004):
|shared words| / (log|a| + log|b|), over lowercased content words. PageRank over that graph
scores each turn.

    python ml/extractive_baseline.py --k 2          # print a few SAMSum test examples
"""

import argparse
import math
import re
import sys
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data.format import parse_dialogue  # noqa: E402

STOPWORDS = frozenset(
    "a an and are as at be but by for from have i if in is it its me my of on or so that the this "
    "to was we were will with you your yes no ok okay yeah do did not just what there they he she "
    "him her them our us can be been am im i'm it's don't".split()
)
_WORD = re.compile(r"[a-z0-9']+")
# SAMSum stands in for attachments with <file_gif>, <file_photo>, <file_other>, <link> ...
_PLACEHOLDER = re.compile(r"<[a-z_]+>")


def _words(text: str) -> set[str]:
    return {w for w in _WORD.findall(_PLACEHOLDER.sub(" ", text.lower())) if w not in STOPWORDS}


def _similarity(a: set[str], b: set[str]) -> float:
    if len(a) < 2 or len(b) < 2:
        # log(1) = 0 would divide by zero; single-word turns barely link to anything anyway
        return 0.0
    return len(a & b) / (math.log(len(a)) + math.log(len(b)))


def textrank(dialogue: str, k: int = 2) -> str:
    """Top-k turns by PageRank, kept as `Speaker: text` lines in the order they were said."""
    turns = parse_dialogue(dialogue)
    if len(turns) <= k:
        return "\n".join(f"{s}: {t}" if s else t for s, t in turns)

    bags = [_words(text) for _, text in turns]
    graph = nx.Graph()
    graph.add_nodes_from(range(len(turns)))
    for i in range(len(turns)):
        for j in range(i + 1, len(turns)):
            weight = _similarity(bags[i], bags[j])
            if weight > 0:
                graph.add_edge(i, j, weight=weight)

    scores = nx.pagerank(graph, weight="weight") if graph.number_of_edges() else {}
    # turns with no words at all (only an attachment placeholder) are picked last; ties and an
    # edgeless graph fall back to longer turns first, then earlier ones
    ranked = sorted(
        range(len(turns)), key=lambda i: (not bags[i], -scores.get(i, 0.0), -len(bags[i]), i)
    )
    chosen = sorted(ranked[:k])
    return "\n".join(f"{turns[i][0]}: {turns[i][1]}" if turns[i][0] else turns[i][1] for i in chosen)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--k", type=int, default=2)
    parser.add_argument("--examples", type=int, default=3)
    args = parser.parse_args()

    from data.prepare import load_samsum

    test = load_samsum()["test"]
    for row in test.select(range(args.examples)):
        print(f"--- {row['id']} ---\n{textrank(row['dialogue'], args.k)}\n  reference: {row['summary']}\n")


if __name__ == "__main__":
    main()
