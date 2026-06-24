from __future__ import annotations

from collections.abc import Mapping, Sequence

from arxiv_fetcher import Paper


DEFAULT_KEYWORDS: dict[str, int] = {
    "reinforcement learning": 4,
    "control": 4,
    "world model": 4,
    "agent": 4,
    "reasoning": 4,
    "representation learning": 4,
    "optimization": 3,
    "interpretability": 3,
    "foundation model": 3,
    "causal": 3,
}


def keyword_score(
    paper: Paper,
    keywords: Mapping[str, int] = DEFAULT_KEYWORDS,
) -> int:
    text = f"{paper.title} {paper.abstract}".lower()
    return sum(weight for keyword, weight in keywords.items() if keyword.lower() in text)


def rank_papers(
    papers: Sequence[Paper],
    keywords: Mapping[str, int] = DEFAULT_KEYWORDS,
) -> list[tuple[Paper, int]]:
    scored = [(paper, keyword_score(paper, keywords)) for paper in papers]
    return sorted(scored, key=lambda item: (item[1], item[0].published), reverse=True)
