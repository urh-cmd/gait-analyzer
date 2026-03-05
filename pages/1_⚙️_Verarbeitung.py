"""
Gait Analyzer - Page 1: Video Processing
=========================================
Processes uploaded video with YOLOv8-pose and extracts keypoints.
"""

import streamlit as st
import cv2
import numpy as np
import json
import time
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
    st.warning("⚠️ Kein Video hochgeladen. Bitte gehen Sie zurück zur Startseite.")
    if st.button("⬅️ Zurück zum Upload"):
        st.switch_page("Home.py")
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
log_message(f"⏱️ Geschätzte Zeit: ~{total_frames/30:.0f} Sekunden ({total_frames} Frames @ 30 FPS)")

keypoints_data = []
frame_count = 0
start_time = time.time()

# Process every frame with frequent updates
update_interval = max(1, total_frames // 100)  # Update ~100 times during processing

for frame_idx in range(total_frames):
    ret, frame = cap.read()
    if not ret:
        break
    
    # Run YOLOv8-pose
    results = model(frame, verbose=False)
    
    # Extract keypoints
    frame_data = {
        "frame": frame_idx,
        "timestamp": frame_idx / fps,
        "keypoints": []
    }
    
    for result in results:
        if result.keypoints is not None:
            xy = result.keypoints.xy.cpu().numpy()
            
            # Handle different array shapes
            if xy.ndim == 1:
                xy = xy.reshape(1, -1)
            elif xy.ndim == 3:
                xy = xy.reshape(-1, xy.shape[-1])
            
            conf = result.keypoints.conf.cpu().numpy().flatten() if hasattr(result.keypoints, 'conf') and result.keypoints.conf is not None else None
            
            for i in range(len(xy)):
                kp = xy[i]
                if len(kp) >= 2:
                    x, y = float(kp[0]), float(kp[1])
                    c = float(conf[i]) if conf is not None and i < len(conf) else 1.0
                    frame_data["keypoints"].append([x, y, c])
    
    keypoints_data.append(frame_data)
    frame_count += 1
    
    # Update UI frequently
    if frame_count % update_interval == 0 or frame_count == total_frames:
        progress = 0.50 + (frame_count / total_frames) * 0.25
        progress_bar.progress(min(0.74, progress))
        
        elapsed = time.time() - start_time
        fps_processing = frame_count / elapsed if elapsed > 0 else 0
        remaining = (total_frames - frame_count) / fps_processing if fps_processing > 0 else 0
        
        status_text.text(f"Frame {frame_count}/{total_frames} ({fps_processing:.1f} FPS) | Noch ~{remaining:.0f}s")
        log_message(f"Frame {frame_count}/{total_frames} - {fps_processing:.1f} FPS")

cap.release()
elapsed_total = time.time() - start_time
log_message(f"✅ Pose-Estimation abgeschlossen: {frame_count} Frames in {elapsed_total:.1f}s ({frame_count/elapsed_total:.1f} FPS)")
progress_bar.progress(0.75)

cap.release()
log_message(f"Pose-Estimation abgeschlossen: {frame_count} Frames")
progress_bar.progress(0.70)

# Step 4: Apply One Euro Filter for temporal smoothing (WEEK 4)
status_text.text("Schritt 4/5: One Euro Filter wird angewendet...")
log_message("Wende One Euro Filter an (temporal smoothing)...")

try:
    from src.one_euro_filter import apply_one_euro_filter
    keypoints_data_filtered = apply_one_euro_filter(keypoints_data, fps=fps, mincutoff=1.0, beta=0.007)
    log_message(f"One Euro Filter angewendet: {len(keypoints_data_filtered)} Frames geglättet")
    
    # Store both raw and filtered data
    output_keypoints_data = keypoints_data_filtered
    filter_applied = True
except Exception as e:
    log_message(f"WARNUNG: One Euro Filter fehlgeschlagen: {e}")
    output_keypoints_data = keypoints_data
    filter_applied = False

progress_bar.progress(0.85)

# Step 5: Save results
status_text.text("Schritt 5/5: Ergebnisse werden gespeichert...")
log_message("Speichere Keypoint-Daten...")

# Create output directory
output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

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

# Clear cache before navigation to prevent old data issues
st.cache_data.clear()

col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

with col_nav2:
    if st.button("➡️ Zum Dashboard", type="primary", use_container_width=True, key="to_dashboard_btn"):
        st.switch_page("pages/2_📊_Dashboard.py")

if st.button("⬅️ Zurück zum Upload", key="back_to_upload"):
    # Clear all session state on back
    for k in list(st.session_state.keys()):
        if k not in ['processed_file', 'processing_metadata']:
            del st.session_state[k]
    st.switch_page("Home.py")

# Footer
st.markdown("---")
st.markdown(
    "<small>Gait Analyzer v0.1.0 | GDPR-konform - alle Daten werden lokal verarbeitet</small>",
    unsafe_allow_html=True
)
