"""
Gait Analyzer - Professional Analysis Engine
=============================================
Calculates clinical gait metrics from pose keypoints.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class GaitMetrics:
    """Container for calculated gait metrics."""
    # Temporal parameters
    step_count: int = 0
    cadence: float = 0.0  # steps per minute
    step_time_left: float = 0.0  # seconds
    step_time_right: float = 0.0
    double_support_time: float = 0.0  # percentage of gait cycle
    single_support_time: float = 0.0
    swing_phase_percent: float = 0.0
    stance_phase_percent: float = 0.0
    
    # Spatial parameters
    step_length_left: float = 0.0  # cm
    step_length_right: float = 0.0
    stride_length: float = 0.0
    step_width: float = 0.0
    base_of_support: float = 0.0
    
    # Symmetry
    symmetry_index: float = 0.0  # 0 = perfect symmetry, >0 = asymmetry
    left_right_ratio: float = 1.0
    
    # Kinematic
    max_knee_flexion: float = 0.0  # degrees
    hip_range_of_motion: float = 0.0
    ankle_dorsiflexion: float = 0.0
    
    # Red flags
    has_asymmetry: bool = False
    has_irregular_cadence: bool = False
    

def detect_heel_strikes(keypoints_data: List[Dict], fps: float = 30.0) -> Tuple[List[int], List[int]]:
    """
    Detect heel strikes (initial contact) for left and right foot.
    
    Returns:
        (left_heel_strike_frames, right_heel_strike_frames)
    """
    left_strikes = []
    right_strikes = []
    
    prev_left_y = None
    prev_right_y = None
    
    for i, frame in enumerate(keypoints_data):
        kps = frame.get("keypoints", [])
        if len(kps) < 16:
            continue
        
        # Left ankle (index 15), Right ankle (index 16) in COCO format
        left_ankle = kps[15] if len(kps) > 15 else None
        right_ankle = kps[16] if len(kps) > 16 else None
        
        if left_ankle and len(left_ankle) >= 2 and prev_left_y is not None:
            # Heel strike: Y position changes from decreasing to increasing (foot hitting ground)
            current_y = left_ankle[1]
            if prev_left_y < current_y - 5:  # Threshold for movement
                # Check if it's a local minimum (heel strike)
                if i > 0 and i < len(keypoints_data) - 1:
                    prev_frame_y = keypoints_data[i-1]["keypoints"][15][1] if len(keypoints_data[i-1]["keypoints"]) > 15 else current_y
                    next_frame_y = keypoints_data[i+1]["keypoints"][15][1] if len(keypoints_data[i+1]["keypoints"]) > 15 else current_y
                    if current_y <= prev_frame_y and current_y <= next_frame_y:
                        left_strikes.append(i)
            prev_left_y = current_y
        elif left_ankle:
            prev_left_y = left_ankle[1]
        
        if right_ankle and len(right_ankle) >= 2 and prev_right_y is not None:
            current_y = right_ankle[1]
            if prev_right_y < current_y - 5:
                if i > 0 and i < len(keypoints_data) - 1:
                    prev_frame_y = keypoints_data[i-1]["keypoints"][16][1] if len(keypoints_data[i-1]["keypoints"]) > 16 else current_y
                    next_frame_y = keypoints_data[i+1]["keypoints"][16][1] if len(keypoints_data[i+1]["keypoints"]) > 16 else current_y
                    if current_y <= prev_frame_y and current_y <= next_frame_y:
                        right_strikes.append(i)
            prev_right_y = current_y
        elif right_ankle:
            prev_right_y = right_ankle[1]
    
    return left_strikes, right_strikes


def calculate_step_lengths(keypoints_data: List[Dict], pixel_to_cm: float = 1.0) -> Tuple[float, float]:
    """
    Calculate step lengths for left and right foot.
    
    Args:
        pixel_to_cm: Conversion factor from pixels to cm
    
    Returns:
        (left_step_length, right_step_length) in cm
    """
    left_lengths = []
    right_lengths = []
    
    left_strikes, right_strikes = detect_heel_strikes(keypoints_data)
    
    # Calculate distance between consecutive strikes
    for i in range(len(left_strikes) - 1):
        frame1 = keypoints_data[left_strikes[i]]
        frame2 = keypoints_data[left_strikes[i + 1]]
        
        kps1 = frame1.get("keypoints", [])
        kps2 = frame2.get("keypoints", [])
        
        if len(kps1) > 15 and len(kps2) > 15:
            left_ankle1 = kps1[15]
            left_ankle2 = kps2[15]
            if len(left_ankle1) >= 2 and len(left_ankle2) >= 2:
                dist = abs(left_ankle2[0] - left_ankle1[0]) * pixel_to_cm
                left_lengths.append(dist)
    
    for i in range(len(right_strikes) - 1):
        frame1 = keypoints_data[right_strikes[i]]
        frame2 = keypoints_data[right_strikes[i + 1]]
        
        kps1 = frame1.get("keypoints", [])
        kps2 = frame2.get("keypoints", [])
        
        if len(kps1) > 16 and len(kps2) > 16:
            right_ankle1 = kps1[16]
            right_ankle2 = kps2[16]
            if len(right_ankle1) >= 2 and len(right_ankle2) >= 2:
                dist = abs(right_ankle2[0] - right_ankle1[0]) * pixel_to_cm
                right_lengths.append(dist)
    
    left_avg = np.mean(left_lengths) if left_lengths else 0.0
    right_avg = np.mean(right_lengths) if right_lengths else 0.0
    
    return left_avg, right_avg


def calculate_joint_angles(keypoints_data: List[Dict]) -> Dict[str, List[float]]:
    """
    Calculate joint angles over time.
    
    Returns:
        Dictionary with 'knee_left', 'knee_right', 'hip_left', 'hip_right', 'ankle_left', 'ankle_right'
    """
    angles = {
        'knee_left': [], 'knee_right': [],
        'hip_left': [], 'hip_right': [],
        'ankle_left': [], 'ankle_right': []
    }
    
    for frame in keypoints_data:
        kps = frame.get("keypoints", [])
        if len(kps) < 17:
            continue
        
        # Knee angles (hip-knee-ankle)
        # Left: hip=11, knee=13, ankle=15
        if all(len(kps[i]) >= 2 for i in [11, 13, 15]):
            angle = calculate_angle(kps[11], kps[13], kps[15])
            angles['knee_left'].append(angle)
        
        # Right: hip=12, knee=14, ankle=16
        if all(len(kps[i]) >= 2 for i in [12, 14, 16]):
            angle = calculate_angle(kps[12], kps[14], kps[16])
            angles['knee_right'].append(angle)
        
        # Hip angles (shoulder-hip-knee)
        # Left: shoulder=5, hip=11, knee=13
        if all(len(kps[i]) >= 2 for i in [5, 11, 13]):
            angle = calculate_angle(kps[5], kps[11], kps[13])
            angles['hip_left'].append(angle)
        
        # Right: shoulder=6, hip=12, knee=14
        if all(len(kps[i]) >= 2 for i in [6, 12, 14]):
            angle = calculate_angle(kps[6], kps[12], kps[14])
            angles['hip_right'].append(angle)
    
    return angles


def calculate_angle(p1: List[float], p2: List[float], p3: List[float]) -> float:
    """Calculate angle at p2 formed by p1-p2-p3 in degrees."""
    a = np.array([p1[0], p1[1]])
    b = np.array([p2[0], p2[1]])
    c = np.array([p3[0], p3[1]])
    
    ba = a - b
    bc = c - b
    
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
    
    angle = np.arccos(cosine_angle)
    return np.degrees(angle)


def analyze_gait(keypoints_data: List[Dict], fps: float = 30.0, 
                 duration_seconds: float = None,
                 pixel_to_cm: float = 1.0) -> GaitMetrics:
    """
    Perform complete gait analysis.
    
    Args:
        keypoints_data: List of frame data with keypoints
        fps: Video framerate
        duration_seconds: Total video duration
        pixel_to_cm: Conversion factor from pixels to cm
    
    Returns:
        GaitMetrics object with all calculated metrics
    """
    metrics = GaitMetrics()
    
    if not keypoints_data:
        return metrics
    
    # Detect heel strikes
    left_strikes, right_strikes = detect_heel_strikes(keypoints_data, fps)
    total_steps = len(left_strikes) + len(right_strikes)
    metrics.step_count = total_steps
    
    # Cadence (steps per minute)
    if duration_seconds and duration_seconds > 0:
        metrics.cadence = (total_steps / duration_seconds) * 60
    
    # Step times
    if len(left_strikes) > 1 and duration_seconds:
        left_intervals = np.diff(left_strikes) / fps
        metrics.step_time_left = np.mean(left_intervals) if len(left_intervals) > 0 else 0
    
    if len(right_strikes) > 1 and duration_seconds:
        right_intervals = np.diff(right_strikes) / fps
        metrics.step_time_right = np.mean(right_intervals) if len(right_intervals) > 0 else 0
    
    # Step lengths
    left_length, right_length = calculate_step_lengths(keypoints_data, pixel_to_cm)
    metrics.step_length_left = left_length
    metrics.step_length_right = right_length
    metrics.stride_length = (left_length + right_length) / 2 * 2  # Approximate
    
    # Symmetry index
    if left_length > 0 and right_length > 0:
        metrics.symmetry_index = abs(left_length - right_length) / ((left_length + right_length) / 2) * 100
        metrics.left_right_ratio = left_length / right_length
        metrics.has_asymmetry = metrics.symmetry_index > 10  # >10% difference is significant
    
    # Joint angles
    angles = calculate_joint_angles(keypoints_data)
    if angles['knee_left']:
        metrics.max_knee_flexion = max(angles['knee_left'])
    if angles['hip_left']:
        metrics.hip_range_of_motion = max(angles['hip_left']) - min(angles['hip_left'])
    
    # Phase percentages (simplified)
    if metrics.step_time_left > 0:
        metrics.swing_phase_percent = 40.0  # Typical value
        metrics.stance_phase_percent = 60.0
    
    return metrics


def generate_clinical_summary(metrics: GaitMetrics) -> str:
    """Generate a clinical summary text from metrics."""
    summary = []
    summary.append("## Ganganalyse-Befund")
    summary.append("")
    
    # Overall assessment
    if metrics.has_asymmetry:
        summary.append("⚠️ **Auffälligkeit:** Asymmetrisches Gangbild erkannt")
        summary.append(f"   - Symmetrie-Index: {metrics.symmetry_index:.1f}% (Normal: <10%)")
    else:
        summary.append("✅ **Symmetrischer Gang** erkannt")
    
    summary.append("")
    summary.append(f"**Schrittanzahl:** {metrics.step_count}")
    summary.append(f"**Cadenz:** {metrics.cadence:.1f} Schritte/Minute")
    
    if metrics.step_length_left > 0 or metrics.step_length_right > 0:
        summary.append("")
        summary.append("**Schrittlängen:**")
        summary.append(f"   - Links: {metrics.step_length_left:.1f} cm")
        summary.append(f"   - Rechts: {metrics.step_length_right:.1f} cm")
    
    if metrics.max_knee_flexion > 0:
        summary.append("")
        summary.append(f"**Max. Knieflexion:** {metrics.max_knee_flexion:.1f}°")
    
    return "\n".join(summary)
