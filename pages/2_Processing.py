"""
Haile - Video Processing
========================
Video processing with YOLOv8-pose.
"""

import streamlit as st
import cv2
import numpy as np
import json
from pathlib import Path
from datetime import datetime
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.components.linear_ui import render_linear_css

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

st.set_page_config(
    page_title="Haile - Processing",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

render_linear_css()

st.markdown(
    """
    <h3 class="text-xl font-semibold text-white mb-1">Video Verarbeitung</h3>
    <p class="text-slate-500 text-sm mb-6">KI-gestützte Pose-Estimation</p>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

if "uploaded_file_path" not in st.session_state:
    st.markdown(
        """
        <div class="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 mb-4 text-amber-200">
            Kein Video hochgeladen. Bitte gehen Sie zurück zur Upload-Seite.
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Zurück zum Upload", use_container_width=True):
        st.switch_page("pages/1_Upload.py")
    st.stop()

video_path = st.session_state["uploaded_file_path"]
patient_id = st.session_state.get("patient_id", "UNKNOWN")
patient_notes = st.session_state.get("patient_notes", "")
camera_view = st.session_state.get("camera_view", "sagittal (seitlich)")

st.markdown('<p class="text-lg font-medium text-slate-300 mb-4">Video-Informationen</p>', unsafe_allow_html=True)
col_info1, col_info2 = st.columns([2, 1])
with col_info1:
    st.markdown(
        f"""
        <div class="bg-slate-800/50 border border-slate-700 rounded-xl p-4 mb-4">
            <p class="text-slate-300 text-sm"><span class="text-slate-500">Patient:</span> {patient_id}</p>
            <p class="text-slate-300 text-sm"><span class="text-slate-500">Ansicht:</span> {camera_view}</p>
            <p class="text-slate-300 text-sm"><span class="text-slate-500">Video:</span> {Path(video_path).name}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_info2:
    st.video(video_path)
st.markdown("---")

st.markdown('<p class="text-lg font-medium text-slate-300 mb-4">Verarbeitung</p>', unsafe_allow_html=True)

# Check if already processed
if "processing_complete" in st.session_state and st.session_state.get("processed_file"):
    # Show completion status
    st.markdown(
        """
        <div class="bg-sky-500/10 border border-sky-500/30 rounded-xl p-5 mb-6">
            <p class="text-sky-300 font-medium">✅ Analyse bereits abgeschlossen!</p>
            <p class="text-slate-400 text-sm mt-1">Die Verarbeitung wurde bereits durchgeführt.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Show results from session state
    output_file = Path(st.session_state["processed_file"])
    if output_file.exists():
        with open(output_file, "r") as f:
            output_data = json.load(f)
        keypoints_data = output_data["keypoints"]
        video_info = output_data["metadata"]["video_info"]
        fps = video_info["fps"]
        frame_count = len(keypoints_data)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Frames verarbeitet", frame_count)
        with col2:
            st.metric("Keypoints extrahiert", f"{len(keypoints_data) * 17:,}")
        with col3:
            st.metric("Video-Dauer", f"{frame_count/fps:.1f}s")
        with col4:
            st.metric("Dateigröße", f"{output_file.stat().st_size / 1024:.1f} KB")
        
        st.markdown(
            f'<p class="text-slate-500 text-sm mt-4">Gespeichert: <code class="text-slate-400">{output_file}</code></p>',
            unsafe_allow_html=True,
        )
else:
    # Show start button
    if not st.button("🚀 Verarbeitung starten", type="primary", use_container_width=True):
        st.info("Klicke auf 'Verarbeitung starten', um die KI-Analyse zu beginnen.")
        st.stop()
    
    # Processing
    progress_bar = st.progress(0)
    status_text = st.empty()
    progress_text = st.empty()
    
    status_text.markdown("**Schritt 1 von 4: Video-Analyse**")
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Konnte Video nicht öffnen")
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0
        progress_bar.progress(25)
        progress_text.text(f"Video geladen: {total_frames} Frames | {fps:.1f} FPS | {width}x{height} | {duration:.1f}s")
    except Exception as e:
        st.error(f"Fehler beim Laden des Videos: {e}")
        st.stop()
    
    status_text.markdown("**Schritt 2 von 4: KI-Modell initialisieren**")
    if not YOLO_AVAILABLE:
        st.error("Ultralytics (YOLOv8) ist nicht installiert.")
        st.code("pip install ultralytics", language="bash")
        st.stop()
    try:
        model = YOLO("yolov8n-pose.pt")
        progress_bar.progress(50)
        progress_text.text("YOLOv8n-pose Modell geladen")
    except Exception as e:
        st.error(f"Fehler beim Laden des Modells: {e}")
        st.stop()
    
    status_text.markdown("**Schritt 3 von 4: Pose-Estimation**")
    progress_text.text("Extrahiere Gelenkpositionen aus jedem Frame...")
    keypoints_data = []
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame, verbose=False)
        frame_data = {"frame": frame_count, "timestamp": frame_count / fps, "keypoints": []}
        for result in results:
            if result.keypoints is not None and result.keypoints.xy is not None:
                kp_xy = result.keypoints.xy[0].cpu().numpy()
                kp_conf = result.keypoints.conf[0].cpu().numpy() if result.keypoints.conf is not None else None
                for i, (x, y) in enumerate(kp_xy):
                    conf = kp_conf[i] if kp_conf is not None else 1.0
                    frame_data["keypoints"].append([float(x), float(y), float(conf)])
        keypoints_data.append(frame_data)
        frame_count += 1
        progress = 50 + int((frame_count / total_frames) * 25)
        progress_bar.progress(progress)
        if frame_count % 30 == 0 or frame_count == total_frames:
            progress_text.text(f"Verarbeite: {frame_count}/{total_frames} Frames ({100*frame_count/total_frames:.0f}%)")
    cap.release()
    
    status_text.markdown("**Schritt 4 von 4: Ergebnisse speichern**")
    progress_text.text("Speichere analysierte Daten...")
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"{patient_id}_{timestamp}_keypoints.json"
    output_data = {
        "metadata": {
            "patient_id": patient_id,
            "notes": patient_notes,
            "camera_view": camera_view,
            "source_video": Path(video_path).name,
            "processing_date": datetime.now().isoformat(),
            "video_info": {"fps": fps, "total_frames": total_frames, "resolution": f"{width}x{height}", "duration_seconds": total_frames / fps}
        },
        "keypoints": keypoints_data
    }
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    progress_bar.progress(100)
    status_text.markdown("**Verarbeitung abgeschlossen**")
    
    # Store in session state
    st.session_state["processed_file"] = str(output_file)
    st.session_state["processing_metadata"] = output_data["metadata"]
    st.session_state["processing_complete"] = True
    
    st.markdown("---")
    st.markdown(
        """
        <div class="bg-sky-500/10 border border-sky-500/30 rounded-xl p-5 mb-6">
            <p class="text-sky-300 font-medium">Analyse erfolgreich!</p>
            <p class="text-slate-400 text-sm mt-1">Alle Gelenkpositionen wurden extrahiert und gespeichert.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Frames verarbeitet", frame_count)
    with col2:
        st.metric("Keypoints extrahiert", f"{len(keypoints_data) * 17:,}")
    with col3:
        st.metric("Video-Dauer", f"{frame_count/fps:.1f}s")
    with col4:
        st.metric("Dateigröße", f"{Path(output_file).stat().st_size / 1024:.1f} KB")
    
    st.markdown(
        f'<p class="text-slate-500 text-sm mt-4">Gespeichert: <code class="text-slate-400">{output_file}</code></p>',
        unsafe_allow_html=True,
    )

st.markdown("---")
st.markdown('<p class="text-sm font-medium text-slate-500 mb-4">Navigation</p>', unsafe_allow_html=True)
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("Zurück zum Upload", use_container_width=True):
        st.switch_page("pages/1_Upload.py")
with col_btn2:
    if st.button("Zum Dashboard", type="primary", use_container_width=True):
        st.switch_page("pages/3_Dashboard.py")

st.markdown("---")
st.markdown('<p class="text-slate-600 text-sm">Haile v0.1.0 | GDPR-konform — alle Daten werden lokal verarbeitet</p>', unsafe_allow_html=True)
