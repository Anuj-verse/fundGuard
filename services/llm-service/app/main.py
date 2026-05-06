from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

from app.llm import generate_explanation
from app.pdf_gen import build_pdf_report
from app.rag import retrieve_similar_cases
from app.schemas import ExplainRequest, ExplainResponse, ReportRequest


app = FastAPI(title="FundGuard LLM Explainability Service")

REPORT_CACHE: dict[str, ExplainResponse] = {}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/explain", response_model=ExplainResponse)
def explain(request: ExplainRequest) -> ExplainResponse:
    query = " ".join(
        [
            request.account_id,
            " ".join(request.transaction_ids),
            " ".join(request.pattern_flags),
            str(request.graph_subnetwork),
        ]
    ).strip()

    similar_cases = retrieve_similar_cases(query or request.account_id)
    response = generate_explanation(request, similar_cases)
    REPORT_CACHE[response.case_id] = response
    return response


@app.post("/report/{case_id}")
def report(case_id: str, request: ReportRequest | None = None) -> Response:
    report_data = REPORT_CACHE.get(case_id)
    if report_data is None:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found in memory")

    pdf_bytes = build_pdf_report(report_data, title=request.title if request else None)
    filename = f"{case_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
