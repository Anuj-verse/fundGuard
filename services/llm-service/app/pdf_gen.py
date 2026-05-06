from __future__ import annotations

from io import BytesIO
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas import ExplainResponse


def _bullet_paragraphs(items: Iterable[str], style: ParagraphStyle) -> list[Paragraph]:
    return [Paragraph(f"&bull; {item}", style) for item in items]


def build_pdf_report(report: ExplainResponse, title: str | None = None) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=title or f"Fraud Explainability Report - {report.case_id}",
    )

    styles = getSampleStyleSheet()
    heading = ParagraphStyle(
        "Heading",
        parent=styles["Heading1"],
        alignment=TA_LEFT,
        textColor=colors.HexColor("#102A43"),
        fontSize=18,
        leading=22,
        spaceAfter=10,
    )
    subheading = ParagraphStyle(
        "Subheading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#334E68"),
        fontSize=12,
        leading=16,
        spaceBefore=8,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#243B53"),
        spaceAfter=6,
    )

    story = [
        Paragraph(title or "Fraud Explainability Report", heading),
        Paragraph(f"Case ID: {report.case_id}", body),
        Paragraph(f"Account ID: {report.account_id}", body),
        Paragraph(f"Generated at: {report.generated_at.isoformat()}", body),
        Spacer(1, 0.15 * inch),
        Paragraph("Investigation Summary", subheading),
        Paragraph(report.investigation_summary, body),
        Paragraph("Risk Rationale", subheading),
        Paragraph(report.risk_rationale, body),
        Paragraph("Similar Cases", subheading),
    ]

    if report.similar_cases:
        story.extend(_bullet_paragraphs((f"{case.case_id}: {case.summary}" for case in report.similar_cases), body))
    else:
        story.append(Paragraph("No similar cases were retrieved.", body))

    story.append(Paragraph("STR Draft", subheading))
    story.append(Paragraph(report.str_draft.replace("<", "&lt;").replace(">", "&gt;"), body))

    metadata_table = Table(
        [["Risk score", f"{report.generated_at:%Y-%m-%d %H:%M UTC}"], ["Similar case count", str(len(report.similar_cases))]],
        colWidths=[1.7 * inch, 3.7 * inch],
    )
    metadata_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E2EC")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#102A43")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BCCCDC")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(Spacer(1, 0.2 * inch))
    story.append(metadata_table)

    document.build(story)
    return buffer.getvalue()
