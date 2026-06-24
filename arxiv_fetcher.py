from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

import arxiv

from config import DEFAULT_CATEGORIES


@dataclass(frozen=True)
class Paper:
    title: str
    authors: list[str]
    published: datetime
    abstract: str
    url: str


def build_category_query(categories: Sequence[str] = DEFAULT_CATEGORIES) -> str:
    return " OR ".join(f"cat:{category}" for category in categories)


def result_to_paper(result: arxiv.Result) -> Paper:
    return Paper(
        title=result.title.strip(),
        authors=[author.name for author in result.authors],
        published=result.published,
        abstract=result.summary.strip(),
        url=result.entry_id,
    )


def fetch_recent_papers(
    categories: Sequence[str] = DEFAULT_CATEGORIES,
    max_results: int = 100,
    delay_seconds: float = 15.0,
    num_retries: int = 6,
    client: arxiv.Client | None = None,
) -> list[Paper]:
    search = arxiv.Search(
        query=build_category_query(categories),
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    arxiv_client = client or arxiv.Client(
        page_size=max_results,
        delay_seconds=delay_seconds,
        num_retries=num_retries,
    )

    try:
        return [result_to_paper(result) for result in arxiv_client.results(search)]
    except Exception as exc:
        raise RuntimeError("Failed to fetch papers from arXiv") from exc
