# Core processing modules for Clippy

"""
Core functionality for video processing and clip generation
"""

from .viral_clipper_complete import ViralClipGenerator, Speaker
from .auto_peak_viral_clipper import AutoPeakViralClipper
from .enhanced_heuristic_peak_detector import EnhancedHeuristicPeakDetector, ViralMoment
from .storage_optimizer import StorageOptimizer

__all__ = [
    "ViralClipGenerator",
    "Speaker",
    "AutoPeakViralClipper",
    "EnhancedHeuristicPeakDetector",
    "ViralMoment",
    "StorageOptimizer",
]
