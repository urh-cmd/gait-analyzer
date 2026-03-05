"""
Gait Analyzer - Dashboard
=========================
Keypoint-Analyse und Statistiken. Kein Video-Player – nur die Analyse-Ergebnisse.
"""

import streamlit as st
import json
import numpy as np
from pathlib import Path
from datetime import datetime

try:
    import plotly.graph_objects as go
    import pandas as pd
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# COCO Keypoint-Namen
KEYPOINT_NAMES = [
    "Nase", "L Auge", "R Auge", "L Ohr", "R Ohr",
    "L Schulter", "R Schulter", "L Ellbogen", "R Ellbogen",
    "L Handgelenk", "R Handgelenk", "L Hüfte", "R Hüfte",
    "L Knie", "R Knie", "L Knöchel", "R Knöchel",
]

st.set_page_config(page_title="Gait Analyzer - Dashboard", page_icon="📊", layout="wide")
st.title("📊 Gait Analyzer – Keypoint-Analyse & Statistiken")
st.markdown("---")

if "processed_file" not in st.session_state:
    st.warning("⚠️ Keine Daten. Bitte zuerst Video verarbeiten!")
    if st.button("⬅️ Zum Upload"):
        st.switch_page("Home.py")
    st.stop()

# Load data
with open(st.session_state["processed_file"], "r") as f:
    data = json.load(f)

keypoints_data = data["keypoints"]
metadata = data["metadata"]
total_frames = len(keypoints_data)
fps = metadata.get("video_info", {}).get("fps", 30)
duration = metadata.get("video_info", {}).get("duration_seconds", total_frames / fps)

# Header: Infos
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Patient", metadata.get("patient_id", "N/A"))
with col2:
    st.metric("Dauer", f"{duration:.1f}s")
with col3:
    st.metric("Frames", total_frames)
with col4:
    st.metric("FPS", fps)
with col5:
    avg_kp = np.mean([len(f["keypoints"]) for f in keypoints_data]) if keypoints_data else 0
    st.metric("Ø Keypoints/Frame", f"{avg_kp:.1f}")

if metadata.get("notes"):
    st.info(f"📝 **Notizen:** {metadata['notes']}")

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Keypoint-Verlauf",
    "🦴 Pose pro Frame",
    "📊 Statistiken",
    "📋 Analyse",
    "💾 Export",
])

# Tab 1: Keypoint-Analyse über Zeit
with tab1:
    st.markdown("### 📈 Keypoints über Zeit")

    if not PLOTLY_AVAILABLE:
        st.error("Plotly fehlt: `pip install plotly`")
    elif not keypoints_data or not keypoints_data[0].get("keypoints"):
        st.warning("Keine Keypoint-Daten vorhanden.")
    else:
        timestamps = [f["timestamp"] for f in keypoints_data]
        num_kp = len(keypoints_data[0]["keypoints"])

        kp_options = [f"{i}: {KEYPOINT_NAMES[i]}" if i < len(KEYPOINT_NAMES) else str(i)
                      for i in range(num_kp)]
        kp_choice = st.selectbox(
            "Keypoint auswählen",
            range(num_kp),
            format_func=lambda i: kp_options[i],
        )

        x_vals = []
        y_vals = []
        conf_vals = []
        for frame in keypoints_data:
            kps = frame.get("keypoints", [])
            if kp_choice < len(kps):
                kp = kps[kp_choice]
                x_vals.append(kp[0] if len(kp) > 0 else None)
                y_vals.append(kp[1] if len(kp) > 1 else None)
                conf_vals.append(kp[2] if len(kp) > 2 else None)
            else:
                x_vals.append(None)
                y_vals.append(None)
                conf_vals.append(None)

        col1, col2 = st.columns(2)
        with col1:
            fig_x = go.Figure()
            fig_x.add_trace(go.Scatter(x=timestamps, y=x_vals, mode="lines", name="X", line=dict(color="#1f77b4", width=2)))
            fig_x.update_layout(title="X-Koordinate", xaxis_title="Zeit (s)", yaxis_title="Pixel", height=350)
            st.plotly_chart(fig_x, use_container_width=True)
        with col2:
            fig_y = go.Figure()
            fig_y.add_trace(go.Scatter(x=timestamps, y=y_vals, mode="lines", name="Y", line=dict(color="#d62728", width=2)))
            fig_y.update_layout(title="Y-Koordinate", xaxis_title="Zeit (s)", yaxis_title="Pixel", height=350)
            st.plotly_chart(fig_y, use_container_width=True)

        if any(c is not None for c in conf_vals):
            fig_conf = go.Figure()
            fig_conf.add_trace(go.Scatter(x=timestamps, y=conf_vals, mode="lines", name="Confidence", line=dict(color="#2ca02c", width=2)))
            fig_conf.update_layout(title="Confidence über Zeit", xaxis_title="Zeit (s)", yaxis_title="Confidence", height=300)
            st.plotly_chart(fig_conf, use_container_width=True)

# Tab 2: Pose als abspielbares Video
with tab2:
    st.markdown("### 🦴 Video mit Pose-Overlay")

    source_video = metadata.get("source_video", "")
    video_path = Path("data/raw") / source_video
    if not video_path.exists():
        video_path = Path.cwd() / "data/raw" / source_video

    if not video_path.exists():
        st.info("Video nicht gefunden – zeige Keypoint-Positionen als Diagramm.")
        frame_idx = st.slider("Frame", 0, max(0, total_frames - 1), len(keypoints_data) // 2)
        if frame_idx < len(keypoints_data):
            kps = keypoints_data[frame_idx].get("keypoints", [])
            if kps and PLOTLY_AVAILABLE:
                df = pd.DataFrame(kps, columns=["X", "Y", "Conf"]) if len(kps[0]) >= 3 else pd.DataFrame(kps, columns=["X", "Y"])
                df["Keypoint"] = [KEYPOINT_NAMES[i] if i < len(KEYPOINT_NAMES) else str(i) for i in range(len(df))]
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df["X"], y=df["Y"], mode="markers+text", text=df["Keypoint"],
                    textposition="top center", marker=dict(size=10, color="blue")
                ))
                fig.update_layout(
                    title=f"Frame {frame_idx} – Keypoints",
                    xaxis_title="X", yaxis_title="Y",
                    yaxis=dict(autorange="reversed"),
                    height=500,
                )
                st.plotly_chart(fig, use_container_width=True)
            if kps:
                cols = ["X", "Y", "Confidence"] if len(kps[0]) >= 3 else ["X", "Y"]
                st.dataframe(pd.DataFrame(kps, columns=cols), use_container_width=True)
    else:
        try:
            from app.components.video_player import create_pose_overlay_video
        except ImportError:
            # Fallback falls Modul-Cache veraltet
            import cv2
            from app.components.video_player import draw_pose_on_frame

            def create_pose_overlay_video(video_path, keypoints_data, output_path, min_confidence=0.5):
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    return None
                fps = cap.get(cv2.CAP_PROP_FPS) or 30
                w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fourcc = cv2.VideoWriter_fourcc(*"avc1")
                out = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))
                if not out.isOpened():
                    out = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
                if not out.isOpened():
                    cap.release()
                    return None
                idx = 0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    kps = keypoints_data[idx]["keypoints"] if idx < len(keypoints_data) else []
                    out.write(draw_pose_on_frame(frame, kps, min_confidence))
                    idx += 1
                cap.release()
                out.release()
                return output_path

        min_conf = st.slider("Min. Confidence für Keypoints", 0.0, 1.0, 0.5, 0.1, key="conf_tab2")
        
        # Unique video ID based on current analysis + confidence
        pid = metadata.get("patient_id", "unknown").replace("/", "_").replace("\\", "_")
        source_vid = metadata.get("source_video", "unknown").replace(".", "_")
        timestamp = metadata.get("processing_date", "")[:10].replace("-", "")
        conf_suffix = str(int(min_conf * 10))
        
        out_dir = Path("data/processed")
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Include timestamp to ensure uniqueness per analysis
        pose_video_path = out_dir / f"pose_{pid}_{source_vid}_{timestamp}_c{conf_suffix}.mp4"

        if pose_video_path.exists():
            # Show existing video for this configuration
            abs_path = pose_video_path.resolve()
            with open(abs_path, "rb") as f:
                video_bytes = f.read()
            st.video(video_bytes, format="video/mp4")
            st.download_button("📥 Video herunterladen", video_bytes, pose_video_path.name, "video/mp4")
            st.caption(f"Video mit Pose-Skeleton (Confidence: {min_conf})")
            
            # Option to re-render
            if st.button("🔄 Neu rendern (bei Problemen)", key="rerender_btn"):
                pose_video_path.unlink(missing_ok=True)
                st.rerun()
        else:
            if st.button("▶️ Video mit Pose-Overlay erstellen", type="primary"):
                with st.spinner("Rendere Video …"):
                    result = create_pose_overlay_video(
                        str(video_path), keypoints_data, str(pose_video_path), min_conf
                    )
                if result:
                    st.success("Video erstellt!")
                    st.rerun()
                else:
                    st.error("Video konnte nicht erstellt werden.")
            st.info("Klicke auf **Video mit Pose-Overlay erstellen**, um ein abspielbares Video zu generieren.")

# Tab 3: Statistiken
with tab3:
    st.markdown("### 📊 Statistiken")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Frames gesamt", total_frames)
    with col2:
        st.metric("FPS", fps)
    with col3:
        st.metric("Dauer", f"{duration:.2f}s")
    with col4:
        kp_per_frame = [len(f["keypoints"]) for f in keypoints_data]
        st.metric("Ø Keypoints/Frame", f"{np.mean(kp_per_frame):.1f}")
    with col5:
        st.metric("Max Keypoints", max(kp_per_frame) if kp_per_frame else 0)

    st.markdown("#### Keypoint-Erkennungsrate pro Frame")
    if PLOTLY_AVAILABLE and keypoints_data:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(total_frames)),
            y=kp_per_frame,
            mode="lines",
            line=dict(color="#17becf", width=2),
        ))
        fig.update_layout(
            xaxis_title="Frame",
            yaxis_title="Anzahl Keypoints",
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Confidence-Statistik
    if keypoints_data:
        all_conf = []
        for f in keypoints_data:
            for kp in f.get("keypoints", []):
                if len(kp) >= 3:
                    all_conf.append(kp[2])
        if all_conf:
            st.markdown("#### Confidence-Verteilung")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Ø Confidence", f"{np.mean(all_conf):.2f}")
            with c2:
                st.metric("Min", f"{np.min(all_conf):.2f}")
            with c3:
                st.metric("Max", f"{np.max(all_conf):.2f}")

# Tab 4: Export
with tab4:
    st.markdown("### 💾 Export")
    pid = metadata.get("patient_id", "data").replace("/", "_").replace("\\", "_")
    json_str = json.dumps(data, indent=2)
    st.download_button("📥 JSON herunterladen", json_str, f"gait_{pid}.json", "application/json")

# Tab 4: Analyse
with tab4:
    st.markdown("### 📋 Ganganalyse")
    st.info("Automatische Berechnung von Gait-Metriken")
    
    # Import analysis engine
    try:
        from src.gait_analysis import analyze_gait, generate_clinical_summary
        from src.pdf_report import create_gait_report
        
        # Calculate metrics
        with st.spinner("Analysiere Gangmuster..."):
            metrics = analyze_gait(
                keypoints_data, 
                fps=fps,
                duration_seconds=duration,
                pixel_to_cm=1.0  # TODO: Calibration
            )
        
        # Display summary
        st.markdown("#### 📝 Zusammenfassung")
        summary = generate_clinical_summary(metrics)
        st.markdown(summary)
        
        # Key metrics in columns
        st.markdown("#### 📊 Wichtige Kennzahlen")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Schritte", metrics.step_count)
        with c2:
            st.metric("Cadenz", f"{metrics.cadence:.1f}/min")
        with c3:
            st.metric("Symmetrie", f"{metrics.symmetry_index:.1f}%")
        with c4:
            st.metric("L/R Verhältnis", f"{metrics.left_right_ratio:.2f}")
        
        # Asymmetry warning
        if metrics.has_asymmetry:
            st.error("⚠️ **Asymmetrie erkannt!** Ein Symmetrie-Index >10% deutet auf ein auffälliges Gangbild hin.")
        else:
            st.success("✅ **Symmetrischer Gang** - Keine signifikante Asymmetrie festgestellt.")
        
        # Detailed metrics table
        st.markdown("#### 📈 Detaillierte Metriken")
        
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("**Zeitliche Parameter:**")
            st.write(f"• Schrittzeit links: {metrics.step_time_left:.2f}s")
            st.write(f"• Schrittzeit rechts: {metrics.step_time_right:.2f}s")
            st.write(f"• Swing Phase: {metrics.swing_phase_percent:.1f}%")
            st.write(f"• Stance Phase: {metrics.stance_phase_percent:.1f}%")
        
        with col_right:
            st.markdown("**Räumliche Parameter:**")
            st.write(f"• Schrittlänge links: {metrics.step_length_left:.1f} cm")
            st.write(f"• Schrittlänge rechts: {metrics.step_length_right:.1f} cm")
            st.write(f"• Maximale Knieflexion: {metrics.max_knee_flexion:.1f}°")
        
        # PDF Report Generation
        st.markdown("---")
        st.markdown("#### 📄 PDF-Report erstellen")
        
        if st.button("📄 Professionellen Bericht erstellen", type="primary"):
            with st.spinner("Generiere PDF-Bericht..."):
                try:
                    output_dir = Path("data/processed")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    patient_data = {
                        'patient_id': metadata.get('patient_id', 'Unknown'),
                        'duration_seconds': duration,
                        'total_frames': total_frames,
                        'notes': metadata.get('notes', '')
                    }
                    
                    report_path = output_dir / f"gait_report_{metadata.get('patient_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    
                    create_gait_report(
                        str(report_path),
                        patient_data,
                        metrics,
                        keypoints_data
                    )
                    
                    # Offer download
                    with open(report_path, "rb") as f:
                        pdf_bytes = f.read()
                    
                    st.download_button(
                        "📥 PDF herunterladen",
                        pdf_bytes,
                        report_path.name,
                        "application/pdf"
                    )
                    
                    st.success(f"✅ Bericht erstellt: {report_path.name}")
                    
                except Exception as e:
                    st.error(f"❌ Fehler bei PDF-Erstellung: {e}")
        
    except Exception as e:
        st.error(f"Fehler bei der Analyse: {e}")
        st.info("Stelle sicher, dass alle Abhängigkeiten installiert sind.")

# Navigation
st.markdown("---")
if st.button("🔄 Neue Analyse", type="primary"):
    # Lösche ALLE session state variables
    keys_to_delete = [k for k in st.session_state.keys()]
    for k in keys_to_delete:
        del st.session_state[k]
    # Clear any cached data
    st.cache_data.clear()
    st.cache_resource.clear()
    st.switch_page("Home.py")
if st.button("⬅️ Zurück zur Verarbeitung"):
    st.switch_page("pages/1_⚙️_Verarbeitung.py")
