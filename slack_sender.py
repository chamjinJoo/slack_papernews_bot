from __future__ import annotations

from collections.abc import Sequence

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from arxiv_fetcher import Paper
from llm_explainer import PaperExplanation


def _truncate(value: str, max_length: int = 600) -> str:
    value = " ".join(value.split())
    if len(value) <= max_length:
        return value
    return value[: max_length - 3].rstrip() + "..."


def format_paper_message(
    paper: Paper,
    score: int,
    explanation: PaperExplanation,
    index: int,
) -> str:
    authors = ", ".join(paper.authors[:5])
    if len(paper.authors) > 5:
        authors += " et al."

    return (
        f"*{index}. {paper.title}*\n"
        f"- Score: {score}\n"
        f"- Field: {_truncate(explanation.field) or '-'}\n"
        f"- Core idea: {_truncate(explanation.core_idea) or '-'}\n"
        f"- Note: {_truncate(explanation.note) or '-'}\n"
        f"- Authors: {authors or '-'}\n"
        f"- Published: {paper.published.date().isoformat()}\n"
        f"- Link: {paper.url}"
    )


def build_digest_message(
    ranked_papers: Sequence[tuple[Paper, int]],
    explanations: Sequence[PaperExplanation],
) -> str:
    lines = ["*Daily ML Paper Digest - arXiv 최신 논문 브리핑*"]
    for index, ((paper, score), explanation) in enumerate(
        zip(ranked_papers, explanations, strict=True),
        start=1,
    ):
        lines.append(format_paper_message(paper, score, explanation, index))
    return "\n\n".join(lines)


def send_dm(
    token: str,
    user_id: str,
    text: str,
    client: WebClient | None = None,
) -> None:
    slack_client = client or WebClient(token=token)

    try:
        dm = slack_client.conversations_open(users=user_id)
        channel_id = dm["channel"]["id"]
        slack_client.chat_postMessage(channel=channel_id, text=text)
    except SlackApiError as exc:
        detail = exc.response.get("error", "unknown_error") if exc.response else "unknown_error"
        raise RuntimeError(f"Failed to send Slack DM: {detail}") from exc
    except Exception as exc:
        raise RuntimeError("Failed to send Slack DM") from exc
