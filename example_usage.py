#!/usr/bin/env python3
"""
Example usage of Smart Markdown Tool
Demonstrates different use cases and configurations
"""

from pathlib import Path
from smart_md_tool import SmartMDTool
import json

def example_basic_usage():
    """Basic usage example - analyze current directory"""
    print("🔧 Example 1: Basic Analysis")
    print("-" * 30)
    
    # Create tool instance for current directory
    tool = SmartMDTool(Path.cwd())
    
    # Run dry-run analysis
    tool.run(dry_run=True, create_backup=False, generate_reports=True)
    print()

def example_custom_config():
    """Example with custom configuration"""
    print("🔧 Example 2: Custom Configuration")
    print("-" * 35)
    
    # Custom configuration for a documentation project
    custom_config = {
        'include_patterns': ['docs/**/*.md', 'README.md'],
        'exclude_patterns': [
            '**/node_modules',
            '**/.git',
            '**/build',
            '**/dist'
        ],
        'link_patterns': [
            r'\[([^\]]*)\]\(([^)]+)\)',  # Standard links
            r'\[API: ([^\]]+)\]\(([^)]+)\)',  # API links
            r'\[Guide: ([^\]]+)\]\(([^)]+)\)'  # Guide links
        ],
        'similarity_threshold': 0.7,  # Higher threshold for docs
        'fix_broken_links': True,
        'fix_mismatched_text': True
    }
    
    tool = SmartMDTool(Path.cwd(), custom_config)
    tool.run(dry_run=True, create_backup=False, generate_reports=True)
    print()

def example_learning_project():
    """Example configuration for learning/tutorial projects"""
    print("🔧 Example 3: Learning Project Setup")
    print("-" * 37)
    
    learning_config = {
        'include_patterns': ['**/*.md'],
        'exclude_patterns': [
            '**/.backup_*',
            '**/__pycache__',
            '**/.git',
            '**/SmartMDTool'  # Exclude the tool directory
        ],
        'link_patterns': [
            r'\[See details in ([^]]+\.md)\]\(([^)]+)\)',
            r'\[See project details in ([^]]+\.md)\]\(([^)]+)\)',
            r'\[([^\]]*)\]\(([^)]+)\)'
        ],
        'similarity_threshold': 0.6,
        'max_backup_files': 200,
        'fix_broken_links': True,
        'fix_mismatched_text': True
    }
    
    # For learning projects, you might want to be in parent directory
    base_path = Path.cwd().parent if Path.cwd().name == 'SmartMDTool' else Path.cwd()
    
    tool = SmartMDTool(base_path, learning_config)
    tool.run(dry_run=True, create_backup=False, generate_reports=True)
    print()

def example_api_documentation():
    """Example for API documentation projects"""
    print("🔧 Example 4: API Documentation")
    print("-" * 33)
    
    api_config = {
        'include_patterns': [
            'api/**/*.md',
            'docs/**/*.md',
            'guides/**/*.md'
        ],
        'exclude_patterns': [
            '**/generated',
            '**/temp',
            '**/.cache'
        ],
        'link_patterns': [
            r'\[([^\]]*)\]\(([^)]+)\)',
            r'\[API Reference: ([^\]]+)\]\(([^)]+)\)',
            r'\[Endpoint: ([^\]]+)\]\(([^)]+)\)'
        ],
        'similarity_threshold': 0.8,  # Very strict for API docs
        'fix_broken_links': True,
        'fix_mismatched_text': False  # Keep original API names
    }
    
    tool = SmartMDTool(Path.cwd(), api_config)
    tool.run(dry_run=True, create_backup=False, generate_reports=True)
    print()

def create_sample_config_files():
    """Create sample configuration files for different project types"""
    print("📄 Creating sample configuration files...")
    
    configs = {
        'documentation_config.json': {
            'include_patterns': ['docs/**/*.md', '*.md'],
            'exclude_patterns': ['**/node_modules', '**/.git', '**/build'],
            'link_patterns': [r'\[([^\]]*)\]\(([^)]+)\)'],
            'similarity_threshold': 0.7,
            'fix_broken_links': True,
            'fix_mismatched_text': True
        },
        'learning_config.json': {
            'include_patterns': ['**/*.md'],
            'exclude_patterns': ['**/.backup_*', '**/__pycache__', '**/.git'],
            'link_patterns': [
                r'\[See details in ([^]]+\.md)\]\(([^)]+)\)',
                r'\[([^\]]*)\]\(([^)]+)\)'
            ],
            'similarity_threshold': 0.6,
            'max_backup_files': 300,
            'fix_broken_links': True,
            'fix_mismatched_text': True
        },
        'api_config.json': {
            'include_patterns': ['api/**/*.md', 'docs/**/*.md'],
            'exclude_patterns': ['**/generated', '**/temp'],
            'link_patterns': [
                r'\[([^\]]*)\]\(([^)]+)\)',
                r'\[API: ([^\]]+)\]\(([^)]+)\)'
            ],
            'similarity_threshold': 0.8,
            'fix_broken_links': True,
            'fix_mismatched_text': False
        }
    }
    
    for filename, config in configs.items():
        config_path = Path.cwd() / filename
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            print(f"  ✅ Created {filename}")
        except Exception as e:
            print(f"  ❌ Failed to create {filename}: {e}")
    
    print()

def main():
    """Run all examples"""
    print("🚀 Smart Markdown Tool - Usage Examples")
    print("=" * 50)
    print()
    
    # Create sample configs first
    create_sample_config_files()
    
    # Run examples
    try:
        example_basic_usage()
        example_custom_config()
        example_learning_project()
        example_api_documentation()
        
        print("🎉 All examples completed!")
        print("📄 Check the generated HTML reports for detailed results.")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print("Make sure smart_md_tool.py is in the same directory.")

if __name__ == "__main__":
    main()
