"""
Gait Analyzer - Video Player Component
========================================
HTML5 Video Player with frame-accurate pose overlay.
Video mit Pose-Skeleton direkt überlagert + zuverlässige Player-Buttons.
"""

import streamlit as st
import base64
import json
from pathlib import Path

# YOLOv8/COCO Skeleton: (idx1, idx2) für Linien
SKELETON = [
    (0, 1), (0, 2), (1, 3), (2, 4), (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
    (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
]

def get_video_base64(video_path):
    """Load video file and return as base64 encoded string."""
    try:
        with open(video_path, "rb") as f:
            video_bytes = f.read()
        return base64.b64encode(video_bytes).decode()
    except Exception as e:
        return None

def render_video_player(video_path, keypoints_data, total_frames, fps):
    """
    Render HTML5 video player with custom controls.
    Returns current frame index based on time.
    """
    
    # Get video as base64
    video_b64 = get_video_base64(video_path)
    
    if not video_b64:
        st.error(f"Konnte Video nicht laden: {video_path}")
        return 0
    
    # Determine video MIME type
    video_ext = Path(video_path).suffix.lower()
    mime_types = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".ogg": "video/ogg",
        ".mov": "video/quicktime",
        ".avi": "video/x-msvideo"
    }
    mime_type = mime_types.get(video_ext, "video/mp4")
    
    # HTML5 Video Player with JavaScript for frame tracking
    st.markdown(f"""
    <div style="text-align: center; margin: 20px 0;">
        <video id="gaitVideo" controls style="max-width: 100%; border-radius: 8px;">
            <source src="data:{mime_type};base64,{video_b64}" type="{mime_type}">
            Your browser does not support the video tag.
        </video>
        
        <div style="margin-top: 15px;">
            <input type="range" id="frameSlider" min="0" max="{total_frames - 1}" value="0" 
                   style="width: 100%; margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; color: #666; font-size: 12px;">
                <span>Frame: <b id="frameDisplay">0</b> / {total_frames}</span>
                <span>Zeit: <b id="timeDisplay">0.00</b> s</span>
            </div>
        </div>
        
        <div style="margin-top: 10px;">
            <button id="playPauseBtn" style="padding: 8px 20px; font-size: 16px; cursor: pointer;">▶️ Abspielen</button>
            <button id="rewindBtn" style="padding: 8px 15px; font-size: 14px; cursor: pointer; margin-left: 5px;">⏮️ -10</button>
            <button id="forwardBtn" style="padding: 8px 15px; font-size: 14px; cursor: pointer; margin-left: 5px;">⏭️ +10</button>
            <button id="slowerBtn" style="padding: 8px 15px; font-size: 14px; cursor: pointer; margin-left: 5px;">🐌 0.5x</button>
            <button id="fasterBtn" style="padding: 8px 15px; font-size: 14px; cursor: pointer; margin-left: 5px;">🚀 2x</button>
        </div>
        
        <script>
            // Store in window for Streamlit to access
            window.gaitVideoState = {{
                currentFrame: 0,
                isPlaying: false,
                playbackRate: 1.0
            }};
            
            const video = document.getElementById('gaitVideo');
            const slider = document.getElementById('frameSlider');
            const frameDisplay = document.getElementById('frameDisplay');
            const timeDisplay = document.getElementById('timeDisplay');
            const playPauseBtn = document.getElementById('playPauseBtn');
            const rewindBtn = document.getElementById('rewindBtn');
            const forwardBtn = document.getElementById('forwardBtn');
            const slowerBtn = document.getElementById('slowerBtn');
            const fasterBtn = document.getElementById('fasterBtn');
            
            const totalFrames = {total_frames};
            const fps = {fps};
            
            // Update frame display on time update
            video.addEventListener('timeupdate', () => {{
                const currentTime = video.currentTime;
                const currentFrame = Math.floor(currentTime * fps);
                window.gaitVideoState.currentFrame = currentFrame;
                
                slider.value = currentFrame;
                frameDisplay.textContent = currentFrame;
                timeDisplay.textContent = currentTime.toFixed(2);
                
                // Send to Streamlit
                if (window.parent && window.parent.postMessage) {{
                    window.parent.postMessage({{
                        type: 'gait_frame_update',
                        frame: currentFrame
                    }}, '*');
                }}
            }});
            
            // Update video time when slider changes
            slider.addEventListener('input', () => {{
                const frame = parseInt(slider.value);
                const time = frame / fps;
                video.currentTime = time;
                frameDisplay.textContent = frame;
                timeDisplay.textContent = time.toFixed(2);
            }});
            
            // Play/Pause button
            playPauseBtn.addEventListener('click', () => {{
                if (video.paused) {{
                    video.play();
                    playPauseBtn.textContent = '⏸️ Pause';
                    window.gaitVideoState.isPlaying = true;
                }} else {{
                    video.pause();
                    playPauseBtn.textContent = '▶️ Abspielen';
                    window.gaitVideoState.isPlaying = false;
                }}
            }});
            
            // Rewind button
            rewindBtn.addEventListener('click', () => {{
                const newFrame = Math.max(0, window.gaitVideoState.currentFrame - 10);
                video.currentTime = newFrame / fps;
            }});
            
            // Forward button
            forwardBtn.addEventListener('click', () => {{
                const newFrame = Math.min(totalFrames - 1, window.gaitVideoState.currentFrame + 10);
                video.currentTime = newFrame / fps;
            }});
            
            // Slower playback
            slowerBtn.addEventListener('click', () => {{
                video.playbackRate = Math.max(0.25, video.playbackRate / 2);
                window.gaitVideoState.playbackRate = video.playbackRate;
                slowerBtn.textContent = `🐌 ${video.playbackRate.toFixed(2)}x`;
            }});
            
            // Faster playback
            fasterBtn.addEventListener('click', () => {{
                video.playbackRate = Math.min(4, video.playbackRate * 2);
                window.gaitVideoState.playbackRate = video.playbackRate;
                fasterBtn.textContent = `🚀 ${video.playbackRate.toFixed(2)}x`;
            }});
            
            // Video ended
            video.addEventListener('ended', () => {{
                playPauseBtn.textContent = '▶️ Abspielen';
                window.gaitVideoState.isPlaying = false;
            }});
        </script>
    </div>
    """, unsafe_allow_html=True)
    
    # Try to get current frame from session state (updated via JavaScript)
    if "video_current_frame" not in st.session_state:
        st.session_state.video_current_frame = 0
    
    return st.session_state.video_current_frame


def render_video_with_pose_overlay(video_path, keypoints_data, total_frames, fps, min_confidence=0.5):
    """
    Render video with Pose-Overlay direkt im Player.
    Zuverlässig: HTML5 Video + Canvas-Overlay + Player-Buttons.
    """
    video_b64 = get_video_base64(video_path)
    if not video_b64:
        st.error(f"Konnte Video nicht laden: {video_path}")
        return

    video_ext = Path(video_path).suffix.lower()
    mime_types = {".mp4": "video/mp4", ".webm": "video/webm", ".ogg": "video/ogg",
                  ".mov": "video/quicktime", ".avi": "video/x-msvideo"}
    mime_type = mime_types.get(video_ext, "video/mp4")

    # Keypoints als Base64-JSON (vermeidet Escaping-Probleme)
    kp_list = [f.get("keypoints", []) for f in keypoints_data]
    kp_b64 = base64.b64encode(json.dumps(kp_list).encode()).decode()

    html = f'''
    <div style="margin: 20px 0; font-family: sans-serif;">
        <div style="position: relative; display: inline-block; max-width: 100%;">
            <video id="gaitVideo" controls style="max-width: 100%; border-radius: 8px; display: block;"
                   crossorigin="anonymous">
                <source src="data:{mime_type};base64,{video_b64}" type="{mime_type}">
            </video>
            <canvas id="poseCanvas" style="position: absolute; top: 0; left: 0; pointer-events: none; border-radius: 8px;"></canvas>
        </div>
        <div style="margin-top: 12px;">
            <input type="range" id="seekSlider" min="0" max="{max(0, total_frames - 1) if total_frames else 0}" value="0"
                   style="width: 100%; margin: 8px 0;">
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin: 12px 0;">
            <button id="btnStart" style="padding: 8px 16px; cursor: pointer; border-radius: 6px;">⏮️ Start</button>
            <button id="btnM10" style="padding: 8px 16px; cursor: pointer; border-radius: 6px;">⏪ -10s</button>
            <button id="btnM1" style="padding: 8px 16px; cursor: pointer; border-radius: 6px;">⏪ -1s</button>
            <button id="btnPlay" type="button" style="padding: 8px 20px; cursor: pointer; border-radius: 6px; font-weight: bold;">▶️ Play</button>
            <button id="btnP1" style="padding: 8px 16px; cursor: pointer; border-radius: 6px;">+1s ⏩</button>
            <button id="btnP10" style="padding: 8px 16px; cursor: pointer; border-radius: 6px;">+10s ⏩</button>
            <button id="btnEnd" style="padding: 8px 16px; cursor: pointer; border-radius: 6px;">Ende ⏭️</button>
        </div>
        <div style="color: #666; font-size: 13px; text-align: center;">
            Frame <b id="frameNum">0</b> / {total_frames} &nbsp;|&nbsp; Zeit: <b id="timeVal">0.00</b> s
        </div>
        <script>
        (function() {{
            const keypoints = JSON.parse(atob('{kp_b64}'));
            const skeleton = {json.dumps(SKELETON)};
            const minConf = {min_confidence};
            const fps = {fps};
            const totalFrames = {total_frames};

            const video = document.getElementById('gaitVideo');
            const canvas = document.getElementById('poseCanvas');
            const ctx = canvas.getContext('2d');
            const slider = document.getElementById('seekSlider');
            const btnPlay = document.getElementById('btnPlay');
            const frameNum = document.getElementById('frameNum');
            const timeVal = document.getElementById('timeVal');

            function resizeCanvas() {{
                const w = video.offsetWidth, h = video.offsetHeight;
                if (canvas.width !== w || canvas.height !== h) {{
                    canvas.width = w;
                    canvas.height = h;
                    drawPose();
                }}
            }}

            function drawPose() {{
                const frame = Math.min(Math.floor(video.currentTime * fps), totalFrames - 1);
                if (frame < 0 || !keypoints[frame]) return;
                const kps = keypoints[frame];
                const vw = video.videoWidth, vh = video.videoHeight;
                if (!vw || !vh) return;
                const sx = canvas.width / vw, sy = canvas.height / vh;

                ctx.clearRect(0, 0, canvas.width, canvas.height);

                // Linien
                ctx.lineWidth = 2;
                ctx.strokeStyle = 'rgba(0, 255, 100, 0.9)';
                for (const [i, j] of skeleton) {{
                    if (i >= kps.length || j >= kps.length) continue;
                    const a = kps[i], b = kps[j];
                    if (!a || !b || (a[2] || 0) < minConf || (b[2] || 0) < minConf) continue;
                    ctx.beginPath();
                    ctx.moveTo(a[0] * sx, a[1] * sy);
                    ctx.lineTo(b[0] * sx, b[1] * sy);
                    ctx.stroke();
                }}

                // Punkte
                ctx.fillStyle = 'rgba(255, 200, 50, 0.95)';
                for (let i = 0; i < kps.length; i++) {{
                    const k = kps[i];
                    if (!k || (k[2] || 0) < minConf) continue;
                    ctx.beginPath();
                    ctx.arc(k[0] * sx, k[1] * sy, 4, 0, Math.PI * 2);
                    ctx.fill();
                }}
            }}

            video.addEventListener('loadedmetadata', resizeCanvas);
            video.addEventListener('timeupdate', () => {{
                const f = Math.floor(video.currentTime * fps);
                slider.value = f;
                frameNum.textContent = f;
                timeVal.textContent = video.currentTime.toFixed(2);
                drawPose();
            }});
            video.addEventListener('resize', resizeCanvas);
            window.addEventListener('resize', resizeCanvas);

            slider.addEventListener('input', () => {{
                const f = parseInt(slider.value);
                video.currentTime = f / fps;
                drawPose();
            }});

            btnPlay.addEventListener('click', () => {{
                if (video.paused) {{ video.play(); btnPlay.textContent = '⏸️ Pause'; }}
                else {{ video.pause(); btnPlay.textContent = '▶️ Play'; }}
            }});
            video.addEventListener('play', () => btnPlay.textContent = '⏸️ Pause');
            video.addEventListener('pause', () => btnPlay.textContent = '▶️ Play');
            video.addEventListener('ended', () => btnPlay.textContent = '▶️ Play');

            document.getElementById('btnStart').onclick = () => {{ video.currentTime = 0; drawPose(); }};
            document.getElementById('btnM10').onclick = () => {{ video.currentTime = Math.max(0, video.currentTime - 10); drawPose(); }};
            document.getElementById('btnM1').onclick = () => {{ video.currentTime = Math.max(0, video.currentTime - 1); drawPose(); }};
            document.getElementById('btnP1').onclick = () => {{ video.currentTime = Math.min(video.duration, video.currentTime + 1); drawPose(); }};
            document.getElementById('btnP10').onclick = () => {{ video.currentTime = Math.min(video.duration, video.currentTime + 10); drawPose(); }};
            document.getElementById('btnEnd').onclick = () => {{ video.currentTime = video.duration; drawPose(); }};

            video.load();
        }})();
        </script>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)
