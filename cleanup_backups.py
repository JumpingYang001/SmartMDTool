#!/usr/bin/env python3
"""
Backup Cleanup Utility
Safely removes problematic backup directories.
"""

import shutil
import os
from pathlib import Path

def find_problematic_backups(base_path):
    """Find backup directories that might be problematic."""
    problematic = []
    
    # Check in base directory and immediate subdirectories
    search_paths = [base_path]
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith('.git'):
            search_paths.append(item)
    
    for search_path in search_paths:
        try:
            for item in search_path.iterdir():
                if item.is_dir() and '.backup_' in item.name:
                    # Check if it's huge or contains loops
                    try:
                        # Quick check - if it's too deep or has too many files, it's problematic
                        file_count = sum(1 for _ in item.rglob('*') if _.is_file())
                        if file_count > 100:  # Lower threshold for problematic backup
                            problematic.append((item, file_count))
                        else:
                            problematic.append((item, file_count))  # Include all backup dirs
                    except Exception as e:
                        problematic.append((item, f"Error: {e}"))
        except PermissionError:
            continue
    
    return problematic

def safe_remove_directory(dir_path):
    """Safely remove a directory with error handling."""
    try:
        print(f"🗑️  Removing {dir_path.name}...")
        
        # First try normal removal
        shutil.rmtree(dir_path)
        print(f"✅ Successfully removed {dir_path.name}")
        return True
        
    except PermissionError:
        print(f"❌ Permission denied removing {dir_path.name}")
        print("   Try running as administrator or use File Explorer")
        return False
        
    except Exception as e:
        print(f"❌ Error removing {dir_path.name}: {e}")
        return False

def main():
    """Main cleanup function."""
    # Work from the parent directory
    script_dir = Path(__file__).parent
    base_path = script_dir.parent
    
    print("🧹 Backup Cleanup Utility")
    print("=" * 50)
    print(f"Scanning: {base_path}")
    
    # Find problematic backups
    problematic = find_problematic_backups(base_path)
    
    if not problematic:
        print("✅ No problematic backup directories found")
        return
    
    print(f"\n🚨 Found {len(problematic)} problematic backup directories:")
    for i, (backup_dir, info) in enumerate(problematic, 1):
        print(f"  {i}. {backup_dir.name}")
        if isinstance(info, int):
            print(f"     Size: {info} files")
        else:
            print(f"     Status: {info}")
    
    # Ask for confirmation
    response = input("\n❓ Remove these directories? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Cleanup cancelled")
        return
    
    # Remove directories
    success_count = 0
    for backup_dir, _ in problematic:
        if safe_remove_directory(backup_dir):
            success_count += 1
    
    print(f"\n🎉 Cleanup complete: {success_count}/{len(problematic)} directories removed")
    
    if success_count < len(problematic):
        print("\n💡 For directories that couldn't be removed:")
        print("   1. Close any open files in those directories")
        print("   2. Run this script as administrator")
        print("   3. Use File Explorer to delete manually")

if __name__ == "__main__":
    main()
