"""
Gait Analyzer - Page 1: Video Upload
=====================================
Upload interface for gait analysis videos.
"""

import streamlit as st
import os
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Gait Analyzer - Upload",
    page_icon="🚶",
    layout="wide"
)

# Header
st.title("🚶 Gait Analyzer")
st.subheader("Video Upload")
st.markdown("---")

# Instructions
st.info("""
**Anleitung:**
1. Laden Sie ein Video des Patienten hoch (seitliche oder frontale Ansicht)
2. Geben Sie die Patienten-ID ein
3. Optional: Fügen Sie Notizen hinzu (z.B. "rechtes Knie verletzt")
4. Klicken Sie auf "Verarbeiten" um zur nächsten Seite zu gelangen

**Empfehlungen:**
- Video sollte den gesamten Körper zeigen
- Gute Beleuchtung ist wichtig
- Patient sollte normale Gehkleidung tragen
- Video-Länge: 10-30 Sekunden reichen aus
""")

# Upload section
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📹 Video hochladen")
    
    uploaded_file = st.file_uploader(
        "Wählen Sie eine Videodatei",
        type=["mp4", "avi", "mov", "mkv"],
        help="Unterstützte Formate: MP4, AVI, MOV, MKV"
    )
    
    if uploaded_file is not None:
        # Save uploaded file
        upload_dir = Path("data/raw")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"✅ Video gespeichert: `{file_path}`")
        st.video(uploaded_file)

with col2:
    st.markdown("### 📋 Patienteninformationen")
    
    patient_id = st.text_input(
        "Patienten-ID",
        placeholder="z.B. PAT-2026-001",
        help="Eindeutige Kennung für den Patienten"
    )
    
    patient_notes = st.text_area(
        "Notizen (optional)",
        placeholder="z.B. Schmerzen im rechten Knie, Hinkelinken beobachtet...",
        height=150
    )
    
    camera_view = st.selectbox(
        "Kamera-Ansicht",
        options=["sagittal (seitlich)", "frontal (vorne)", "beide"],
        help="Aus welcher Perspektive wurde das Video aufgenommen?"
    )
    
    # Store in session state
    if uploaded_file is not None:
        st.session_state["uploaded_file_path"] = str(file_path)
        st.session_state["uploaded_file_name"] = uploaded_file.name
    st.session_state["patient_id"] = patient_id
    st.session_state["patient_notes"] = patient_notes
    st.session_state["camera_view"] = camera_view

# Navigation
st.markdown("---")
col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

with col_nav2:
    # Check if file is uploaded
    can_proceed = "uploaded_file_path" in st.session_state
    
    if st.button(
        "➡️ Zur Verarbeitung",
        type="primary",
        disabled=not can_proceed,
        use_container_width=True
    ):
        st.switch_page("app/02_Processing.py")

# Footer
st.markdown("---")
st.markdown(
    "<small>Gait Analyzer v0.1.0 | GDPR-konform - alle Daten werden lokal verarbeitet</small>",
    unsafe_allow_html=True
)
