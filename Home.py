"""
Haile - Home
============
KI-gestützte Bewegungsanalyse.
"""

import streamlit as st
import json
from pathlib import Path

from app.components.linear_ui import render_linear_css

st.set_page_config(
    page_title="Haile",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_linear_css()

# Hero
st.markdown(
    '<div style="margin-bottom:2.5rem;">'
    '<h1 style="font-size:2rem;font-weight:700;color:#f8fafc;letter-spacing:-0.03em;margin-bottom:0.5rem;">Bewegungsanalyse</h1>'
    '<p style="color:#94a3b8;font-size:1.125rem;line-height:1.6;max-width:560px;">'
    'Präzise Bewegungsanalyse durch computergestützte Pose-Estimation. '
    'Ideal für Physiotherapie, Sportmedizin und biomechanische Untersuchungen.'
    '</p></div>',
    unsafe_allow_html=True,
)

# Analyse-Ablauf
st.markdown('<p style="font-size:0.7rem;font-weight:600;color:#64748b;letter-spacing:0.08em;margin-bottom:1rem;">01 — Analyse-Ablauf</p>', unsafe_allow_html=True)

steps = [
    ("01", "Anamnese", "Patientendaten und Beschwerden erfassen"),
    ("02", "Aufnahme", "Video hochladen (seitlich/frontal)"),
    ("03", "Analyse", "KI extrahiert Gelenkpositionen"),
    ("04", "Bericht", "Ergebnisse und PDF-Export"),
]
st.markdown(
    '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;">' +
    "".join(
        f'<div style="background:rgba(30,41,59,0.6);border:1px solid rgba(51,65,85,0.8);border-radius:12px;padding:1.25rem;">'
        f'<p style="font-size:0.7rem;font-weight:600;color:#0ea5e9;letter-spacing:0.05em;margin-bottom:0.5rem;">{num}</p>'
        f'<p style="font-weight:600;color:#f8fafc;margin-bottom:0.25rem;">{title}</p>'
        f'<p style="font-size:0.875rem;color:#64748b;line-height:1.4;">{desc}</p>'
        f'</div>'
        for num, title, desc in steps
    ) +
    '</div>',
    unsafe_allow_html=True,
)

st.markdown("---")

# System-Status (gleicher Card-Stil wie Analyse-Ablauf)
st.markdown('<p style="font-size:0.7rem;font-weight:600;color:#64748b;letter-spacing:0.08em;margin-bottom:1rem;">02 — System-Status</p>', unsafe_allow_html=True)

processed_dir = Path("data/processed")
if processed_dir.exists():
    keypoint_files = list(processed_dir.glob("*_keypoints.json"))
    anamnese_files = list(processed_dir.glob("anamnese_*.json"))
    latest = max(keypoint_files, key=lambda x: x.stat().st_mtime).stem[:20] if keypoint_files else "—"
    stats = [
        ("Analysen durchgeführt", str(len(keypoint_files))),
        ("Anamnesen gespeichert", str(len(anamnese_files))),
        ("Letzte Analyse", latest),
    ]
    st.markdown(
        '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;">' +
        "".join(
            f'<div style="background:rgba(30,41,59,0.6);border:1px solid rgba(51,65,85,0.8);border-radius:12px;padding:1.25rem;">'
            f'<p style="font-size:0.7rem;font-weight:600;color:#0ea5e9;letter-spacing:0.05em;margin-bottom:0.5rem;">{label}</p>'
            f'<p style="font-weight:600;color:#f8fafc;font-size:1.5rem;">{val}</p>'
            f'</div>'
            for label, val in stats
        ) +
        '</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div style="background:rgba(30,41,59,0.6);border:1px solid rgba(51,65,85,0.8);border-radius:12px;padding:1.5rem;color:#94a3b8;">'
        'Noch keine Analysen durchgeführt.'
        '</div>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# Actions
st.markdown('<p style="font-size:0.7rem;font-weight:600;color:#64748b;letter-spacing:0.08em;margin-bottom:1rem;">03 — Neue Analyse</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    if st.button("Anamnese starten", type="primary", use_container_width=True):
        st.switch_page("pages/0_Anamnese.py")
with col2:
    if st.button("Direkt Video aufnehmen", use_container_width=True):
        st.switch_page("pages/1_Upload.py")

# Recent
if processed_dir.exists() and list(processed_dir.glob("*_keypoints.json")):
    st.markdown("---")
    st.markdown('<p style="font-size:0.7rem;font-weight:600;color:#64748b;letter-spacing:0.08em;margin-bottom:1rem;">Letzte Analysen</p>', unsafe_allow_html=True)
    keypoint_files = sorted(
        processed_dir.glob("*_keypoints.json"),
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )[:5]
    for kf in keypoint_files:
        with open(kf, "r") as f:
            data = json.load(f)
        pid = data.get("metadata", {}).get("patient_id", "Unbekannt")
        date = data.get("metadata", {}).get("processing_date", "")[:10]
        duration = data.get("metadata", {}).get("video_info", {}).get("duration_seconds", 0)
        st.markdown(
            f'<p style="font-size:0.9rem;color:#64748b;margin-bottom:0.5rem;"><span style="color:#cbd5e1;font-weight:500;">{pid}</span> — {date} — {duration:.1f}s</p>',
            unsafe_allow_html=True,
        )

st.markdown("---")
st.markdown('<p style="color:#475569;font-size:0.8rem;">Haile v0.1.0 · GDPR-konform — alle Daten werden lokal verarbeitet</p>', unsafe_allow_html=True)
