"""
Gait Analyzer - Video Player Component
========================================
HTML5 Video Player with frame-accurate pose overlay.
"""

import streamlit as st
import base64
import json
from pathlib import Path

# YOLOv8/COCO Skeleton connections
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

def render_video_with_pose_overlay(video_path, keypoints_data, total_frames, fps, min_confidence=0.5):
    """
    Render video with Pose-Overlay direkt im Player.
    """
    video_b64 = get_video_base64(video_path)
    if not video_b64:
        st.error(f"Konnte Video nicht laden: {video_path}")
        return

    video_ext = Path(video_path).suffix.lower()
    mime_types = {".mp4": "video/mp4", ".webm": "video/webm", ".ogg": "video/ogg",
                  ".mov": "video/quicktime", ".avi": "video/x-msvideo"}
    mime_type = mime_types.get(video_ext, "video/mp4")

    # Keypoints als Base64-JSON
    kp_list = [f.get("keypoints", []) for f in keypoints_data]
    kp_b64 = base64.b64encode(json.dumps(kp_list).encode()).decode()

    html = f'''
    <div class="my-6 font-sans">
        <div class="relative inline-block max-w-full">
            <video id="gaitVideo" controls class="max-w-full rounded-lg block" crossorigin="anonymous">
                <source src="data:{mime_type};base64,{video_b64}" type="{mime_type}">
            </video>
            <canvas id="poseCanvas" class="absolute top-0 left-0 pointer-events-none rounded-lg"></canvas>
        </div>
        <div class="mt-3">
            <input type="range" id="seekSlider" min="0" max="{max(0,total_frames-1) if total_frames else 0}" value="0"
                   class="w-full my-2 accent-sky-500">
        </div>
        <div class="flex flex-wrap gap-2 justify-center my-3">
            <button id="btnStart" class="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm font-medium transition">Start</button>
            <button id="btnM10" class="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm transition">-10s</button>
            <button id="btnM1" class="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm transition">-1s</button>
            <button id="btnPlay" type="button" class="px-5 py-2 rounded-lg bg-sky-500 hover:bg-sky-600 text-white font-semibold transition">Play</button>
            <button id="btnP1" class="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm transition">+1s</button>
            <button id="btnP10" class="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm transition">+10s</button>
            <button id="btnEnd" class="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm transition">Ende</button>
        </div>
        <div class="text-slate-500 text-sm text-center">
            Frame <b id="frameNum" class="text-slate-300">0</b> / {total_frames} &nbsp;|&nbsp; Zeit: <b id="timeVal" class="text-slate-300">0.00</b> s
        </div>
        <script>
        (function(){{
            const keypoints=JSON.parse(atob('{kp_b64}'));
            const skeleton={json.dumps(SKELETON)};
            const minConf={min_confidence};
            const fps={fps};
            const totalFrames={total_frames};
            const video=document.getElementById('gaitVideo');
            const canvas=document.getElementById('poseCanvas');
            const ctx=canvas.getContext('2d');
            const slider=document.getElementById('seekSlider');
            const btnPlay=document.getElementById('btnPlay');
            const frameNum=document.getElementById('frameNum');
            const timeVal=document.getElementById('timeVal');
            function resizeCanvas(){{
                const w=video.offsetWidth,h=video.offsetHeight;
                if(canvas.width!==w||canvas.height!==h){{
                    canvas.width=w;canvas.height=h;drawPose();
                }}
            }}
            function drawPose(){{
                const frame=Math.min(Math.floor(video.currentTime*fps),totalFrames-1);
                if(frame<0||!keypoints[frame])return;
                const kps=keypoints[frame];
                const vw=video.videoWidth,vh=video.videoHeight;
                if(!vw||!vh)return;
                const sx=canvas.width/vw,sy=canvas.height/vh;
                ctx.clearRect(0,0,canvas.width,canvas.height);
                // Linien
                ctx.lineWidth=2;ctx.strokeStyle='rgba(0,255,100,0.9)';
                for(const[i,j]of skeleton){{
                    if(i>=kps.length||j>=kps.length)continue;
                    const a=kps[i],b=kps[j];
                    if(!a||!b||(a[2]||0)<minConf||(b[2]||0)<minConf)continue;
                    ctx.beginPath();ctx.moveTo(a[0]*sx,a[1]*sy);ctx.lineTo(b[0]*sx,b[1]*sy);ctx.stroke();
                }}
                // Punkte
                ctx.fillStyle='rgba(255,200,50,0.95)';
                for(let i=0;i<kps.length;i++){{
                    const k=kps[i];
                    if(!k||(k[2]||0)<minConf)continue;
                    ctx.beginPath();ctx.arc(k[0]*sx,k[1]*sy,4,0,Math.PI*2);ctx.fill();
                }}
            }}
            video.addEventListener('loadedmetadata',resizeCanvas);
            video.addEventListener('timeupdate',()=>{{
                const f=Math.floor(video.currentTime*fps);
                slider.value=f;frameNum.textContent=f;timeVal.textContent=video.currentTime.toFixed(2);
                drawPose();
            }});
            video.addEventListener('resize',resizeCanvas);
            window.addEventListener('resize',resizeCanvas);
            slider.addEventListener('input',()=>{{
                const f=parseInt(slider.value);
                video.currentTime=f/fps;drawPose();
            }});
            btnPlay.addEventListener('click',()=>{{
                if(video.paused){{video.play();btnPlay.textContent='Pause';}}
                else{{video.pause();btnPlay.textContent='Play';}}
            }});
            video.addEventListener('play',()=>btnPlay.textContent='Pause');
            video.addEventListener('pause',()=>btnPlay.textContent='Play');
            video.addEventListener('ended',()=>btnPlay.textContent='Play');
            document.getElementById('btnStart').onclick=()=>{{video.currentTime=0;drawPose();}};
            document.getElementById('btnM10').onclick=()=>{{video.currentTime=Math.max(0,video.currentTime-10);drawPose();}};
            document.getElementById('btnM1').onclick=()=>{{video.currentTime=Math.max(0,video.currentTime-1);drawPose();}};
            document.getElementById('btnP1').onclick=()=>{{video.currentTime=Math.min(video.duration,video.currentTime+1);drawPose();}};
            document.getElementById('btnP10').onclick=()=>{{video.currentTime=Math.min(video.duration,video.currentTime+10);drawPose();}};
            document.getElementById('btnEnd').onclick=()=>{{video.currentTime=video.duration;drawPose();}};
            video.load();
        }})();
        </script>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)
