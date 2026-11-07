"""Bounded report rendering; one filter contract for CSV and PDF."""
import csv
import hashlib
import io
import threading
from pathlib import Path
from xml.sax.saxutils import escape

from ..domain.models import FeedbackFilter, ReportUnavailableError, ResourceLimitError
from ..domain.ports import FeedbackStore
from ..settings import Settings

FONT_LOCK = threading.Lock()
FIELDS = ["id", "raw_text", "text", "source", "created_at", "received_at", "sentiment_label",
          "sentiment_confidence", "topic_label", "topic_confidence", "model_version", "predicted_at"]


def spreadsheet_safe(value):
    if isinstance(value, str) and (value.startswith(("\t", "\r", "\n"))
                                 or value.lstrip().startswith(("=", "+", "-", "@"))):
        return "'" + value
    return value


class ReportService:
    def __init__(self, repository: FeedbackStore, settings: Settings):
        self.repository = repository
        self.settings = settings

    def rows(self, filters: FeedbackFilter) -> list[dict]:
        rows = self.repository.export_rows(filters, self.settings.max_export_rows + 1)
        if len(rows) > self.settings.max_export_rows:
            raise ResourceLimitError("Quá nhiều phản hồi để xuất; hãy thu hẹp bộ lọc.")
        return rows

    def csv(self, filters: FeedbackFilter) -> bytes:
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=FIELDS)
        writer.writeheader()
        for row in self.rows(filters):
            writer.writerow({name: spreadsheet_safe(row[name]) for name in FIELDS})
        return ("\ufeff" + output.getvalue()).encode("utf-8")

    def pdf(self, filters: FeedbackFilter) -> bytes:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

        rows = self.rows(filters)
        candidates = ([self.settings.pdf_font_path] if self.settings.pdf_font_path else [
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ])
        font_path = next((path for path in candidates if path.is_file()), None)
        if font_path is None:
            raise ReportUnavailableError("Chưa có font Unicode; hãy cấu hình PDF_FONT_PATH.")
        font = "Feedback-" + hashlib.sha256(str(font_path).encode()).hexdigest()[:12]
        with FONT_LOCK:
            if font not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(font, str(font_path)))
        normal = ParagraphStyle("Feedback", fontName=font, fontSize=10, leading=15,
                                textColor=colors.HexColor("#1f2937"), splitLongWords=True)
        title = ParagraphStyle("Title", parent=normal, fontSize=17, leading=23, spaceAfter=12)
        story = [Paragraph("Báo cáo phản hồi sinh viên", title),
                 Paragraph(f"Tổng phản hồi: {len(rows)}", normal)]
        filter_text = "; ".join(f"{key}={value}" for key, value in vars(filters).items() if value is not None)
        story.extend([Paragraph("Bộ lọc: " + escape(filter_text or "Tất cả"), normal), Spacer(1, 12)])
        from collections import Counter
        from reportlab.graphics.shapes import Drawing, Rect, String
        from ..labels import SENTIMENT_LABELS, TOPIC_LABELS
        for field, heading, mapping in (
            ("sentiment_label", "Phân bố cảm xúc", SENTIMENT_LABELS),
            ("topic_label", "Phân bố chủ đề", TOPIC_LABELS),
        ):
            counts = Counter(row[field] for row in rows)
            story.append(Paragraph(heading, normal))
            chart = Drawing(500, len(mapping) * 25 + 5)
            maximum = max(counts.values(), default=1) or 1
            for index, label in enumerate(mapping.values()):
                y = (len(mapping) - index - 1) * 25 + 5
                chart.add(String(0, y + 4, label, fontName=font, fontSize=9))
                width = counts[label] / maximum * 240
                chart.add(Rect(120, y, width, 15, fillColor=colors.HexColor("#2563eb"), strokeColor=None))
                chart.add(String(370, y + 4, str(counts[label]), fontName=font, fontSize=9))
            story.extend([chart, Spacer(1, 12)])
        for row in rows:
            story.append(Paragraph(escape(
                f"#{row['id']} — {row['sentiment_label']} / {row['topic_label']}"
                f" — {row['predicted_at']}"), normal))
            story.append(Paragraph(escape(row["raw_text"] or row["text"]), normal))
            story.append(Spacer(1, 10))
        output = io.BytesIO()
        document = SimpleDocTemplate(output, pagesize=A4, leftMargin=36, rightMargin=36,
                                     topMargin=36, bottomMargin=36, title="Báo cáo phản hồi sinh viên")
        document.build(story)
        return output.getvalue()
