"""
Gait Analyzer - One Euro Filter
================================
Temporal smoothing filter for pose keypoints.
Optimized for gait analysis with parameters:
- fcmin = 1.0 Hz (minimum cutoff frequency)
- beta = 0.007 (speed coefficient)

Reference: Casiez et al. "The 1€ Filter" (CHI 2012)
"""

import numpy as np
from typing import List, Dict, Any


class OneEuroFilter:
    """
    One Euro Filter for temporal smoothing of noisy signals.
    
    The filter adapts its cutoff frequency based on the rate of change:
    - Low speed → low cutoff → more smoothing
    - High speed → high cutoff → less smoothing (preserves responsiveness)
    
    Parameters:
        freq: Sampling frequency (Hz), e.g., 30 for 30 FPS video
        mincutoff: Minimum cutoff frequency (Hz), default 1.0 for gait
        beta: Speed coefficient, default 0.007 for gait
        dcutoff: Derivative cutoff frequency (Hz), default 1.0
    """
    
    def __init__(self, freq: float = 30.0, mincutoff: float = 1.0, 
                 beta: float = 0.007, dcutoff: float = 1.0):
        self.freq = freq
        self.mincutoff = mincutoff
        self.beta = beta
        self.dcutoff = dcutoff
        
        # State variables
        self.x_prev = None  # Previous filtered value
        self.dx_prev = None  # Previous derivative estimate
        self.t_prev = None   # Previous timestamp
    
    def _alpha(self, cutoff: float) -> float:
        """Compute smoothing factor from cutoff frequency."""
        tau = 1.0 / (2 * np.pi * cutoff)
        te = 1.0 / self.freq
        return 1.0 / (1.0 + tau / te)
    
    def filter(self, x: float, t: float = None) -> float:
        """
        Filter a single value.
        
        Args:
            x: Current raw value
            t: Current timestamp (optional, for variable sampling)
        
        Returns:
            Filtered value
        """
        if self.x_prev is None:
            # First sample - initialize
            self.x_prev = x
            self.dx_prev = 0.0
            self.t_prev = t if t is not None else 0.0
            return x
        
        # Compute timestep if timestamps provided
        if t is not None and t != self.t_prev:
            dt = t - self.t_prev
            self.t_prev = t
        else:
            dt = 1.0 / self.freq
        
        # Filtered derivative
        alpha_d = self._alpha(self.dcutoff)
        dx = (x - self.x_prev) / dt
        dx_filtered = alpha_d * dx + (1 - alpha_d) * self.dx_prev
        
        # Adaptive cutoff based on speed
        cutoff = self.mincutoff + self.beta * abs(dx_filtered)
        alpha = self._alpha(cutoff)
        
        # Filtered value
        x_filtered = alpha * x + (1 - alpha) * self.x_prev
        
        # Update state
        self.x_prev = x_filtered
        self.dx_prev = dx_filtered
        
        return x_filtered
    
    def reset(self):
        """Reset filter state."""
        self.x_prev = None
        self.dx_prev = None
        self.t_prev = None


class PoseOneEuroFilter:
    """
    Apply One Euro Filter to all keypoints in pose data.
    Creates separate filters for X, Y coordinates of each keypoint.
    """
    
    def __init__(self, num_keypoints: int = 17, freq: float = 30.0,
                 mincutoff: float = 1.0, beta: float = 0.007):
        self.num_keypoints = num_keypoints
        self.freq = freq
        self.mincutoff = mincutoff
        self.beta = beta
        
        # Create filters for each keypoint coordinate (X, Y)
        # Confidence values are NOT filtered (they're already probabilities)
        self.filters_x = [OneEuroFilter(freq, mincutoff, beta) for _ in range(num_keypoints)]
        self.filters_y = [OneEuroFilter(freq, mincutoff, beta) for _ in range(num_keypoints)]
    
    def filter_frame(self, keypoints: List[List[float]], timestamp: float = None) -> List[List[float]]:
        """
        Filter keypoints for a single frame.
        
        Args:
            keypoints: List of [x, y, confidence] for each keypoint
            timestamp: Frame timestamp (optional)
        
        Returns:
            Filtered keypoints
        """
        filtered = []
        
        for i, kp in enumerate(keypoints):
            if len(kp) >= 2:
                x, y = kp[0], kp[1]
                conf = kp[2] if len(kp) > 2 else 1.0
                
                # Apply filter to X and Y coordinates
                if i < len(self.filters_x):
                    x_filtered = self.filters_x[i].filter(x, timestamp)
                    y_filtered = self.filters_y[i].filter(y, timestamp)
                    filtered.append([x_filtered, y_filtered, conf])
                else:
                    # Fallback if more keypoints than expected
                    filtered.append([x, y, conf])
            else:
                filtered.append(kp)
        
        return filtered
    
    def filter_sequence(self, keypoints_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter entire sequence of frames.
        
        Args:
            keypoints_data: List of frame data with 'keypoints' and 'timestamp'
        
        Returns:
            Filtered sequence (modifies in place for efficiency)
        """
        filtered_data = []
        
        for frame in keypoints_data:
            timestamp = frame.get("timestamp")
            keypoints = frame.get("keypoints", [])
            
            if keypoints:
                filtered_kp = self.filter_frame(keypoints, timestamp)
                filtered_data.append({
                    "frame": frame.get("frame"),
                    "timestamp": timestamp,
                    "keypoints": filtered_kp
                })
            else:
                filtered_data.append(frame)
        
        return filtered_data
    
    def reset(self):
        """Reset all filters."""
        for f in self.filters_x:
            f.reset()
        for f in self.filters_y:
            f.reset()


def apply_one_euro_filter(keypoints_data: List[Dict[str, Any]], 
                          fps: float = 30.0,
                          mincutoff: float = 1.0,
                          beta: float = 0.007) -> List[Dict[str, Any]]:
    """
    Convenience function to apply One Euro Filter to keypoints data.
    
    Args:
        keypoints_data: List of frame data with keypoints
        fps: Video framerate
        mincutoff: Minimum cutoff frequency (default 1.0 for gait)
        beta: Speed coefficient (default 0.007 for gait)
    
    Returns:
        Filtered keypoints data
    """
    # Detect number of keypoints from first frame
    num_kp = 17  # Default COCO format
    if keypoints_data and keypoints_data[0].get("keypoints"):
        num_kp = len(keypoints_data[0]["keypoints"])
    
    filter_obj = PoseOneEuroFilter(num_kp, fps, mincutoff, beta)
    return filter_obj.filter_sequence(keypoints_data)


def compare_raw_vs_filtered(raw_data: List[Dict], filtered_data: List[Dict], 
                            keypoint_idx: int = 0, coord: str = 'x') -> tuple:
    """
    Compare raw vs filtered values for visualization.
    
    Args:
        raw_data: Original keypoints data
        filtered_data: Filtered keypoints data
        keypoint_idx: Which keypoint to compare
        coord: 'x' or 'y'
    
    Returns:
        (timestamps, raw_values, filtered_values)
    """
    coord_idx = 0 if coord.lower() == 'x' else 1
    
    timestamps = []
    raw_values = []
    filtered_values = []
    
    for raw, filt in zip(raw_data, filtered_data):
        timestamps.append(raw.get("timestamp", 0))
        
        raw_kp = raw.get("keypoints", [])
        filt_kp = filt.get("keypoints", [])
        
        if keypoint_idx < len(raw_kp) and len(raw_kp[keypoint_idx]) > coord_idx:
            raw_values.append(raw_kp[keypoint_idx][coord_idx])
        else:
            raw_values.append(None)
        
        if keypoint_idx < len(filt_kp) and len(filt_kp[keypoint_idx]) > coord_idx:
            filtered_values.append(filt_kp[keypoint_idx][coord_idx])
        else:
            filtered_values.append(None)
    
    return timestamps, raw_values, filtered_values
