"""
Gait Analyzer - Components: Video Player with Pose Overlay
===========================================================
Renders video frames with YOLOv8-pose keypoints overlaid.
"""

import cv2
import numpy as np
import streamlit as st

# YOLOv8-pose skeleton connections (COCO format)
# Format: (left_index, right_index, color)
SKELETON_CONNECTIONS = [
    # Left side (blue)
    (0, 1, (255, 0, 0)),    # Nose to Left Eye
    (1, 3, (255, 0, 0)),    # Left Eye to Left Ear
    (0, 2, (255, 0, 0)),    # Nose to Right Eye
    (2, 4, (255, 0, 0)),    # Right Eye to Right Ear
    (5, 6, (0, 255, 255)),  # Left Shoulder to Right Shoulder
    (5, 7, (0, 255, 0)),    # Left Shoulder to Left Elbow
    (7, 9, (0, 255, 0)),    # Left Elbow to Left Wrist
    (6, 8, (255, 0, 255)),  # Right Shoulder to Right Elbow
    (8, 10, (255, 0, 255)), # Right Elbow to Right Wrist
    (5, 11, (0, 255, 0)),   # Left Shoulder to Left Hip
    (6, 12, (255, 0, 255)), # Right Shoulder to Right Hip
    (11, 12, (0, 255, 255)),# Left Hip to Right Hip
    (11, 13, (0, 255, 0)),  # Left Hip to Left Knee
    (12, 14, (255, 0, 255)),# Right Hip to Right Knee
    (13, 15, (0, 255, 0)),  # Left Knee to Left Ankle
    (14, 16, (255, 0, 255)),# Right Knee to Right Ankle
]

# Keypoint names (COCO format)
KEYPOINT_NAMES = [
    "Nose", "L Eye", "R Eye", "L Ear", "R Ear",
    "L Shoulder", "R Shoulder", "L Elbow", "R Elbow",
    "L Wrist", "R Wrist", "L Hip", "R Hip",
    "L Knee", "R Knee", "L Ankle", "R Ankle"
]


def draw_pose_on_frame(frame, keypoints, min_confidence=0.5):
    """
    Draw pose keypoints and skeleton on a video frame.
    
    Args:
        frame: numpy array (BGR format from OpenCV)
        keypoints: list of [x, y, confidence] for each keypoint
        min_confidence: minimum confidence threshold for drawing
    
    Returns:
        frame with pose overlay drawn on it
    """
    frame_copy = frame.copy()
    height, width = frame_copy.shape[:2]
    
    # Filter keypoints by confidence
    valid_keypoints = []
    for kp in keypoints:
        if len(kp) >= 3 and kp[2] >= min_confidence:
            valid_keypoints.append((int(kp[0]), int(kp[1]), kp[2]))
        elif len(kp) >= 2:
            valid_keypoints.append((int(kp[0]), int(kp[1]), 0.0))
        else:
            valid_keypoints.append(None)
    
    # Draw skeleton connections
    for idx1, idx2, color in SKELETON_CONNECTIONS:
        if idx1 < len(valid_keypoints) and idx2 < len(valid_keypoints):
            kp1 = valid_keypoints[idx1]
            kp2 = valid_keypoints[idx2]
            
            if kp1 is not None and kp2 is not None:
                # Only draw if both keypoints have good confidence
                if kp1[2] >= min_confidence and kp2[2] >= min_confidence:
                    cv2.line(
                        frame_copy,
                        (kp1[0], kp1[1]),
                        (kp2[0], kp2[1]),
                        color,
                        2,
                        cv2.LINE_AA
                    )
    
    # Draw keypoints
    for i, kp in enumerate(valid_keypoints):
        if kp is not None and kp[2] >= min_confidence:
            x, y, conf = kp
            
            # Color based on confidence
            if conf >= 0.8:
                color = (0, 255, 0)  # Green - high confidence
            elif conf >= 0.5:
                color = (0, 255, 255)  # Yellow - medium confidence
            else:
                color = (0, 0, 255)  # Red - low confidence
            
            # Draw circle
            cv2.circle(frame_copy, (x, y), 5, color, -1, cv2.LINE_AA)
            
            # Draw small ring around
            cv2.circle(frame_copy, (x, y), 8, color, 1, cv2.LINE_AA)
    
    return frame_copy


def get_frame_with_pose(video_path, keypoints_data, frame_idx, min_confidence=0.5):
    """
    Load a specific frame from video and draw pose overlay.
    
    Args:
        video_path: path to the video file
        keypoints_data: list of frame data with keypoints
        frame_idx: index of the frame to load
        min_confidence: minimum confidence threshold
    
    Returns:
        frame with pose overlay (RGB format for Streamlit)
    """
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return None
    
    # Get keypoints for this frame
    if frame_idx < len(keypoints_data):
        keypoints = keypoints_data[frame_idx]["keypoints"]
    else:
        keypoints = []
    
    # Draw pose
    frame_with_pose = draw_pose_on_frame(frame, keypoints, min_confidence)
    
    # Convert BGR to RGB for Streamlit
    frame_rgb = cv2.cvtColor(frame_with_pose, cv2.COLOR_BGR2RGB)
    
    return frame_rgb


def create_pose_overlay_video(video_path, keypoints_data, output_path, min_confidence=0.5):
    """
    Erstellt ein vollständiges Video mit Pose-Overlay – abspielbar in jedem Player.

    Args:
        video_path: Pfad zum Original-Video
        keypoints_data: Liste der Frame-Daten mit Keypoints
        output_path: Pfad für die Ausgabe (z.B. .mp4)
        min_confidence: Minimum Confidence für Keypoints

    Returns:
        output_path bei Erfolg, None bei Fehler
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # H.264 für Browser; Fallback mp4v
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    if not out.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    if not out.isOpened():
        cap.release()
        return None

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        keypoints = keypoints_data[frame_idx]["keypoints"] if frame_idx < len(keypoints_data) else []
        frame_with_pose = draw_pose_on_frame(frame, keypoints, min_confidence)
        out.write(frame_with_pose)
        frame_idx += 1

    cap.release()
    out.release()
    return output_path


def create_pose_video_preview(video_path, keypoints_data, num_frames=100, min_confidence=0.5):
    """
    Create a preview video with pose overlay by sampling frames.
    
    Args:
        video_path: path to the video file
        keypoints_data: list of frame data with keypoints
        num_frames: number of frames to sample
        min_confidence: minimum confidence threshold
    
    Returns:
        list of frames with pose overlay (RGB format)
    """
    total_frames = len(keypoints_data)
    if total_frames == 0:
        return []
    
    # Sample frames evenly
    frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
    
    frames_with_pose = []
    cap = cv2.VideoCapture(video_path)
    
    for frame_idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        
        if not ret:
            continue
        
        # Get keypoints for this frame
        if frame_idx < len(keypoints_data):
            keypoints = keypoints_data[frame_idx]["keypoints"]
        else:
            keypoints = []
        
        # Draw pose
        frame_with_pose = draw_pose_on_frame(frame, keypoints, min_confidence)
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame_with_pose, cv2.COLOR_BGR2RGB)
        frames_with_pose.append(frame_rgb)
    
    cap.release()
    return frames_with_pose
