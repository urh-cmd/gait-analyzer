"""
Gait Analyzer - Page 2: Video Processing
=========================================
Processes uploaded video with YOLOv8-pose and extracts keypoints.
"""

import streamlit as st
import cv2
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# Try to import ultralytics, handle if not installed
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Gait Analyzer - Processing",
    page_icon="⚙️",
    layout="wide"
)

# Header
st.title("⚙️ Video Verarbeitung")
st.markdown("---")

# Check session state
if "uploaded_file_path" not in st.session_state:
    st.warning("⚠️ Kein Video hochgeladen. Bitte gehen Sie zurück zur Upload-Seite.")
    if st.button("⬅️ Zurück zum Upload"):
        st.switch_page("app/01_Upload.py")
    st.stop()

# Get session data
video_path = st.session_state["uploaded_file_path"]
patient_id = st.session_state.get("patient_id", "UNKNOWN")
patient_notes = st.session_state.get("patient_notes", "")
camera_view = st.session_state.get("camera_view", "sagittal (seitlich)")

# Display info
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown(f"**Video:** `{Path(video_path).name}`")
    st.markdown(f"**Patienten-ID:** {patient_id}")
    st.markdown(f"**Ansicht:** {camera_view}")
with col2:
    st.video(video_path)

# Processing section
st.markdown("---")
st.markdown("### 🔬 Verarbeitungsschritte")

# Create progress container
progress_container = st.container()
progress_bar = progress_container.progress(0)
status_text = progress_container.empty()
log_container = progress_container.empty()

# Processing log
processing_log = []

def log_message(msg):
    processing_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    log_container.code("\n".join(processing_log), language="text")

# Step 1: Load video
status_text.text("Schritt 1/4: Video wird geladen...")
log_message("Lade Video...")

try:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Konnte Video nicht öffnen")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    log_message(f"Video geladen: {total_frames} Frames @ {fps:.1f} FPS, {width}x{height}")
    progress_bar.progress(0.25)
except Exception as e:
    st.error(f"❌ Fehler beim Laden des Videos: {e}")
    log_message(f"FEHLER: {e}")
    st.stop()

# Step 2: Initialize YOLOv8-pose
status_text.text("Schritt 2/4: Pose-Modell wird initialisiert...")
log_message("Initialisiere YOLOv8-pose...")

if not YOLO_AVAILABLE:
    st.error("❌ Ultralytics (YOLOv8) ist nicht installiert!")
    st.code("pip install ultralytics", language="bash")
    log_message("FEHLER: Ultralytics nicht installiert")
    st.stop()

try:
    model = YOLO("yolov8n-pose.pt")  # Nano model for speed
    log_message("YOLOv8n-pose Modell geladen")
    progress_bar.progress(0.50)
except Exception as e:
    st.error(f"❌ Fehler beim Laden des Modells: {e}")
    log_message(f"FEHLER: {e}")
    st.stop()

# Step 3: Process frames
status_text.text("Schritt 3/4: Pose-Estimation läuft...")
log_message("Starte Pose-Estimation...")

keypoints_data = []
frame_count = 0

# Process every frame (can be optimized later)
with tqdm(total=total_frames, desc="Verarbeite Frames") as pbar:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Run YOLOv8-pose
        results = model(frame, verbose=False)
        
        # Extract keypoints
        frame_data = {
            "frame": frame_count,
            "timestamp": frame_count / fps,
            "keypoints": []
        }
        
        for result in results:
            if result.keypoints is not None:
                for kp in result.keypoints.xy.cpu().numpy():
                    frame_data["keypoints"].append(kp.tolist())
        
        keypoints_data.append(frame_data)
        frame_count += 1
        pbar.update(1)
        
        # Update progress every 10 frames
        if frame_count % 10 == 0:
            progress = 0.50 + (frame_count / total_frames) * 0.25
            progress_bar.progress(progress)
            log_message(f"Frame {frame_count}/{total_frames} verarbeitet")

cap.release()
log_message(f"Pose-Estimation abgeschlossen: {frame_count} Frames")
progress_bar.progress(0.75)

# Step 4: Save results
status_text.text("Schritt 4/4: Ergebnisse werden gespeichert...")
log_message("Speichere Keypoint-Daten...")

# Create output directory
output_dir = Path("data/processed")
output_dir.mkdir(exist_ok=True)

# Generate output filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = output_dir / f"{patient_id}_{timestamp}_keypoints.json"

# Save metadata + keypoints
output_data = {
    "metadata": {
        "patient_id": patient_id,
        "notes": patient_notes,
        "camera_view": camera_view,
        "source_video": Path(video_path).name,
        "processing_date": datetime.now().isoformat(),
        "video_info": {
            "fps": fps,
            "total_frames": total_frames,
            "resolution": f"{width}x{height}",
            "duration_seconds": total_frames / fps
        }
    },
    "keypoints": keypoints_data
}

with open(output_file, "w") as f:
    json.dump(output_data, f, indent=2)

log_message(f"Gespeichert: {output_file}")
progress_bar.progress(1.0)
status_text.text("✅ Verarbeitung abgeschlossen!")

# Store for next page
st.session_state["processed_file"] = str(output_file)
st.session_state["processing_metadata"] = output_data["metadata"]

# Success message
st.success(f"✅ Verarbeitung erfolgreich abgeschlossen!")
st.markdown(f"""
**Zusammenfassung:**
- {frame_count} Frames verarbeitet
- {len(keypoints_data)} Keypoint-Datensätze extrahiert
- Gespeichert in: `{output_file}`
""")

# Navigation
st.markdown("---")
col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

with col_nav2:
    if st.button("➡️ Zum Dashboard", type="primary", use_container_width=True):
        st.switch_page("app/03_Dashboard.py")

if st.button("⬅️ Zurück zum Upload"):
    st.switch_page("app/01_Upload.py")

# Footer
st.markdown("---")
st.markdown(
    "<small>Gait Analyzer v0.1.0 | GDPR-konform - alle Daten werden lokal verarbeitet</small>",
    unsafe_allow_html=True
)
