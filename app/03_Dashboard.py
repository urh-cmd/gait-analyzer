"""
Gait Analyzer - Page 3: Dashboard
==================================
Visualizes gait analysis results with interactive charts.
"""

import streamlit as st
import json
import numpy as np
from pathlib import Path
from datetime import datetime

# Try to import plotting libraries
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Gait Analyzer - Dashboard",
    page_icon="📊",
    layout="wide"
)

# Header
st.title("📊 Analyse Dashboard")
st.markdown("---")

# Check session state
if "processed_file" not in st.session_state:
    st.warning("⚠️ Keine verarbeiteten Daten vorhanden. Bitte gehen Sie zurück zur Upload-Seite.")
    if st.button("⬅️ Zurück zum Upload"):
        st.switch_page("app/01_Upload.py")
    st.stop()

# Load processed data
processed_file = st.session_state["processed_file"]
metadata = st.session_state.get("processing_metadata", {})

try:
    with open(processed_file, "r") as f:
        data = json.load(f)
except Exception as e:
    st.error(f"❌ Fehler beim Laden der Daten: {e}")
    st.stop()

keypoints_data = data["keypoints"]
metadata = data["metadata"]

# Display metadata
st.markdown("### 📋 Patienteninformationen")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Patienten-ID", metadata.get("patient_id", "N/A"))
with col2:
    st.metric("Kamera-Ansicht", metadata.get("camera_view", "N/A"))
with col3:
    st.metric("Video-Dauer", f"{metadata.get('video_info', {}).get('duration_seconds', 0):.1f}s")

if metadata.get("notes"):
    st.info(f"📝 **Notizen:** {metadata['notes']}")

st.markdown("---")

# Tabs for different views
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Zeitlicher Verlauf",
    "🦴 Keypoint-Visualisierung",
    "📊 Statistiken",
    "💾 Export"
])

# Tab 1: Zeitlicher Verlauf
with tab1:
    st.markdown("### 📈 Keypoints über Zeit")
    
    if not PLOTLY_AVAILABLE:
        st.error("Plotly ist nicht installiert. Bitte installieren: `pip install plotly`")
    else:
        # Extract timestamps
        timestamps = [frame["timestamp"] for frame in keypoints_data]
        
        # Get number of keypoints per frame
        if keypoints_data and keypoints_data[0]["keypoints"]:
            num_keypoints = len(keypoints_data[0]["keypoints"])
            
            # Let user select which keypoint to visualize
            st.markdown("**Wähle Keypoint zur Visualisierung:**")
            keypoint_idx = st.slider(
                "Keypoint Index",
                min_value=0,
                max_value=num_keypoints - 1,
                value=0,
                help="0 = Nase, typischerweise: 0=Nase, 1=Augen, 2=Schultern, etc."
            )
            
            # Extract X and Y coordinates for selected keypoint
            x_coords = []
            y_coords = []
            
            for frame in keypoints_data:
                if keypoint_idx < len(frame["keypoints"]):
                    kp = frame["keypoints"][keypoint_idx]
                    x_coords.append(kp[0])
                    y_coords.append(kp[1])
                else:
                    x_coords.append(None)
                    y_coords.append(None)
            
            # Create plot
            col1, col2 = st.columns(2)
            
            with col1:
                fig_x = go.Figure()
                fig_x.add_trace(go.Scatter(
                    x=timestamps,
                    y=x_coords,
                    mode='lines+markers',
                    name='X-Koordinate',
                    line=dict(color='blue', width=2)
                ))
                fig_x.update_layout(
                    title="X-Koordinate über Zeit",
                    xaxis_title="Zeit (s)",
                    yaxis_title="X-Position (Pixel)",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig_x, use_container_width=True)
            
            with col2:
                fig_y = go.Figure()
                fig_y.add_trace(go.Scatter(
                    x=timestamps,
                    y=y_coords,
                    mode='lines+markers',
                    name='Y-Koordinate',
                    line=dict(color='red', width=2)
                ))
                fig_y.update_layout(
                    title="Y-Koordinate über Zeit",
                    xaxis_title="Zeit (s)",
                    yaxis_title="Y-Position (Pixel)",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig_y, use_container_width=True)
            
            # Combined view
            fig_combined = go.Figure()
            fig_combined.add_trace(go.Scatter(
                x=timestamps,
                y=x_coords,
                mode='lines',
                name='X-Koordinate',
                line=dict(color='blue', width=2)
            ))
            fig_combined.add_trace(go.Scatter(
                x=timestamps,
                y=y_coords,
                mode='lines',
                name='Y-Koordinate',
                line=dict(color='red', width=2)
            ))
            fig_combined.update_layout(
                title="Beide Koordinaten über Zeit",
                xaxis_title="Zeit (s)",
                yaxis_title="Position (Pixel)",
                hovermode='x unified',
                height=400
            )
            st.plotly_chart(fig_combined, use_container_width=True)

# Tab 2: Keypoint-Visualisierung
with tab2:
    st.markdown("### 🦴 Keypoint-Positionen")
    
    if keypoints_data:
        # Let user select a frame
        frame_idx = st.slider(
            "Frame auswählen",
            min_value=0,
            max_value=len(keypoints_data) - 1,
            value=len(keypoints_data) // 2
        )
        
        selected_frame = keypoints_data[frame_idx]
        keypoints = selected_frame["keypoints"]
        
        st.write(f"**Frame {frame_idx}** (Zeit: {selected_frame['timestamp']:.2f}s)")
        st.write(f"Anzahl Keypoints: {len(keypoints)}")
        
        # Display as table
        if keypoints:
            import pandas as pd
            
            kp_df = pd.DataFrame(keypoints, columns=["X", "Y"])
            kp_df["Keypoint Index"] = range(len(keypoints))
            
            st.dataframe(kp_df, use_container_width=True)
            
            # Simple scatter plot
            if PLOTLY_AVAILABLE:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=kp_df["X"],
                    y=kp_df["Y"],
                    mode='markers+text',
                    text=kp_df["Keypoint Index"].astype(str),
                    textposition="top center",
                    marker=dict(size=10, color='blue')
                ))
                fig.update_layout(
                    title=f"Keypoint-Positionen (Frame {frame_idx})",
                    xaxis_title="X (Pixel)",
                    yaxis_title="Y (Pixel)",
                    height=500,
                    yaxis=dict(autorange="reversed")  # Image coordinates
                )
                st.plotly_chart(fig, use_container_width=True)

# Tab 3: Statistiken
with tab3:
    st.markdown("### 📊 Basis-Statistiken")
    
    if keypoints_data:
        # Calculate basic stats
        total_frames = len(keypoints_data)
        fps = metadata.get("video_info", {}).get("fps", 30)
        duration = total_frames / fps
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Gesamt-Frames", total_frames)
        with col2:
            st.metric("FPS", fps)
        with col3:
            st.metric("Dauer", f"{duration:.2f}s")
        with col4:
            avg_kp = np.mean([len(f["keypoints"]) for f in keypoints_data])
            st.metric("Ø Keypoints/Frame", f"{avg_kp:.1f}")
        
        # Keypoint detection rate
        st.markdown("#### Keypoint-Erkennungsrate")
        
        if PLOTLY_AVAILABLE:
            num_keypoints_per_frame = [len(f["keypoints"]) for f in keypoints_data]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(total_frames)),
                y=num_keypoints_per_frame,
                mode='lines',
                name='Keypoints pro Frame',
                line=dict(color='green', width=2)
            ))
            fig.update_layout(
                title="Erkannte Keypoints pro Frame",
                xaxis_title="Frame",
                yaxis_title="Anzahl Keypoints",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)

# Tab 4: Export
with tab4:
    st.markdown("### 💾 Daten exportieren")
    
    st.markdown(f"""
    **Quelldatei:** `{processed_file}`
    
    **Metadaten:**
    - Patient: {metadata.get("patient_id", "N/A")}
    - Verarbeitet am: {metadata.get("processing_date", "N/A")}
    - Video: {metadata.get("source_video", "N/A")}
    """)
    
    # Download button for JSON
    json_str = json.dumps(data, indent=2)
    st.download_button(
        label="📥 JSON-Daten herunterladen",
        data=json_str,
        file_name=f"gait_analysis_{metadata.get("patient_id", "unknown")}.json",
        mime="application/json"
    )
    
    st.info("""
    **Nächste Schritte (in Entwicklung):**
    - Berechnung von Gelenkwinkeln (Knie, Hüfte, Knöchel)
    - Schrittdetektion und -analyse
    - Symmetrie-Analyse (links vs. rechts)
    - PDF-Report Generierung
    - Vergleich mit Referenzdaten
    """)

# Navigation
st.markdown("---")
col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

with col_nav2:
    if st.button("🔄 Neue Analyse starten", type="primary", use_container_width=True):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("app/01_Upload.py")

if st.button("⬅️ Zurück zur Verarbeitung"):
    st.switch_page("app/02_Processing.py")

# Footer
st.markdown("---")
st.markdown(
    "<small>Gait Analyzer v0.1.0 | GDPR-konform - alle Daten werden lokal verarbeitet</small>",
    unsafe_allow_html=True
)
