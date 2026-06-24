from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, TypedDict

from google import genai
from google.genai import types

from arxiv_fetcher import Paper


logger = logging.getLogger(__name__)

FALLBACK_MODELS = (
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-flash-latest",
)


class PaperExplanationSchema(TypedDict):
    field: str
    core_idea: str
    note: str


@dataclass(frozen=True)
class PaperExplanation:
    field: str
    core_idea: str
    note: str


PARSE_FAILURE_EXPLANATION = PaperExplanation(
    field="Unknown",
    core_idea="초록 기반 핵심 아이디어를 자동 생성하지 못했습니다.",
    note="Gemini 응답 파싱에 실패했습니다.",
)

API_FAILURE_EXPLANATION = PaperExplanation(
    field="Unknown",
    core_idea="초록 기반 핵심 아이디어를 자동 생성하지 못했습니다.",
    note="Gemini API 호출에 실패했습니다.",
)


def fallback_explanation(_paper: Paper) -> PaperExplanation:
    return API_FAILURE_EXPLANATION


def _build_prompt(paper: Paper) -> str:
    paper_payload = {
        "title": paper.title,
        "authors": paper.authors,
        "published": paper.published.date().isoformat(),
        "abstract": paper.abstract,
    }

    return (
        "당신은 머신러닝 논문을 한국어로 쉽게 설명하는 연구 도우미입니다.\n"
        "아래 논문의 title과 abstract만 근거로 짧은 설명 노트를 작성하세요.\n"
        "평가, 비판, 점수화, 과장된 표현은 하지 말고 이해를 돕는 설명만 작성하세요.\n"
        "반드시 JSON 객체 하나만 반환하세요. 코드블록, 마크다운, 추가 문장, 주석은 금지입니다.\n"
        "JSON 키는 정확히 field, core_idea, note 세 개만 사용하세요.\n"
        "field: 논문 분야를 한국어 짧은 구로 작성하세요.\n"
        "core_idea: 핵심 아이디어를 한국어 한 문장으로 작성하세요.\n"
        "note: 생소한 핵심 개념이나 기술을 대학원생 수준에서 한국어 1~2문장으로 설명하세요.\n\n"
        f"논문 정보:\n{json.dumps(paper_payload, ensure_ascii=False)}"
    )


def _parse_json_object(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or start >= end:
            raise
        data = json.loads(text[start : end + 1])

    if not isinstance(data, dict):
        raise ValueError("Gemini response is not a JSON object")
    return data


def _clean_explanation(data: dict[str, Any]) -> PaperExplanation:
    return PaperExplanation(
        field=str(data.get("field", "")).strip() or "Unknown",
        core_idea=str(data.get("core_idea", "")).strip()
        or "초록 기반 핵심 아이디어를 자동 생성하지 못했습니다.",
        note=str(data.get("note", "")).strip() or "Gemini 응답에 note가 없습니다.",
    )


def _candidate_models(model: str) -> list[str]:
    models = [model, *FALLBACK_MODELS]
    return list(dict.fromkeys(item for item in models if item))


def _generate_content(
    client: genai.Client,
    paper: Paper,
    models: list[str],
):
    last_error: Exception | None = None

    for model_name in models:
        try:
            return client.models.generate_content(
                model=model_name,
                contents=_build_prompt(paper),
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=PaperExplanationSchema,
                ),
            )
        except Exception as exc:
            last_error = exc
            logger.warning("Gemini model %s failed; trying next fallback if available: %s", model_name, exc)

    if last_error is not None:
        raise last_error
    raise RuntimeError("No Gemini model candidates were provided")


def explain_paper(
    paper: Paper,
    api_key: str,
    model: str,
    client: genai.Client | None = None,
) -> PaperExplanation:
    if not api_key:
        logger.warning("GEMINI_API_KEY is missing; using fallback explanation.")
        return API_FAILURE_EXPLANATION

    gemini_client = client or genai.Client(api_key=api_key)

    try:
        response = _generate_content(gemini_client, paper, _candidate_models(model))
    except Exception as exc:
        logger.warning("All Gemini explanation attempts failed; using fallback: %s", exc)
        return API_FAILURE_EXPLANATION

    try:
        return _clean_explanation(_parse_json_object(response.text or ""))
    except Exception as exc:
        logger.warning("Gemini JSON parsing failed; using fallback: %s", exc)
        return PARSE_FAILURE_EXPLANATION


def explain_papers(
    papers: list[Paper],
    api_key: str,
    model: str,
) -> list[PaperExplanation]:
    if not api_key:
        logger.warning("GEMINI_API_KEY is missing; using fallback explanations.")
        return [API_FAILURE_EXPLANATION for _paper in papers]

    client = genai.Client(api_key=api_key)
    return [explain_paper(paper, api_key=api_key, model=model, client=client) for paper in papers]
