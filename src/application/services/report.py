from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import List, Union

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.application.services.ai_explainer import DeadlockExplanation


class ReportService:

    @staticmethod
    def generate_pdf_report(
        processes: List[dict],
        resources: List[dict],
        allocations: List[dict],
        deadlock_cycle: List[str],
        ai_explanation: Union[str, DeadlockExplanation],
    ) -> bytes:
        """Generate a downloadable A4 PDF report representing the system simulation state."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Document Header
        story.append(Paragraph("DeadlockAI Enterprise Report", styles["Title"]))
        story.append(Spacer(1, 8))
        story.append(
            Paragraph(
                f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 15))

        # Processes section
        story.append(Paragraph("System Processes", styles["Heading2"]))
        story.append(Spacer(1, 5))
        proc_rows = [[p["pid"], p["state"]] for p in processes]
        story.append(ReportService._make_table(["Process ID", "State"], proc_rows))
        story.append(Spacer(1, 15))

        # Resources section
        story.append(Paragraph("System Resources", styles["Heading2"]))
        story.append(Spacer(1, 5))
        res_rows = [
            [
                r["rid"],
                r["total_instances"],
                r["allocated_instances"],
                r["total_instances"] - r["allocated_instances"],
            ]
            for r in resources
        ]
        story.append(
            ReportService._make_table(
                ["Resource ID", "Total Instances", "Allocated", "Available"],
                res_rows,
            )
        )
        story.append(Spacer(1, 15))

        # Allocations section
        story.append(Paragraph("Current Resource Allocations", styles["Heading2"]))
        story.append(Spacer(1, 5))
        alloc_rows = [[a["resource"], a["process"]] for a in allocations]
        story.append(ReportService._make_table(["Resource", "Allocated To"], alloc_rows))
        story.append(Spacer(1, 15))

        # Deadlock state section
        cycle_text = " -> ".join(deadlock_cycle) if deadlock_cycle else "No cycle detected"
        story.append(Paragraph("Deadlock Status", styles["Heading2"]))
        story.append(Spacer(1, 5))
        story.append(
            Paragraph(
                f"<b>Status:</b> {'DEADLOCKED' if deadlock_cycle else 'SAFE'}<br/>"
                f"<b>Dependency Cycle:</b> {cycle_text}",
                styles["BodyText"],
            )
        )
        story.append(Spacer(1, 15))

        # AI Analysis Section
        story.append(Paragraph("AI Diagnosis & Recommendation", styles["Heading2"]))
        story.append(Spacer(1, 5))

        if isinstance(ai_explanation, DeadlockExplanation):
            # Format structured output
            story.append(Paragraph("<b>Why it happened:</b>", styles["Heading3"]))
            story.append(Paragraph(ai_explanation.why_occurred, styles["BodyText"]))
            story.append(Spacer(1, 5))

            story.append(Paragraph("<b>Coffman Conditions Met:</b>", styles["Heading3"]))
            for cond in ai_explanation.coffman_conditions:
                story.append(Paragraph(f"• {cond}", styles["BodyText"]))
            story.append(Spacer(1, 5))

            story.append(Paragraph("<b>Resolution Strategies:</b>", styles["Heading3"]))
            for strategy in ai_explanation.resolution_strategies:
                story.append(Paragraph(f"• {strategy}", styles["BodyText"]))
            story.append(Spacer(1, 5))

            story.append(Paragraph("<b>Prevention Techniques:</b>", styles["Heading3"]))
            for technique in ai_explanation.prevention_techniques:
                story.append(Paragraph(f"• {technique}", styles["BodyText"]))
            story.append(Spacer(1, 5))

            story.append(
                Paragraph("<b>Banker's Algorithm Recommendation:</b>", styles["Heading3"])
            )
            story.append(Paragraph(ai_explanation.banker_recommendation, styles["BodyText"]))
        else:
            # Fallback formatting for plain string
            story.append(
                Paragraph(ai_explanation.replace("\n", "<br/>"), styles["BodyText"])
            )

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def _make_table(headers: List[str], rows: List[List[object]]) -> Table:
        payload = [headers]
        payload.extend(rows if rows else [["-" for _ in headers]])
        table = Table(payload)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return table
