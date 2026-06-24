from __future__ import annotations

import logging

from arxiv_fetcher import fetch_recent_papers
from config import load_config
from llm_explainer import explain_papers
from ranking import rank_papers
from slack_sender import build_digest_message, send_dm


def run() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    config = load_config()

    papers = fetch_recent_papers(
        categories=config.arxiv_categories,
        max_results=config.arxiv_max_results,
        delay_seconds=config.arxiv_delay_seconds,
        num_retries=config.arxiv_num_retries,
    )
    ranked = rank_papers(papers)
    top_ranked = ranked[: config.top_n]
    top_papers = [paper for paper, _score in top_ranked]

    explanations = explain_papers(
        top_papers,
        api_key=config.gemini_api_key,
        model=config.gemini_model,
    )
    message = build_digest_message(top_ranked, explanations)

    send_dm(
        token=config.slack_bot_token,
        user_id=config.slack_user_id,
        text=message,
    )


if __name__ == "__main__":
    run()
