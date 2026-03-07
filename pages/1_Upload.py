"""
Haile - Video Upload
====================
Video upload interface.
"""

import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.components.linear_ui import render_linear_css

st.set_page_config(
    page_title="Haile - Upload",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

render_linear_css()

st.markdown(
    """
    <h3 class="text-xl font-semibold text-white mb-1">Video Upload</h3>
    <p class="text-slate-500 text-sm mb-6">Ganganalyse-Video hochladen</p>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

st.markdown(
    """
    <div class="bg-slate-800/50 border border-slate-700 rounded-xl p-4 border-l-4 border-l-sky-500 mb-6">
        <p class="text-slate-300 text-sm font-medium mb-2">Tipps für optimale Ergebnisse</p>
        <ul class="text-slate-400 text-sm space-y-1 list-disc list-inside">
            <li>Perspektive: Seitliche oder frontale Ansicht des gesamten Körpers</li>
            <li>Beleuchtung: Gleichmäßig und hell, ohne starke Schatten</li>
            <li>Kleidung: Eng anliegend für bessere Gelenkerkennung</li>
            <li>Dauer: 10–30 Sekunden Gehzeit</li>
            <li>Hintergrund: Möglichst einheitlich und kontrastreich</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

col1, col2 = st.columns([2, 1])
with col1:
    st.markdown('<p class="text-lg font-medium text-slate-300 mb-4">Video auswählen</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Videodatei hochladen",
        type=["mp4", "avi", "mov", "mkv"],
        label_visibility="collapsed"
    )
    if uploaded_file is not None:
        upload_dir = Path("data/raw")
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"Video gespeichert: {file_path.name}")
        st.video(uploaded_file)

with col2:
    st.markdown('<p class="text-lg font-medium text-slate-300 mb-4">Aufnahme-Details</p>', unsafe_allow_html=True)
    patient_id = st.text_input(
        "Patienten-ID",
        placeholder="z.B. PAT-2026-001",
        help="Eindeutige Kennung für den Patienten"
    )
    patient_notes = st.text_area(
        "Notizen",
        placeholder="z.B. rechtes Knie verletzt...",
        height=100
    )
    camera_view = st.selectbox(
        "Kamera-Perspektive",
        options=["sagittal (seitlich)", "frontal (vorne)", "beide"],
        help="Aufnahmeperspektive"
    )
    if uploaded_file is not None:
        st.session_state["uploaded_file_path"] = str(file_path)
        st.session_state["uploaded_file_name"] = uploaded_file.name
    st.session_state["patient_id"] = patient_id
    st.session_state["patient_notes"] = patient_notes
    st.session_state["camera_view"] = camera_view

st.markdown("---")
st.markdown('<p class="text-sm font-medium text-slate-500 mb-4">Navigation</p>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    if st.button("Zurück", use_container_width=True):
        st.switch_page("Home.py")
with col2:
    can_proceed = "uploaded_file_path" in st.session_state
    if st.button(
        "Weiter zur Verarbeitung",
        type="primary",
        disabled=not can_proceed,
        use_container_width=True
    ):
        st.switch_page("pages/2_Processing.py")

st.markdown("---")
st.markdown('<p class="text-slate-600 text-sm">Haile v0.1.0 | GDPR-konform — alle Daten werden lokal verarbeitet</p>', unsafe_allow_html=True)
