"""
Gait Analyzer - PDF Report Generator
======================================
Generates professional PDF reports from gait analysis data.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image, PageBreak, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
from pathlib import Path
import json
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO


def create_gait_report(output_path: str, patient_data: dict, metrics, 
                       keypoints_data: list, plots: dict = None,
                       ai_report: str = None, anamnese_data: dict = None) -> str:
    """
    Create a professional PDF gait analysis report.
    
    Args:
        output_path: Path to save the PDF
        patient_data: Patient information dictionary
        metrics: GaitMetrics object with calculated metrics
        keypoints_data: Raw keypoints data for additional analysis
        plots: Dictionary of plot images (optional)
    
    Returns:
        Path to generated PDF
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Container for elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a472a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c5f2d'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#4a7c59'),
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        alignment=TA_JUSTIFY
    )
    
    # ===== TITLE PAGE =====
    elements.append(Spacer(1, 3*cm))
    elements.append(Paragraph("🎬 Gait Analyzer", title_style))
    elements.append(Paragraph("<i>Professionelle Ganganalyse</i>", 
                              ParagraphStyle('Subtitle', parent=normal_style, 
                                           alignment=TA_CENTER, fontSize=14, 
                                           textColor=colors.grey)))
    elements.append(Spacer(1, 2*cm))
    
    # Patient info box
    patient_info = [
        ["Patienten-ID:", patient_data.get('patient_id', 'N/A')],
        ["Datum:", datetime.now().strftime('%d.%m.%Y')],
        ["Untersuchungsdauer:", f"{patient_data.get('duration_seconds', 0):.1f} Sekunden"],
        ["Frames analysiert:", str(patient_data.get('total_frames', 0))],
    ]
    
    patient_table = Table(patient_info, colWidths=[4*cm, 8*cm])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f5e9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(patient_table)
    elements.append(Spacer(1, 1*cm))
    
    if patient_data.get('notes'):
        elements.append(Paragraph("<b>Notizen:</b>", subheading_style))
        elements.append(Paragraph(patient_data['notes'], normal_style))
        elements.append(Spacer(1, 0.5*cm))
    
    elements.append(PageBreak())
    
    # ===== EXECUTIVE SUMMARY =====
    elements.append(Paragraph("📋 Zusammenfassung", heading_style))
    
    summary_text = generate_summary_text(metrics)
    elements.append(Paragraph(summary_text, normal_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Key findings
    findings = []
    if metrics.has_asymmetry:
        findings.append(f"⚠️ Asymmetrisches Gangbild (Symmetrie-Index: {metrics.symmetry_index:.1f}%)")
    else:
        findings.append("✅ Symmetrischer Gang")
    
    if metrics.cadence > 0:
        if metrics.cadence < 90:
            findings.append(f"📉 Niedrige Cadenz ({metrics.cadence:.1f} Schritte/min)")
        elif metrics.cadence > 130:
            findings.append(f"📈 Erhöhte Cadenz ({metrics.cadence:.1f} Schritte/min)")
        else:
            findings.append(f"✅ Normale Cadenz ({metrics.cadence:.1f} Schritte/min)")
    
    if findings:
        elements.append(Paragraph("<b>Wichtige Befunde:</b>", subheading_style))
        for finding in findings:
            elements.append(Paragraph(f"• {finding}", normal_style))
    
    elements.append(PageBreak())
    
    # ===== TEMPORAL PARAMETERS =====
    elements.append(Paragraph("⏱️ Zeitliche Parameter", heading_style))
    
    temporal_data = [
        ["Parameter", "Wert", "Referenz", "Bewertung"],
        ["Schrittanzahl", str(metrics.step_count), "-", "-"],
        ["Cadenz", f"{metrics.cadence:.1f} Schritte/min", "100-120", 
         "✅ Normal" if 90 <= metrics.cadence <= 130 else "⚠️ Auffällig"],
        ["Schrittzeit links", f"{metrics.step_time_left:.2f} s", "~1.0s", "-"],
        ["Schrittzeit rechts", f"{metrics.step_time_right:.2f} s", "~1.0s", "-"],
        ["Doppelstandphase", f"{metrics.double_support_percent:.1f}%", "10-20%",
         "✅ Normal" if 10 <= metrics.double_support_percent <= 20 else "⚠️ Auffällig"],
        ["Einfachstandphase", f"{metrics.single_support_percent:.1f}%", "~40%", "-"],
        ["Swing Phase Links", f"{metrics.swing_phase_left:.1f}%", "~40%", "-"],
        ["Swing Phase Rechts", f"{metrics.swing_phase_right:.1f}%", "~40%", "-"],
    ]
    
    temporal_table = Table(temporal_data, colWidths=[4.5*cm, 3.5*cm, 2.5*cm, 3*cm])
    temporal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5f2d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(temporal_table)
    elements.append(Spacer(1, 0.5*cm))
    
    elements.append(PageBreak())
    
    # ===== SPATIAL PARAMETERS =====
    elements.append(Paragraph("📏 Räumliche Parameter", heading_style))
    
    spatial_data = [
        ["Parameter", "Links", "Rechts", "Durchschnitt"],
        ["Schrittlänge", f"{metrics.step_length_left:.1f} cm", 
         f"{metrics.step_length_right:.1f} cm",
         f"{(metrics.step_length_left + metrics.step_length_right)/2:.1f} cm"],
        ["Schrittbreite", "-", "-", f"{metrics.step_width:.1f} cm"],
        ["Base of Support", "-", "-", f"{metrics.base_of_support:.1f} cm"],
    ]
    
    spatial_table = Table(spatial_data, colWidths=[4*cm, 3.5*cm, 3.5*cm, 3.5*cm])
    spatial_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5f2d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(spatial_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Symmetry section
    elements.append(Paragraph("⚖️ Symmetrie-Analyse", subheading_style))
    
    if metrics.symmetry_index > 0:
        symmetry_text = f"""
        Der Symmetrie-Index beträgt <b>{metrics.symmetry_index:.1f}%</b>. 
        {"<font color='green'>✅ Dies ist im normalen Bereich (<10%).</font>" if metrics.symmetry_index < 10 else "<font color='red'>⚠️ Dies deutet auf eine Asymmetrie hin (>10%).</font>"}
        <br/><br/>
        Links/Rechts-Verhältnis: <b>{metrics.left_right_ratio:.2f}</b> 
        (1.0 = perfekt symmetrisch)
        """
        elements.append(Paragraph(symmetry_text, normal_style))
    
    elements.append(PageBreak())
    
    # ===== KINEMATIC ANALYSIS =====
    elements.append(Paragraph("🦴 Kinematische Analyse", heading_style))
    
    if metrics.max_knee_flexion > 0:
        elements.append(Paragraph("<b>Kniegelenk:</b>", subheading_style))
        elements.append(Paragraph(
            f"Maximale Knieflexion: <b>{metrics.max_knee_flexion:.1f}°</b> "
            f"(Normal: 60-70° während Swing Phase)", normal_style))
        elements.append(Spacer(1, 0.3*cm))
    
    if metrics.hip_range_of_motion > 0:
        elements.append(Paragraph("<b>Hüftgelenk:</b>", subheading_style))
        elements.append(Paragraph(
            f"Bewegungsausmaß: <b>{metrics.hip_range_of_motion:.1f}°</b>", 
            normal_style))
    
    elements.append(PageBreak())
    
    # ===== AI REPORT =====
    if ai_report:
        elements.append(PageBreak())
        elements.append(Paragraph("🤖 KI-Bericht", heading_style))
        
        # Clean and format AI report text for PDF
        import re
        
        # Simple approach: convert markdown to plain text first
        ai_text = ai_report
        
        # Remove ALL HTML-like tags first
        ai_text = re.sub(r'<[^>]+>', '', ai_text)
        
        # Remove markdown bold and italic
        ai_text = re.sub(r'\*\*(.*?)\*\*', r'\1', ai_text)
        ai_text = re.sub(r'\*(.*?)\*', r'\1', ai_text)
        
        # Remove markdown headers
        ai_text = re.sub(r'^#+\s+', '', ai_text, flags=re.MULTILINE)
        
        # Replace horizontal rules
        ai_text = ai_text.replace('---', '')
        
        # Split by paragraphs and add as simple text
        paragraphs = ai_text.split('\n\n')
        for para in paragraphs:
            para = para.strip()
            if para:
                # Escape HTML special chars
                para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                # Convert newlines to breaks
                para = para.replace('\n', '<br/>')
                elements.append(Paragraph(para, normal_style))
                elements.append(Spacer(1, 0.3*cm))
        
        elements.append(Spacer(1, 0.5*cm))
    
    # ===== ANAMNESE =====
    if anamnese_data:
        elements.append(PageBreak())
        elements.append(Paragraph("📋 Anamnese", heading_style))
        
        anamnese_items = [
            ("Patienten-ID", anamnese_data.get('patient_id', 'N/A')),
            ("Alter", f"{anamnese_data.get('alter', 'N/A')} Jahre"),
            ("Geschlecht", anamnese_data.get('geschlecht', 'N/A')),
            ("Größe", f"{anamnese_data.get('groesse', 'N/A')} cm"),
            ("Gewicht", f"{anamnese_data.get('gewicht', 'N/A')} kg"),
            ("BMI", f"{anamnese_data.get('bmi', 'N/A')}"),
            ("Hauptbeschwerde", anamnese_data.get('hauptbeschwerde', 'N/A')),
        ]
        
        if anamnese_data.get('schmerz_ort'):
            anamnese_items.append(("Schmerzlokalisation", ', '.join(anamnese_data['schmerz_ort'])))
        if anamnese_data.get('schmerz_intensitaet') is not None:
            anamnese_items.append(("Schmerzintensität", f"{anamnese_data['schmerz_intensitaet']}/10"))
        if anamnese_data.get('therapie_ziel'):
            anamnese_items.append(("Therapieziel", anamnese_data['therapie_ziel']))
        
        for label, value in anamnese_items:
            elements.append(Paragraph(f"<b>{label}:</b> {value}", normal_style))
            elements.append(Spacer(1, 0.15*cm))
    
    # ===== RECOMMENDATIONS =====
    elements.append(Paragraph("💡 Empfehlungen", heading_style))
    
    recommendations = generate_recommendations(metrics)
    for rec in recommendations:
        elements.append(Paragraph(f"• {rec}", normal_style))
        elements.append(Spacer(1, 0.2*cm))
    
    # Footer
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(
        f"<i>Bericht erstellt am {datetime.now().strftime('%d.%m.%Y um %H:%M')} "
        f"mit Gait Analyzer v1.0</i>",
        ParagraphStyle('Footer', parent=normal_style, alignment=TA_CENTER, 
                      fontSize=9, textColor=colors.grey)
    ))
    
    # Build PDF
    doc.build(elements)
    return output_path


def generate_summary_text(metrics) -> str:
    """Generate executive summary text."""
    parts = []
    
    if metrics.step_count > 0:
        parts.append(f"Die Analyse umfasst <b>{metrics.step_count} Schritte</b> ")
        parts.append(f"bei einer Cadenz von <b>{metrics.cadence:.1f} Schritten pro Minute</b>. ")
    
    if metrics.has_asymmetry:
        parts.append(f"Es wurde eine <b>asymmetrische Gangmuster</b> mit einem Symmetrie-Index ")
        parts.append(f"von {metrics.symmetry_index:.1f}% festgestellt. ")
    else:
        parts.append("Das Gangbild zeigt <b>symmetrische Muster</b>. ")
    
    if metrics.step_length_left > 0 or metrics.step_length_right > 0:
        avg_length = (metrics.step_length_left + metrics.step_length_right) / 2
        parts.append(f"Die durchschnittliche Schrittlänge beträgt <b>{avg_length:.1f} cm</b>.")
    
    return "".join(parts)


def generate_recommendations(metrics) -> list:
    """Generate clinical recommendations based on metrics."""
    recs = []
    
    if metrics.has_asymmetry:
        recs.append("Aufgrund der festgestellten Asymmetrie wird eine weitere physiotherapeutische Untersuchung empfohlen.")
        recs.append("Übungen zur Verbesserung der Gleichgewichtigkeit zwischen linker und rechter Seite sollten in Betracht gezogen werden.")
    
    if metrics.cadence < 90:
        recs.append("Die niedrige Cadenz könnte auf eine verlangsamte Fortbewegung hinweisen. Kardiovaskuläre Übungen zur Steigerung der Gehgeschwindigkeit können hilfreich sein.")
    elif metrics.cadence > 130:
        recs.append("Die erhöhte Cadenz kann auf einen hastigen Gang hinweisen. Übungen zur Verlangsamung und Stabilisierung des Gangs werden empfohlen.")
    
    if metrics.max_knee_flexion < 50:
        recs.append("Die verminderte Knieflexion während der Schwungphase sollte durch Dehnübungen und Mobilitätstraining für das Kniegelenk adressiert werden.")
    
    if not recs:
        recs.append("Das Gangbild liegt im physiologischen Normbereich. Regelmäßige Bewegung und Muskelaufbau werden zur Prophylaxe empfohlen.")
    
    return recs


def create_metric_plot(timestamps, values, title, ylabel, color='#1f77b4'):
    """Create a simple metric plot and return as BytesIO."""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(timestamps, values, color=color, linewidth=2)
    ax.set_xlabel('Zeit (s)')
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf
