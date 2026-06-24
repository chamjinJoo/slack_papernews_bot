from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Sequence

from dotenv import load_dotenv


DEFAULT_CATEGORIES = ("cs.LG", "cs.AI", "stat.ML")
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


@dataclass(frozen=True)
class AppConfig:
    slack_bot_token: str
    slack_user_id: str
    gemini_api_key: str
    gemini_model: str = DEFAULT_GEMINI_MODEL
    arxiv_categories: Sequence[str] = field(default_factory=lambda: DEFAULT_CATEGORIES)
    arxiv_max_results: int = 100
    arxiv_delay_seconds: float = 15.0
    arxiv_num_retries: int = 6
    top_n: int = 5


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if not raw_value:
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an integer") from exc


def _float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if not raw_value:
        return default

    try:
        return float(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be a number") from exc


def load_config() -> AppConfig:
    load_dotenv()

    categories = tuple(
        item.strip()
        for item in os.getenv("ARXIV_CATEGORIES", ",".join(DEFAULT_CATEGORIES)).split(",")
        if item.strip()
    )

    return AppConfig(
        slack_bot_token=_required_env("SLACK_BOT_TOKEN"),
        slack_user_id=_required_env("SLACK_USER_ID"),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
        arxiv_categories=categories or DEFAULT_CATEGORIES,
        arxiv_max_results=_int_env("ARXIV_MAX_RESULTS", 100),
        arxiv_delay_seconds=_float_env("ARXIV_DELAY_SECONDS", 15.0),
        arxiv_num_retries=_int_env("ARXIV_NUM_RETRIES", 6),
        top_n=_int_env("TOP_N", 5),
    )
