"""
Haile - Professional Analysis Engine
=====================================
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
    
    # Phase percentages
    double_support_percent: float = 0.0   # % of gait cycle where both feet on ground
    single_support_percent: float = 0.0   # % where one foot on ground
    swing_phase_left: float = 0.0         # % for left leg
    swing_phase_right: float = 0.0        # % for right leg
    stance_phase_left: float = 0.0        # % for left leg
    stance_phase_right: float = 0.0       # % for right leg
    
    # Swing phase symmetry
    swing_symmetry_index: float = 0.0     # Difference between left/right swing
    stance_symmetry_index: float = 0.0    # Difference between left/right stance
    
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
    has_phase_asymmetry: bool = False
    

def calculate_gait_phases(keypoints_data: List[Dict], left_strikes: List[int], 
                         right_strikes: List[int], fps: float = 30.0) -> Dict[str, float]:
    """
    Calculate gait phase percentages.
    
    Returns:
        Dictionary with phase percentages and symmetry indices
    """
    if not left_strikes or not right_strikes or len(keypoints_data) < 10:
        return {
            'double_support': 0.0,
            'single_support': 0.0,
            'swing_left': 0.0,
            'swing_right': 0.0,
            'stance_left': 0.0,
            'stance_right': 0.0,
            'swing_symmetry': 0.0,
            'stance_symmetry': 0.0
        }
    
    total_frames = len(keypoints_data)
    
    # Sort strikes chronologically
    all_events = []
    for frame in left_strikes:
        all_events.append(('left', frame))
    for frame in right_strikes:
        all_events.append(('right', frame))
    all_events.sort(key=lambda x: x[1])
    
    if len(all_events) < 4:
        return {k: 0.0 for k in ['double_support', 'single_support', 'swing_left', 'swing_right', 
                                  'stance_left', 'stance_right', 'swing_symmetry', 'stance_symmetry']}
    
    # Calculate phases based on alternating pattern
    double_support_frames = 0
    single_support_frames = 0
    left_swing_frames = 0
    right_swing_frames = 0
    left_stance_frames = 0
    right_stance_frames = 0
    
    for i in range(len(all_events) - 1):
        current_side, current_frame = all_events[i]
        next_side, next_frame = all_events[i + 1]
        duration = next_frame - current_frame
        
        if current_side != next_side:
            # Alternating steps - single support phase
            single_support_frames += duration
            
            # The leg that just struck is now in stance
            # The other leg is in swing
            if current_side == 'left':
                left_stance_frames += duration
                right_swing_frames += duration  # Right was swinging before strike
            else:
                right_stance_frames += duration
                left_swing_frames += duration
        else:
            # Same side twice - indicates double support or irregular gait
            double_support_frames += duration // 2
            single_support_frames += duration // 2
    
    # Calculate percentages
    def safe_percent(frames):
        return (frames / total_frames * 100) if total_frames > 0 else 0.0
    
    swing_left_pct = safe_percent(left_swing_frames)
    swing_right_pct = safe_percent(right_swing_frames)
    stance_left_pct = safe_percent(left_stance_frames)
    stance_right_pct = safe_percent(right_stance_frames)
    
    # Normalized to gait cycle (should sum to ~100%)
    total_cycle = swing_left_pct + stance_left_pct
    if total_cycle > 0:
        swing_left_pct = (swing_left_pct / total_cycle) * 100
        stance_left_pct = (stance_left_pct / total_cycle) * 100
    
    total_cycle_right = swing_right_pct + stance_right_pct
    if total_cycle_right > 0:
        swing_right_pct = (swing_right_pct / total_cycle_right) * 100
        stance_right_pct = (stance_right_pct / total_cycle_right) * 100
    
    # Calculate symmetry indices
    swing_symmetry = abs(swing_left_pct - swing_right_pct) / ((swing_left_pct + swing_right_pct) / 2) * 100 if (swing_left_pct + swing_right_pct) > 0 else 0
    stance_symmetry = abs(stance_left_pct - stance_right_pct) / ((stance_left_pct + stance_right_pct) / 2) * 100 if (stance_left_pct + stance_right_pct) > 0 else 0
    
    return {
        'double_support': safe_percent(double_support_frames),
        'single_support': safe_percent(single_support_frames),
        'swing_left': swing_left_pct,
        'swing_right': swing_right_pct,
        'stance_left': stance_left_pct,
        'stance_right': stance_right_pct,
        'swing_symmetry': swing_symmetry,
        'stance_symmetry': stance_symmetry
    }


def detect_heel_strikes(keypoints_data: List[Dict], fps: float = 30.0,
                       min_step_interval_ms: float = 200.0) -> Tuple[List[int], List[int]]:
    """
    Detect heel strikes (initial contact) for left and right foot.
    Improved algorithm with better sensitivity.
    
    Args:
        keypoints_data: List of frame data with keypoints
        fps: Video framerate
        min_step_interval_ms: Minimum time between steps (ms) to avoid double-counting
    
    Returns:
        (left_heel_strike_frames, right_heel_strike_frames)
    """
    left_strikes = []
    right_strikes = []
    
    min_frame_interval = int((min_step_interval_ms / 1000.0) * fps)
    
    # Track Y positions over time for both ankles
    left_y_history = []
    right_y_history = []
    valid_frames = []
    
    for i, frame in enumerate(keypoints_data):
        kps = frame.get("keypoints", [])
        if len(kps) < 17:
            continue
        
        # Get ankle positions with confidence check
        left_ankle = kps[15] if len(kps) > 15 and len(kps[15]) >= 3 and kps[15][2] > 0.3 else None
        right_ankle = kps[16] if len(kps) > 16 and len(kps[16]) >= 3 and kps[16][2] > 0.3 else None
        
        if left_ankle and right_ankle:
            left_y_history.append((i, left_ankle[1]))
            right_y_history.append((i, right_ankle[1]))
            valid_frames.append(i)
    
    if len(left_y_history) < 10 or len(right_y_history) < 10:
        return left_strikes, right_strikes
    
    # Find local minima in Y position (lowest point = heel strike)
    def find_strikes(y_history, side_name):
        strikes = []
        window_size = max(3, min_frame_interval // 2)
        
        for i in range(window_size, len(y_history) - window_size):
            frame_idx, y_val = y_history[i]
            
            # Check if local minimum
            is_minimum = True
            for j in range(1, window_size + 1):
                if i - j >= 0 and y_history[i - j][1] < y_val:
                    is_minimum = False
                    break
                if i + j < len(y_history) and y_history[i + j][1] < y_val:
                    is_minimum = False
                    break
            
            if is_minimum:
                # Check minimum interval from last strike
                if not strikes or (frame_idx - strikes[-1]) >= min_frame_interval:
                    strikes.append(frame_idx)
        
        return strikes
    
    left_strikes = find_strikes(left_y_history, "left")
    right_strikes = find_strikes(right_y_history, "right")
    
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
    """
    Calculate interior angle at p2 formed by p1-p2-p3 in degrees.
    Correctly handles image coordinates (Y increases downward).
    For knee: p1=hip, p2=knee, p3=ankle
    Returns angle between 0-180 degrees.
    """
    try:
        # Convert to numpy arrays (X, Y)
        hip = np.array([float(p1[0]), float(p1[1])])
        knee = np.array([float(p2[0]), float(p2[1])])
        ankle = np.array([float(p3[0]), float(p3[1])])
        
        # Vector from knee to hip (thigh direction)
        thigh = hip - knee
        # Vector from knee to ankle (shin direction)
        shin = ankle - knee
        
        # Check for zero vectors
        norm_thigh = np.linalg.norm(thigh)
        norm_shin = np.linalg.norm(shin)
        
        if norm_thigh < 1e-10 or norm_shin < 1e-10:
            return 0.0
        
        # Calculate angle between thigh and shin
        cos_angle = np.dot(thigh, shin) / (norm_thigh * norm_shin)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)
        
        # The angle should be the supplement for knee flexion
        # When leg is straight: angle ≈ 180°
        # When knee is bent: angle < 180°
        # For knee flexion angle: 180 - calculated_angle
        knee_flexion = 180.0 - angle_deg
        
        return knee_flexion
    except Exception:
        return 0.0


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
    
    # Advanced Phase Analysis
    phases = calculate_gait_phases(keypoints_data, left_strikes, right_strikes, fps)
    
    metrics.double_support_percent = phases['double_support']
    metrics.single_support_percent = phases['single_support']
    metrics.swing_phase_left = phases['swing_left']
    metrics.swing_phase_right = phases['swing_right']
    metrics.stance_phase_left = phases['stance_left']
    metrics.stance_phase_right = phases['stance_right']
    metrics.swing_symmetry_index = phases['swing_symmetry']
    metrics.stance_symmetry_index = phases['stance_symmetry']
    
    # Phase asymmetry detection (>15% difference is significant for phases)
    metrics.has_phase_asymmetry = (metrics.swing_symmetry_index > 15 or 
                                   metrics.stance_symmetry_index > 15)
    
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
