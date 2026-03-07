"""
Haile - Longitudinal Tracking
==============================
Track patient progress over multiple gait analyses.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class AnalysisSnapshot:
    """Snapshot of a single gait analysis."""
    date: str
    patient_id: str
    duration_seconds: float
    step_count: int
    cadence: float
    symmetry_index: float
    step_length_left: float
    step_length_right: float
    max_knee_flexion: float
    notes: str = ""


class LongitudinalTracker:
    """
    Track patient progress over multiple analyses.
    """
    
    def __init__(self, data_dir: str = "data/processed"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def get_patient_analyses(self, patient_id: str) -> List[AnalysisSnapshot]:
        """Get all analyses for a specific patient."""
        analyses = []
        
        # Find all keypoint files for this patient
        if not self.data_dir.exists():
            return analyses
        
        for file_path in sorted(self.data_dir.glob(f"{patient_id}_*_keypoints.json")):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                metadata = data.get('metadata', {})
                
                # Try to load corresponding anamnesis
                anamnesis_file = self.data_dir / f"anamnese_{patient_id}.json"
                notes = ""
                if anamnesis_file.exists():
                    with open(anamnesis_file, 'r', encoding='utf-8') as f:
                        anamnesis = json.load(f)
                        notes = anamnesis.get('hauptbeschwerde', '')
                
                snapshot = AnalysisSnapshot(
                    date=metadata.get('processing_date', '')[:10],
                    patient_id=patient_id,
                    duration_seconds=metadata.get('video_info', {}).get('duration_seconds', 0),
                    step_count=metadata.get('video_info', {}).get('total_frames', 0) // 30,
                    cadence=0,  # Would need proper calculation
                    symmetry_index=0,  # Would need proper calculation
                    step_length_left=0,
                    step_length_right=0,
                    max_knee_flexion=0,
                    notes=notes
                )
                
                analyses.append(snapshot)
                
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        # Sort by date
        analyses.sort(key=lambda x: x.date)
        return analyses
    
    def get_all_patients(self) -> List[str]:
        """Get list of all unique patient IDs."""
        patients = set()
        
        if not self.data_dir.exists():
            return list(patients)
        
        for file_path in self.data_dir.glob("*_keypoints.json"):
            # Extract patient ID from filename
            parts = file_path.stem.split('_')
            if parts:
                patients.add(parts[0])
        
        return sorted(list(patients))
    
    def calculate_progress(self, patient_id: str) -> Dict[str, any]:
        """
        Calculate progress metrics for a patient.
        
        Returns:
            Dictionary with progress indicators
        """
        analyses = self.get_patient_analyses(patient_id)
        
        if len(analyses) < 2:
            return {
                'total_analyses': len(analyses),
                'first_date': analyses[0].date if analyses else None,
                'last_date': analyses[-1].date if analyses else None,
                'trend': 'insufficient_data',
                'improvements': []
            }
        
        # Analyze trends
        improvements = []
        
        # Check symmetry trend (lower is better)
        symmetry_values = [a.symmetry_index for a in analyses if a.symmetry_index > 0]
        if len(symmetry_values) >= 2:
            if symmetry_values[-1] < symmetry_values[0]:
                improvements.append('symmetry')
        
        # Check cadence trend (closer to 100-120 is better)
        cadence_values = [a.cadence for a in analyses if a.cadence > 0]
        if len(cadence_values) >= 2:
            optimal_cadence = 110
            first_diff = abs(cadence_values[0] - optimal_cadence)
            last_diff = abs(cadence_values[-1] - optimal_cadence)
            if last_diff < first_diff:
                improvements.append('cadence')
        
        # Determine overall trend
        if len(improvements) >= 2:
            trend = 'improving'
        elif len(improvements) == 1:
            trend = 'stable'
        else:
            trend = 'declining'
        
        return {
            'total_analyses': len(analyses),
            'first_date': analyses[0].date,
            'last_date': analyses[-1].date,
            'trend': trend,
            'improvements': improvements,
            'analyses': analyses
        }
    
    def generate_progress_report(self, patient_id: str) -> str:
        """Generate a text progress report for a patient."""
        progress = self.calculate_progress(patient_id)
        
        if progress['total_analyses'] < 2:
            return f"Unzureichende Daten für Verlaufskontrolle. Nur {progress['total_analyses']} Analyse(n) vorhanden."
        
        report = []
        report.append(f"# Verlaufskontrolle: {patient_id}")
        report.append("")
        report.append(f"**Analysen:** {progress['total_analyses']}")
        report.append(f"**Zeitraum:** {progress['first_date']} bis {progress['last_date']}")
        report.append("")
        
        # Trend
        trend_emoji = {
            'improving': '📈',
            'stable': '➡️',
            'declining': '📉',
            'insufficient_data': '❓'
        }
        
        trend_text = {
            'improving': 'Verbesserung erkennbar',
            'stable': 'Stabiler Verlauf',
            'declining': 'Verschlechterung erkennbar',
            'insufficient_data': 'Unzureichende Daten'
        }
        
        report.append(f"**Trend:** {trend_emoji.get(progress['trend'], '❓')} {trend_text.get(progress['trend'], 'Unbekannt')}")
        report.append("")
        
        # Improvements
        if progress['improvements']:
            report.append("### Verbesserungen")
            for imp in progress['improvements']:
                if imp == 'symmetry':
                    report.append("✅ Symmetrie verbessert")
                elif imp == 'cadence':
                    report.append("✅ Cadenz normalisiert")
            report.append("")
        
        # Analysis timeline
        report.append("### Analysen-Timeline")
        report.append("")
        
        for i, analysis in enumerate(progress.get('analyses', []), 1):
            report.append(f"**{i}. Analyse ({analysis.date})**")
            if analysis.notes:
                report.append(f"- Beschwerde: {analysis.notes}")
            report.append("")
        
        return "\n".join(report)
    
    def export_progress_data(self, patient_id: str, output_path: str):
        """Export progress data as JSON."""
        progress = self.calculate_progress(patient_id)
        
        data = {
            'patient_id': patient_id,
            'generated_at': datetime.now().isoformat(),
            'progress': progress
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return output_path


# Convenience function
def get_patient_timeline(patient_id: str) -> List[Dict]:
    """Get simplified timeline for a patient."""
    tracker = LongitudinalTracker()
    analyses = tracker.get_patient_analyses(patient_id)
    
    return [
        {
            'date': a.date,
            'duration': a.duration_seconds,
            'notes': a.notes
        }
        for a in analyses
    ]
