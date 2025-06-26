# Clippy Repository Structure Migration Guide

This guide helps you reorganize the Clippy repository into a cleaner, more maintainable structure.

## Current Structure → New Structure

### Before:
```
Clippy/
├── app.py
├── auto_peak_viral_clipper.py
├── viral_clipper_complete.py
├── enhanced_heuristic_peak_detector.py
├── ass_caption_update_system_v6.py
├── ass_subtitle_generation.py
├── srt_viral_caption_system.py
├── caption_fragment_fix.py
├── storage_optimizer.py
├── tiktok_routes.py
├── install_deps.py
└── ... (other files)
```

### After:
```
Clippy/
├── app.py
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── auto_peak_viral_clipper.py
│   │   ├── viral_clipper_complete.py
│   │   ├── enhanced_heuristic_peak_detector.py
│   │   └── storage_optimizer.py
│   ├── captions/
│   │   ├── __init__.py
│   │   ├── ass_caption_update_system_v6.py
│   │   ├── ass_subtitle_generation.py
│   │   ├── srt_viral_caption_system.py
│   │   └── caption_fragment_fix.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── tiktok_routes.py
│   └── utils/
│       ├── __init__.py
│       └── install_deps.py
└── ... (other files remain in place)
```

## Migration Steps

### 1. Run the Reorganization Script

```bash
cd /path/to/Clippy
python scripts/reorganize_structure.py
```

This script will:
- Create the new directory structure
- Copy files to their new locations
- Update import statements
- Create README files for each subdirectory

### 2. Manual Updates Required

After running the script, you'll need to:

#### Update app.py imports
The script attempts to update imports automatically, but verify these changes in `app.py`:

```python
# Old imports
from viral_clipper_complete import VirtualClipGenerator
from ass_caption_update_system_v6 import ASSCaptionUpdateSystemV6

# New imports
from src.core.viral_clipper_complete import VirtualClipGenerator
from src.captions.ass_caption_update_system_v6 import ASSCaptionUpdateSystemV6
```

#### Update any configuration files
If you have config files that reference Python modules, update the paths.

#### Update documentation
Update any documentation that references file locations.

### 3. Testing

After migration, test key functionality:

```bash
# Test the main app
python app.py

# Test individual modules
python -m src.core.auto_peak_viral_clipper
python -m src.captions.ass_caption_update_system_v6
```

### 4. Clean Up

Once everything is working:

```bash
# Remove old files from root (BE CAREFUL!)
rm auto_peak_viral_clipper.py
rm viral_clipper_complete.py
rm enhanced_heuristic_peak_detector.py
rm ass_caption_update_system_v6.py
rm ass_subtitle_generation.py
rm srt_viral_caption_system.py
rm caption_fragment_fix.py
rm storage_optimizer.py
rm tiktok_routes.py
rm install_deps.py
```

### 5. Commit Changes

```bash
git add .
git commit -m "Reorganize repository structure with src/ directory"
git push
```

## Benefits of New Structure

1. **Better Organization**: Related files are grouped together
2. **Cleaner Root**: Root directory is less cluttered
3. **Easier Navigation**: Clear separation of concerns
4. **Import Clarity**: Explicit imports show module relationships
5. **Scalability**: Easy to add new modules in appropriate directories

## Troubleshooting

### Import Errors
If you get import errors after migration:

1. Check that all `__init__.py` files exist
2. Verify import statements use the new paths
3. Ensure PYTHONPATH includes the project root

### Missing Files
If files are missing:

1. Check if they were moved to archive/
2. Look in the git history
3. The reorganization script creates copies, so originals should still exist

## Future Considerations

### Version Control
- Remove version numbers from filenames (e.g., `_v6`)
- Use git tags/branches for versioning

### Additional Organization
Consider creating:
- `src/models/` for data models
- `src/api/` for API integrations
- `src/config/` for configuration management

### Build System
Consider adding:
- `setup.py` for package installation
- `requirements.txt` split by environment (dev, prod)
- `Makefile` for common tasks

## Need Help?

If you encounter issues:
1. Check the script output for errors
2. Review git status for uncommitted changes
3. Use git to revert if needed: `git checkout -- .`
