#!/usr/bin/env python3
"""
Script to reorganize Clippy repository structure
Moves files from root to organized src/ subdirectories
"""

import os
import shutil
from pathlib import Path

# Define the file mapping
FILE_MAPPING = {
    # Core processing files
    'src/core/': [
        'auto_peak_viral_clipper.py',
        'viral_clipper_complete.py',
        'enhanced_heuristic_peak_detector.py',
        'storage_optimizer.py'
    ],
    
    # Caption-related modules
    'src/captions/': [
        'ass_caption_update_system_v6.py',
        'ass_subtitle_generation.py',
        'srt_viral_caption_system.py',
        'caption_fragment_fix.py'
    ],
    
    # Route handlers
    'src/routes/': [
        'tiktok_routes.py'
    ],
    
    # Utility functions
    'src/utils/': [
        'install_deps.py'
    ]
}

def create_directories():
    """Create the src directory structure"""
    print("Creating directory structure...")
    for dir_path in FILE_MAPPING.keys():
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created {dir_path}")

def move_files():
    """Move files to their new locations"""
    print("\nMoving files...")
    moved_files = []
    
    for target_dir, files in FILE_MAPPING.items():
        for file_name in files:
            source_path = Path(file_name)
            target_path = Path(target_dir) / file_name
            
            if source_path.exists():
                try:
                    shutil.copy2(source_path, target_path)
                    moved_files.append((file_name, target_dir))
                    print(f"✓ Moved {file_name} → {target_dir}")
                except Exception as e:
                    print(f"✗ Error moving {file_name}: {e}")
            else:
                print(f"⚠ File not found: {file_name}")
    
    return moved_files

def update_imports_in_file(file_path, import_mappings):
    """Update import statements in a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update imports
        for old_import, new_import in import_mappings.items():
            content = content.replace(old_import, new_import)
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error updating imports in {file_path}: {e}")
        return False

def update_imports():
    """Update import statements in all Python files"""
    print("\nUpdating import statements...")
    
    # Define import mappings
    import_mappings = {
        'from viral_clipper_complete import': 'from src.core.viral_clipper_complete import',
        'from enhanced_heuristic_peak_detector import': 'from src.core.enhanced_heuristic_peak_detector import',
        'from ass_caption_update_system_v6 import': 'from src.captions.ass_caption_update_system_v6 import',
        'from ass_subtitle_generation import': 'from src.captions.ass_subtitle_generation import',
        'from srt_viral_caption_system import': 'from src.captions.srt_viral_caption_system import',
        'from caption_fragment_fix import': 'from src.captions.caption_fragment_fix import',
        'from storage_optimizer import': 'from src.core.storage_optimizer import',
        'from tiktok_routes import': 'from src.routes.tiktok_routes import',
        'import viral_clipper_complete': 'import src.core.viral_clipper_complete',
        'import enhanced_heuristic_peak_detector': 'import src.core.enhanced_heuristic_peak_detector',
        'import ass_caption_update_system_v6': 'import src.captions.ass_caption_update_system_v6',
        'import ass_subtitle_generation': 'import src.captions.ass_subtitle_generation',
        'import srt_viral_caption_system': 'import src.captions.srt_viral_caption_system',
        'import caption_fragment_fix': 'import src.captions.caption_fragment_fix',
        'import storage_optimizer': 'import src.core.storage_optimizer',
        'import tiktok_routes': 'import src.routes.tiktok_routes',
    }
    
    # Update imports in app.py
    if update_imports_in_file('app.py', import_mappings):
        print("✓ Updated imports in app.py")
    
    # Update imports in all moved files
    for target_dir, files in FILE_MAPPING.items():
        for file_name in files:
            file_path = Path(target_dir) / file_name
            if file_path.exists() and update_imports_in_file(file_path, import_mappings):
                print(f"✓ Updated imports in {file_path}")

def create_readme_files():
    """Create README files for each subdirectory"""
    print("\nCreating README files...")
    
    readmes = {
        'src/core/README.md': """# Core Processing Modules

This directory contains the main processing engines for Clippy:

- `auto_peak_viral_clipper.py` - Automatic peak detection and viral clip generation
- `viral_clipper_complete.py` - Complete viral clip generation system
- `enhanced_heuristic_peak_detector.py` - Advanced heuristic-based peak detection
- `storage_optimizer.py` - Storage optimization utilities
""",
        'src/captions/README.md': """# Caption Processing Modules

This directory contains all caption-related functionality:

- `ass_caption_update_system_v6.py` - ASS subtitle system with speech synchronization
- `ass_subtitle_generation.py` - ASS subtitle generation utilities
- `srt_viral_caption_system.py` - SRT subtitle system for viral captions
- `caption_fragment_fix.py` - Caption fragment fixing utilities
""",
        'src/routes/README.md': """# Route Handlers

This directory contains Flask route handlers:

- `tiktok_routes.py` - TikTok integration routes
""",
        'src/utils/README.md': """# Utility Functions

This directory contains utility functions and helpers:

- `install_deps.py` - Dependency installation script
"""
    }
    
    for readme_path, content in readmes.items():
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Created {readme_path}")
        except Exception as e:
            print(f"✗ Error creating {readme_path}: {e}")

def main():
    """Main function to reorganize the repository"""
    print("🎯 Clippy Repository Reorganization Script")
    print("=" * 50)
    
    # Create directories
    create_directories()
    
    # Move files
    moved_files = move_files()
    
    # Update imports
    update_imports()
    
    # Create README files
    create_readme_files()
    
    print("\n✅ Reorganization complete!")
    print(f"Moved {len(moved_files)} files to new structure")
    
    # Show summary
    print("\nNew structure:")
    print("src/")
    print("├── __init__.py")
    print("├── core/          # Main processing files")
    print("├── captions/      # Caption-related modules")
    print("├── routes/        # Route handlers")
    print("└── utils/         # Utility functions")
    
    print("\n⚠️  Note: Remember to:")
    print("1. Test all functionality after reorganization")
    print("2. Update any configuration files that reference old paths")
    print("3. Commit and push changes to git")
    print("4. Update documentation if needed")

if __name__ == "__main__":
    main()
