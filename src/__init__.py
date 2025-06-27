# Clippy Source Code
# AI-powered YouTube Shorts generator

"""
Clippy - Transform long-form videos into viral shorts
"""

__version__ = "2.0.0"
__author__ = "DS"
__email__ = "schwenkedavis@gmail.com"

# Make imports easier by exposing main classes
from src.core.viral_clipper_complete import ViralClipGenerator
from src.core.auto_peak_viral_clipper import AutoPeakViralClipper
from src.core.enhanced_heuristic_peak_detector import EnhancedHeuristicPeakDetector
from src.captions.ass_caption_update_system_v6 import ASSCaptionUpdateSystemV6

__all__ = [
    "ViralClipGenerator",
    "AutoPeakViralClipper", 
    "EnhancedHeuristicPeakDetector",
    "ASSCaptionUpdateSystemV6",
]
