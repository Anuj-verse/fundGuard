from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.config import GROQ_MODEL, LLM_PROVIDER, OLLAMA_MODEL, get_llm_client
from app.schemas import ExplainRequest, ExplainResponse, SimilarCase


def _build_prompt(request: ExplainRequest, similar_cases: list[dict[str, Any]]) -> str:
    similar_cases_text = json.dumps(similar_cases, indent=2, ensure_ascii=False)
    graph_text = json.dumps(request.graph_subnetwork, indent=2, ensure_ascii=False)
    pattern_flags = ", ".join(request.pattern_flags) if request.pattern_flags else "None"
    transactions = ", ".join(request.transaction_ids) if request.transaction_ids else "None"

    return f"""You are a financial fraud analyst writing an internal explainability note.

Return ONLY valid JSON with these keys:
- investigation_summary: a concise summary of why the case is suspicious
- risk_rationale: detailed rationale referencing the graph evidence, patterns, and similar cases
- str_draft: a FIU-IND style STR draft as XML text inside one JSON string value

Rules:
- Keep the language formal and operational.
- Use the graph evidence and similar cases in the explanation.
- Make the STR draft plausible, structured, and compliant in tone.
- Do not wrap the JSON in markdown fences.

Case context:
account_id: {request.account_id}
transaction_ids: {transactions}
risk_score: {request.risk_score}
pattern_flags: {pattern_flags}

Graph subnetwork:
{graph_text}

Similar cases:
{similar_cases_text}
"""


def _extract_message_text(response: Any) -> str:
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        message = response.get("message")
        if isinstance(message, dict):
            return message.get("content", "")
        return response.get("content", "")
    choices = getattr(response, "choices", None)
    if choices:
        first_choice = choices[0]
        message = getattr(first_choice, "message", None)
        if message is not None:
            return getattr(message, "content", "") or ""
    return getattr(response, "content", "") or ""


def _parse_json_payload(raw_text: str) -> dict[str, Any]:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("LLM response did not contain a JSON object")

    return json.loads(cleaned[start : end + 1])


def _fallback_response(request: ExplainRequest, similar_cases: list[dict[str, Any]]) -> dict[str, Any]:
    similar_summary = "; ".join(case["summary"] for case in similar_cases) if similar_cases else "No comparable cases were retrieved."
    return {
        "investigation_summary": (
            f"Account {request.account_id} shows elevated fraud indicators with risk score {request.risk_score:.2f}."
        ),
        "risk_rationale": (
            f"Pattern flags: {', '.join(request.pattern_flags) if request.pattern_flags else 'none'}. "
            f"Similar cases: {similar_summary}"
        ),
        "str_draft": (
            "<STR><CaseId>{case_id}</CaseId><AccountId>{account_id}</AccountId>"
            "<RiskScore>{risk_score}</RiskScore><Narrative>Manual review recommended.</Narrative></STR>"
        ).format(case_id=request.case_id or request.account_id, account_id=request.account_id, risk_score=request.risk_score),
    }


def generate_explanation(request: ExplainRequest, similar_cases: list[dict[str, Any]]) -> ExplainResponse:
    prompt = _build_prompt(request, similar_cases)
    client = get_llm_client()

    try:
        if LLM_PROVIDER == "groq":
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You write structured fraud investigation outputs."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
        else:
            response = client.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": "You write structured fraud investigation outputs."},
                    {"role": "user", "content": prompt},
                ],
                options={"temperature": 0.2},
            )

        raw_text = _extract_message_text(response)
        payload = _parse_json_payload(raw_text)
    except Exception:
        payload = _fallback_response(request, similar_cases)

    now = datetime.now(timezone.utc)
    case_id = request.case_id or f"case-{request.account_id}"
    return ExplainResponse(
        case_id=case_id,
        account_id=request.account_id,
        generated_at=now,
        investigation_summary=str(payload.get("investigation_summary", "")),
        risk_rationale=str(payload.get("risk_rationale", "")),
        str_draft=str(payload.get("str_draft", "")),
        similar_cases=[
            SimilarCase(
                case_id=str(item.get("case_id", "unknown-case")),
                summary=str(item.get("summary", "")),
                similarity=item.get("similarity"),
            )
            for item in similar_cases
        ],
    )
