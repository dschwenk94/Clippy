# Clippy Import Guide

With the new `src/` directory structure, here are the different ways to import Clippy modules:

## Import Methods

### Method 1: Direct imports from src submodules
```python
# Most explicit and clear
from src.core.viral_clipper_complete import ViralClipGenerator
from src.core.auto_peak_viral_clipper import AutoPeakViralClipper
from src.captions.ass_caption_update_system_v6 import ASSCaptionUpdateSystemV6
from src.routes.tiktok_routes import tiktok_bp
```

### Method 2: Import from submodule packages
```python
# Using the __init__.py exports
from src.core import ViralClipGenerator, AutoPeakViralClipper
from src.captions import ASSCaptionUpdateSystemV6
```

### Method 3: Import from top-level src
```python
# Simplest - using top-level src/__init__.py
from src import (
    ViralClipGenerator,
    AutoPeakViralClipper,
    ASSCaptionUpdateSystemV6
)
```

## Common Import Patterns

### In app.py
```python
# Core functionality
from src.core import ViralClipGenerator, AutoPeakViralClipper
from src.captions import ASSCaptionUpdateSystemV6
from src.routes.tiktok_routes import tiktok_bp
from src.core.storage_optimizer import StorageOptimizer
```

### In test files
```python
# For testing specific modules
from src.core.enhanced_heuristic_peak_detector import (
    EnhancedHeuristicPeakDetector,
    ViralMoment
)
from src.captions.caption_fragment_fix import fix_caption_fragments
```

### In utility scripts
```python
# When you need specific functionality
from src.utils.install_deps import install_dependencies
```

## Module Organization

### src.core
- `ViralClipGenerator` - Main clip generation class
- `Speaker` - Speaker data class
- `AutoPeakViralClipper` - Automatic peak detection clipper
- `EnhancedHeuristicPeakDetector` - Peak detection algorithms
- `ViralMoment` - Viral moment data class
- `StorageOptimizer` - Storage management utilities

### src.captions
- `ASSCaptionUpdateSystemV6` - Advanced SubStation caption system
- `generate_ass_subtitles` - ASS subtitle generation function
- `SRTViralCaptionSystem` - SRT caption system
- `fix_caption_fragments` - Caption fixing utilities

### src.routes
- `tiktok_bp` - TikTok integration Flask blueprint

### src.utils
- Various utility functions and helpers

## Migration Examples

### Old import style:
```python
from viral_clipper_complete import ViralClipGenerator
from ass_caption_update_system_v6 import ASSCaptionUpdateSystemV6
```

### New import style:
```python
# Option 1: Direct from module
from src.core.viral_clipper_complete import ViralClipGenerator
from src.captions.ass_caption_update_system_v6 import ASSCaptionUpdateSystemV6

# Option 2: From package
from src.core import ViralClipGenerator
from src.captions import ASSCaptionUpdateSystemV6

# Option 3: From top-level
from src import ViralClipGenerator, ASSCaptionUpdateSystemV6
```

## Best Practices

1. **Be consistent** - Choose one import style and stick to it throughout your project
2. **Use explicit imports** - Avoid `from src import *`
3. **Group imports** - Keep imports organized by source (standard library, third-party, local)
4. **Document complex imports** - Add comments when import paths might be confusing

## Troubleshooting

### ImportError: No module named 'src'
- Ensure you're running from the project root directory
- Check that PYTHONPATH includes the project root
- Verify all `__init__.py` files exist

### AttributeError when importing
- Check the `__all__` exports in `__init__.py` files
- Verify the class/function name is correct
- Ensure the module is properly installed (`pip install -e .`)
