"""
CropVision - PDF Report Generation Service

Generates executive-grade agricultural satellite health diagnostic PDF reports
using ReportLab. Formatted for commercial agribusinesses, agronomists, and farm managers.
"""

import io
from datetime import datetime
from typing import Dict, Any, List

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def generate_crop_health_pdf(
    field_data: Dict[str, Any],
    analysis_data: Dict[str, Any],
    history_data: List[Dict[str, Any]],
) -> bytes:
    """
    Generate a formatted multi-section PDF report buffer.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Brand Styles
    brand_primary = colors.HexColor("#065f46")  # Deep Emerald
    brand_accent = colors.HexColor("#10b981")   # Vibrant Emerald
    bg_light = colors.HexColor("#f8fafc")       # Slate light
    text_dark = colors.HexColor("#0f172a")      # Slate dark
    text_muted = colors.HexColor("#475569")     # Slate muted
    border_color = colors.HexColor("#cbd5e1")
    
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=brand_primary,
    )
    
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=text_muted,
    )
    
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=brand_primary,
        spaceBefore=10,
        spaceAfter=6,
    )
    
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=text_dark,
    )
    
    body_bold = ParagraphStyle(
        "BodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=text_dark,
    )
    
    headline_style = ParagraphStyle(
        "HeadlineStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=brand_primary,
    )
    
    story = []
    
    # 1. Header Banner
    header_table_data = [
        [
            Paragraph("<b>CROPVISION</b> | Satellite Health Diagnostic", title_style),
            Paragraph(f"<b>Report Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/><b>Platform:</b> Sentinel-2 MSI Level-2A", subtitle_style),
        ]
    ]
    header_table = Table(header_table_data, colWidths=[3.8 * inch, 3.4 * inch])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=2, color=brand_primary, spaceBefore=6, spaceAfter=10))
    
    # 2. Field Profile & Key Metrics
    field_name = field_data.get("name", "Agricultural Field")
    crop_type = field_data.get("crop_type", "Crop")
    growth_stage = analysis_data.get("growth_stage", "VEGETATIVE").replace("_", " ").title()
    cchs_score = analysis_data.get("cchs_score", 0.0)
    classification = analysis_data.get("classification", {})
    health_label = classification.get("label", "Moderate")
    trend = analysis_data.get("trend", {})
    trend_label = trend.get("trend_label", "Stable")
    trend_arrow = trend.get("trend_arrow", "→")
    delta_baseline = trend.get("delta_vs_baseline", 0.0)
    
    metadata_data = [
        [
            Paragraph("<b>Field Name:</b>", body_style),
            Paragraph(str(field_name), body_bold),
            Paragraph("<b>Current CCHS Score:</b>", body_style),
            Paragraph(f"<font color='{classification.get('color', '#10b981')}'><b>{cchs_score} / 100</b> ({health_label})</font>", body_bold),
        ],
        [
            Paragraph("<b>Crop Type:</b>", body_style),
            Paragraph(str(crop_type), body_bold),
            Paragraph("<b>Historical Trajectory:</b>", body_style),
            Paragraph(f"{trend_arrow} {trend_label} ({delta_baseline:+.1f} pts vs baseline)", body_bold),
        ],
        [
            Paragraph("<b>Growth Stage:</b>", body_style),
            Paragraph(str(growth_stage), body_bold),
            Paragraph("<b>Scan Date:</b>", body_style),
            Paragraph(str(analysis_data.get("date", datetime.now().strftime("%Y-%m-%d"))), body_bold),
        ],
    ]
    meta_table = Table(metadata_data, colWidths=[1.3 * inch, 2.3 * inch, 1.6 * inch, 2.0 * inch])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_light),
        ("BOX", (0, 0), (-1, -1), 1, border_color),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))
    
    # 3. Plain Language Agronomic Assessment
    plain_lang = analysis_data.get("plain_language", {})
    story.append(Paragraph("Agronomic Diagnosis & Field Assessment", section_heading))
    
    diag_data = [
        [Paragraph(f"<b>Diagnosis:</b> {plain_lang.get('headline', 'Field Assessment')}", headline_style)],
        [Paragraph(f"{plain_lang.get('executive_summary', 'Analysis completed.')}", body_style)],
        [Paragraph(f"<b>Primary Stress Driver:</b> {plain_lang.get('primary_issue', 'None')} | <b>Location:</b> {plain_lang.get('affected_quadrant', 'Uniform')}", body_bold)],
    ]
    diag_table = Table(diag_data, colWidths=[7.2 * inch])
    diag_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#86efac")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(diag_table)
    story.append(Spacer(1, 10))
    
    # 4. Actionable Recommendations Checklist
    action_items = plain_lang.get("action_items", [])
    if action_items:
        story.append(Paragraph("Recommended Agronomic Actions", section_heading))
        rec_rows = [
            [
                Paragraph("<b>Priority</b>", body_bold),
                Paragraph("<b>Action Item</b>", body_bold),
                Paragraph("<b>Agronomic Rationale</b>", body_bold),
            ]
        ]
        for item in action_items:
            prio = item.get("priority", "MEDIUM")
            prio_color = "#ef4444" if prio == "HIGH" else "#f59e0b" if prio == "MEDIUM" else "#10b981"
            rec_rows.append([
                Paragraph(f"<font color='{prio_color}'><b>[{item.get('badge', prio)}]</b></font>", body_style),
                Paragraph(f"<b>{item.get('action', '')}</b>", body_style),
                Paragraph(f"{item.get('rationale', '')}", body_style),
            ])
        rec_table = Table(rec_rows, colWidths=[1.1 * inch, 3.2 * inch, 2.9 * inch])
        rec_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("BOX", (0, 0), (-1, -1), 1, border_color),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(rec_table)
        story.append(Spacer(1, 10))
    
    # 5. Biophysical Index Breakdown & Growth Stage Weights
    story.append(Paragraph("Multispectral Index Breakdown & Dynamic Weighting", section_heading))
    raw_indices = analysis_data.get("raw_indices", {})
    sub_scores = analysis_data.get("sub_scores", {})
    weights = analysis_data.get("weights_used", {})
    
    index_table_data = [
        [
            Paragraph("<b>Index</b>", body_bold),
            Paragraph("<b>Full Name / Physiological Target</b>", body_bold),
            Paragraph("<b>Raw Value</b>", body_bold),
            Paragraph("<b>Sub-Score (0-100)</b>", body_bold),
            Paragraph("<b>Stage Weight</b>", body_bold),
        ],
        [
            Paragraph("<b>NDVI</b>", body_bold),
            Paragraph("Normalized Difference Vegetation Index (Canopy Biomass & Greenness)", body_style),
            Paragraph(f"{raw_indices.get('ndvi', 0.0):.3f}", body_style),
            Paragraph(f"{sub_scores.get('ndvi_score', 0.0):.1f} / 100", body_style),
            Paragraph(f"{weights.get('ndvi', 0.25) * 100:.0f}%", body_style),
        ],
        [
            Paragraph("<b>EVI</b>", body_bold),
            Paragraph("Enhanced Vegetation Index (Canopy Structure & Soil Decoupling)", body_style),
            Paragraph(f"{raw_indices.get('evi', 0.0):.3f}", body_style),
            Paragraph(f"{sub_scores.get('evi_score', 0.0):.1f} / 100", body_style),
            Paragraph(f"{weights.get('evi', 0.25) * 100:.0f}%", body_style),
        ],
        [
            Paragraph("<b>GCI</b>", body_bold),
            Paragraph("Green Chlorophyll Index (Nitrogen Nutrition & Chlorophyll Status)", body_style),
            Paragraph(f"{raw_indices.get('gci', 0.0):.3f}", body_style),
            Paragraph(f"{sub_scores.get('gci_score', 0.0):.1f} / 100", body_style),
            Paragraph(f"{weights.get('gci', 0.25) * 100:.0f}%", body_style),
        ],
        [
            Paragraph("<b>NDWI</b>", body_bold),
            Paragraph("Normalized Difference Water Index (Canopy Moisture & Water Stress)", body_style),
            Paragraph(f"{raw_indices.get('ndwi', 0.0):.3f}", body_style),
            Paragraph(f"{sub_scores.get('ndwi_score', 0.0):.1f} / 100", body_style),
            Paragraph(f"{weights.get('ndwi', 0.25) * 100:.0f}%", body_style),
        ],
    ]
    idx_table = Table(index_table_data, colWidths=[0.8 * inch, 3.2 * inch, 1.0 * inch, 1.2 * inch, 1.0 * inch])
    idx_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("BOX", (0, 0), (-1, -1), 1, border_color),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(idx_table)
    story.append(Spacer(1, 10))
    
    # 6. Historical Trajectory Timeline
    if history_data:
        story.append(Paragraph("Historical Trajectory & Multi-Scan Progression", section_heading))
        hist_rows = [
            [
                Paragraph("<b>Date</b>", body_bold),
                Paragraph("<b>Growth Stage</b>", body_bold),
                Paragraph("<b>NDVI</b>", body_bold),
                Paragraph("<b>NDWI</b>", body_bold),
                Paragraph("<b>GCI</b>", body_bold),
                Paragraph("<b>CCHS Score</b>", body_bold),
                Paragraph("<b>Status</b>", body_bold),
            ]
        ]
        for h in history_data[-5:]:
            h_raw = h.get("raw_indices", {})
            hist_rows.append([
                Paragraph(str(h.get("date", "")), body_style),
                Paragraph(str(h.get("growth_stage", "")).replace("_", " ").title(), body_style),
                Paragraph(f"{h_raw.get('ndvi', 0.0):.2f}", body_style),
                Paragraph(f"{h_raw.get('ndwi', 0.0):.2f}", body_style),
                Paragraph(f"{h_raw.get('gci', 0.0):.2f}", body_style),
                Paragraph(f"<b>{h.get('cchs_score', 0.0):.1f}</b>", body_bold),
                Paragraph(str(h.get("status", "Good")), body_style),
            ])
        hist_table = Table(hist_rows, colWidths=[1.1 * inch, 1.4 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 1.1 * inch, 1.2 * inch])
        hist_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("BOX", (0, 0), (-1, -1), 1, border_color),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(hist_table)
        story.append(Spacer(1, 12))
    
    # 7. Footer Notice
    footer_text = Paragraph(
        "<font color='#64748b'>Generated automatically by CropVision MVP • Satellite data processed via Sentinel-2 MSI Level-2A • Contact agronomist for ground validation.</font>",
        subtitle_style,
    )
    story.append(footer_text)
    
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
