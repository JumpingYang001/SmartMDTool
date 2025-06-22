#!/usr/bin/env python3
"""
Smart Markdown Tool
A generic tool for analyzing and fixing markdown files across different projects.
Includes HTML report generation for comprehensive analysis.
"""

import os
import re
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict

@dataclass
class LinkIssue:
    """Represents a link issue found in a markdown file."""
    file_path: str
    line_number: int
    issue_type: str  # 'broken_link', 'mismatched_text', 'invalid_format'
    original_text: str
    original_link: str
    suggested_fix: Optional[str] = None
    description: str = ""

@dataclass
class FileAnalysis:
    """Represents analysis results for a single file."""
    file_path: str
    total_links: int
    broken_links: int
    mismatched_text: int
    invalid_format: int
    issues: List[LinkIssue]
    word_count: int
    heading_count: int
    image_count: int

class SmartMDTool:
    def __init__(self, base_path: Path, config: Dict[str, Any] = None):
        self.base_path = base_path
        self.config = config or self.default_config()
        self.analysis_results: List[FileAnalysis] = []
        self.fixes_applied = 0
        
    def default_config(self) -> Dict[str, Any]:
        """Default configuration for the tool."""
        return {
            'include_patterns': ['**/*.md'],
            'exclude_patterns': [
                '**/.backup_*',
                '**/__pycache__',
                '**/.git',
                '**/.vscode',
                '**/node_modules',
                '**/.env',
                '**/*.pyc',
                '**/*.pyo'
            ],
            'link_patterns': [
                r'\[([^\]]*)\]\(([^)]+)\)',  # Standard markdown links
                r'\[See details in ([^]]+\.md)\]\(([^)]+)\)',  # Specific pattern
                r'\[See project details in ([^]]+\.md)\]\(([^)]+)\)'  # Another pattern
            ],
            'similarity_threshold': 0.6,
            'max_backup_files': 500,
            'generate_report': True,
            'fix_broken_links': True,
            'fix_mismatched_text': True
        }
    
    def similarity(self, a: str, b: str) -> float:
        """Calculate similarity between two strings."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if a file should be excluded based on patterns."""
        file_str = str(file_path).replace('\\', '/')
        
        for pattern in self.config['exclude_patterns']:
            if pattern.startswith('**/'):
                pattern = pattern[3:]
                if pattern in file_str:
                    return True
            elif file_str.endswith(pattern) or pattern in file_str:
                return True
        return False
    
    def find_markdown_files(self) -> List[Path]:
        """Find all markdown files that should be processed."""
        md_files = []
        
        for pattern in self.config['include_patterns']:
            for file_path in self.base_path.glob(pattern):
                if file_path.is_file() and not self.should_exclude_file(file_path):
                    md_files.append(file_path)
        
        return sorted(set(md_files))
    
    def extract_number_and_base(self, filename: str) -> Tuple[Optional[str], str]:
        """Extract number prefix and base name from filename."""
        match = re.match(r'^(\d+)_(.+)\.md$', filename)
        if match:
            return match.group(1), match.group(2)
        return None, filename.replace('.md', '')
    
    def find_best_file_match(self, expected_filename: str, search_dir: Path) -> Optional[Path]:
        """Find the best matching file using fuzzy matching logic."""
        if not search_dir.exists():
            return None
        
        expected_number, expected_base = self.extract_number_and_base(expected_filename)
        
        md_files = [f for f in os.listdir(search_dir) 
                   if f.endswith('.md') and f.lower() != 'readme.md']
          # First, try to find files with the same number prefix
        if expected_number:
            same_number_files = []
            for f in md_files:
                file_number, _ = self.extract_number_and_base(f)
                if file_number == expected_number:
                    same_number_files.append(f)
            
            if len(same_number_files) == 1:
                return search_dir / same_number_files[0]
        
        # If no unique number match, use similarity matching
        best_match = None
        best_score = 0.0
        threshold = self.config['similarity_threshold']
        
        for file in md_files:
            score = self.similarity(expected_filename, file)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = file
        
        return search_dir / best_match if best_match else None
    
    def is_likely_markdown_link(self, link_text: str, link_url: str, line: str) -> bool:
        """Check if a matched pattern is likely a real markdown link vs code."""
        # Skip if inside code blocks or inline code
        if '`' in line:
            # Check if the match is inside backticks
            match_pos = line.find(f'[{link_text}]({link_url})')
            if match_pos != -1:
                before_match = line[:match_pos]
                after_match = line[match_pos + len(f'[{link_text}]({link_url})'):]
                
                # Count backticks before and after the match
                backticks_before = before_match.count('`')
                backticks_after = after_match.count('`')
                
                # If odd number of backticks before, we're inside inline code
                if backticks_before % 2 == 1:
                    return False
        
        # URLs, file paths, and anchors are definitely real links
        if any(link_url.startswith(prefix) for prefix in ['http://', 'https://', 'ftp://', 'mailto:', '#', './', '../', '/']):
            return True
        
        # File extensions indicate real links
        if any(link_url.endswith(ext) for ext in ['.md', '.html', '.pdf', '.txt', '.doc', '.docx', '.png', '.jpg', '.gif']):
            return True
        
        # If it looks like a file path (contains / or \)
        if '/' in link_url or '\\' in link_url:
            return True
        
        # If link_url contains spaces AND commas/multiple words, it's probably code parameters
        if ' ' in link_url and (',' in link_url or len(link_url.split()) > 2):
            return False
        
        # Skip obvious code patterns
        code_patterns = [
            r'^int\s+\w+',  # int variable declarations
            r'^\w+\s*\(',   # function calls at start
            r'^\w+::\w+',   # C++ scope resolution at start
            r'^[a-zA-Z_]\w*\s*[&*]',  # C/C++ reference/pointer at start
        ]
        
        for pattern in code_patterns:
            if re.match(pattern, link_url):
                return False
        
        # Default to True for other cases
        return True
    
    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analyze a single markdown file for issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            return FileAnalysis(
                file_path=str(file_path),
                total_links=0, broken_links=0, mismatched_text=0,
                invalid_format=0, issues=[], word_count=0,
                heading_count=0, image_count=0
            )
        
        issues = []
        total_links = 0
        broken_links = 0
        mismatched_text = 0
        invalid_format = 0
        
        lines = content.split('\n')
        in_code_block = False
        
        # Analyze links
        for pattern in self.config['link_patterns']:
            for line_num, line in enumerate(lines, 1):
                # Track code blocks
                if line.strip().startswith('```'):
                    in_code_block = not in_code_block
                    continue
                
                # Skip lines inside code blocks
                if in_code_block:
                    continue
                
                for match in re.finditer(pattern, line):
                    link_text = match.group(1) if match.groups() else ""
                    link_url = match.group(2) if len(match.groups()) > 1 else match.group(1)
                    
                    # Filter out non-link patterns
                    if not self.is_likely_markdown_link(link_text, link_url, line):
                        continue
                    
                    total_links += 1
                    
                    # Check if link is broken
                    full_target_path = self.resolve_link_path(file_path, link_url)
                    
                    if full_target_path and not full_target_path.exists():
                        broken_links += 1
                        suggested_fix = self.suggest_link_fix(file_path, link_text, link_url)
                        issues.append(LinkIssue(
                            file_path=str(file_path),
                            line_number=line_num,
                            issue_type='broken_link',
                            original_text=link_text,
                            original_link=link_url,
                            suggested_fix=suggested_fix,
                            description=f"Link target does not exist: {link_url}"
                        ))
                      # Check for mismatched text (for file links)
                    elif full_target_path and full_target_path.exists() and link_text.endswith('.md'):
                        actual_filename = full_target_path.name
                        # Only flag as mismatched if the link text doesn't match the actual filename
                        # and it's not just a "See details in filename.md" pattern where filename matches
                        is_see_details_pattern = link_text.startswith('See details in ') or link_text.startswith('See project details in ')
                        if is_see_details_pattern:
                            # Extract just the filename from "See details in filename.md"
                            extracted_filename = link_text.split(' in ')[-1] if ' in ' in link_text else link_text
                            if extracted_filename != actual_filename:
                                mismatched_text += 1
                                issues.append(LinkIssue(
                                    file_path=str(file_path),
                                    line_number=line_num,
                                    issue_type='mismatched_text',
                                    original_text=link_text,
                                    original_link=link_url,
                                    suggested_fix=f"See details in {actual_filename}" if link_text.startswith('See details in ') else f"See project details in {actual_filename}",
                                    description=f"Link text filename '{extracted_filename}' doesn't match actual filename '{actual_filename}'"
                                ))
                        elif link_text != actual_filename:
                            mismatched_text += 1
                            issues.append(LinkIssue(
                                file_path=str(file_path),
                                line_number=line_num,
                                issue_type='mismatched_text',
                                original_text=link_text,
                                original_link=link_url,
                                suggested_fix=actual_filename,
                                description=f"Link text '{link_text}' doesn't match filename '{actual_filename}'"
                            ))
        
        # Count other elements
        word_count = len(content.split())
        heading_count = len(re.findall(r'^#+\s', content, re.MULTILINE))
        image_count = len(re.findall(r'!\[.*?\]\(.*?\)', content))
        
        return FileAnalysis(
            file_path=str(file_path),
            total_links=total_links,
            broken_links=broken_links,
            mismatched_text=mismatched_text,
            invalid_format=invalid_format,
            issues=issues,
            word_count=word_count,
            heading_count=heading_count,
            image_count=image_count        )
    
    def resolve_link_path(self, file_path: Path, link_url: str) -> Optional[Path]:
        """Resolve a link URL to an absolute path."""
        if link_url.startswith(('http://', 'https://', 'mailto:', '#')):
            return None  # External link or anchor
        
        try:
            if link_url.startswith('/'):
                return self.base_path / link_url.lstrip('/')
            else:
                return file_path.parent / link_url
        except Exception:
            return None
    
    def suggest_link_fix(self, file_path: Path, link_text: str, link_url: str) -> Optional[str]:
        """Suggest a fix for a broken link."""
        link_path = Path(link_url)
        target_dir = file_path.parent / link_path.parent
        expected_filename = link_path.name
        
        if not target_dir.exists():
            return None
        
        # First try exact match
        correct_file = self.find_best_file_match(expected_filename, target_dir)
        
        if correct_file and correct_file.exists():
            try:
                relative_path = correct_file.relative_to(file_path.parent)
                return str(relative_path).replace('\\', '/')
            except Exception:
                pass
        
        # If no match found, try variations of the filename
        # Handle common naming convention differences
        if not correct_file:
            variations = []
            base_name = expected_filename.replace('.md', '')
            
            # Try replacing hyphens with underscores and vice versa
            if '-' in base_name:
                variations.append(base_name.replace('-', '_') + '.md')
            if '_' in base_name:
                variations.append(base_name.replace('_', '-') + '.md')
            
            # Try variations with different case
            variations.extend([
                base_name.lower() + '.md',
                base_name.upper() + '.md',
                base_name.title().replace(' ', '_') + '.md',
                base_name.title().replace(' ', '-') + '.md'
            ])
            
            for variation in variations:
                test_file = target_dir / variation
                if test_file.exists():
                    try:
                        relative_path = test_file.relative_to(file_path.parent)
                        return str(relative_path).replace('\\', '/')
                    except Exception:
                        continue
        
        return None
    
    def create_backup(self) -> Optional[Path]:
        """Create a backup of markdown files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.base_path / f".backup_smart_md_{timestamp}"
        
        print(f"📦 Creating backup in {backup_dir.name}...")
        
        file_count = 0
        md_files = self.find_markdown_files()
        
        for file_path in md_files:
            if file_count >= self.config['max_backup_files']:
                print(f"⚠️  Backup limited to {self.config['max_backup_files']} files")
                break
            
            try:
                relative_path = file_path.relative_to(self.base_path)
                backup_file = backup_dir / relative_path
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, backup_file)
                file_count += 1
            except Exception as e:
                print(f"⚠️  Skipped {file_path}: {e}")
        
        print(f"✅ Backup created: {backup_dir.name} ({file_count} files)")
        return backup_dir
    
    def apply_fixes(self, file_analysis: FileAnalysis, dry_run: bool = True) -> int:
        """Apply fixes to a file based on analysis results."""
        if not file_analysis.issues:
            return 0
        
        fixes_applied = 0
        file_path = Path(file_analysis.file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            return 0
        
        original_content = content
        
        for issue in file_analysis.issues:
            if issue.suggested_fix is None:
                continue
            
            if issue.issue_type == 'broken_link' and self.config['fix_broken_links']:
                # Fix broken links
                old_pattern = f"[{issue.original_text}]({issue.original_link})"
                new_pattern = f"[{issue.original_text}]({issue.suggested_fix})"
                if old_pattern in content:
                    content = content.replace(old_pattern, new_pattern)
                    fixes_applied += 1
                    if not dry_run:
                        print(f"    🔧 Fixed broken link: {issue.original_link} -> {issue.suggested_fix}")
            
            elif issue.issue_type == 'mismatched_text' and self.config['fix_mismatched_text']:
                # Fix mismatched text
                old_pattern = f"[{issue.original_text}]({issue.original_link})"
                new_pattern = f"[{issue.suggested_fix}]({issue.original_link})"
                if old_pattern in content:
                    content = content.replace(old_pattern, new_pattern)
                    fixes_applied += 1
                    if not dry_run:
                        print(f"    🔧 Fixed text mismatch: {issue.original_text} -> {issue.suggested_fix}")
        
        # Write changes if not dry run and changes were made
        if not dry_run and content != original_content:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"    ✅ Updated {file_path.name}")
            except Exception as e:
                print(f"    ❌ Error writing {file_path}: {e}")
                return 0
        
        return fixes_applied
    
    def generate_html_report(self, output_path: Path) -> None:
        """Generate an HTML report of the analysis results."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        total_files = len(self.analysis_results)
        total_issues = sum(len(analysis.issues) for analysis in self.analysis_results)
        total_links = sum(analysis.total_links for analysis in self.analysis_results)
        total_broken = sum(analysis.broken_links for analysis in self.analysis_results)
        total_mismatched = sum(analysis.mismatched_text for analysis in self.analysis_results)
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Markdown Tool Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
        .card {{ background: #fff; border: 1px solid #ddd; border-radius: 5px; padding: 15px; text-align: center; }}
        .card h3 {{ margin: 0 0 10px 0; color: #333; }}
        .card .number {{ font-size: 2em; font-weight: bold; }}
        .card.error .number {{ color: #e74c3c; }}
        .card.warning .number {{ color: #f39c12; }}
        .card.success .number {{ color: #27ae60; }}
        .card.info .number {{ color: #3498db; }}
        
        .file-section {{ margin-bottom: 30px; border: 1px solid #ddd; border-radius: 5px; }}
        .file-header {{ background: #f8f9fa; padding: 15px; border-bottom: 1px solid #ddd; }}
        .file-header h3 {{ margin: 0; color: #333; }}
        .file-stats {{ display: flex; gap: 20px; margin-top: 10px; }}
        .file-stats span {{ background: #e9ecef; padding: 5px 10px; border-radius: 3px; font-size: 0.9em; }}
        
        .issues-list {{ padding: 15px; }}
        .issue {{ background: #fff; border-left: 4px solid #e74c3c; padding: 10px; margin-bottom: 10px; }}
        .issue.warning {{ border-left-color: #f39c12; }}
        .issue-type {{ font-weight: bold; text-transform: uppercase; font-size: 0.8em; }}
        .issue-description {{ margin: 5px 0; }}
        .issue-details {{ font-family: monospace; background: #f8f9fa; padding: 5px; border-radius: 3px; font-size: 0.9em; }}
        .suggested-fix {{ color: #27ae60; font-weight: bold; }}
        
        .no-issues {{ text-align: center; padding: 20px; color: #666; }}
        .footer {{ margin-top: 40px; text-align: center; color: #666; font-size: 0.9em; }}
        
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        tr:hover {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔧 Smart Markdown Tool Report</h1>
        <p>Generated on {timestamp}</p>
        <p>Base Path: <code>{self.base_path}</code></p>
    </div>
    
    <div class="summary">
        <div class="card info">
            <h3>Files Analyzed</h3>
            <div class="number">{total_files}</div>
        </div>
        <div class="card info">
            <h3>Total Links</h3>
            <div class="number">{total_links}</div>
        </div>
        <div class="card error">
            <h3>Broken Links</h3>
            <div class="number">{total_broken}</div>
        </div>
        <div class="card warning">
            <h3>Mismatched Text</h3>
            <div class="number">{total_mismatched}</div>
        </div>
        <div class="card {'error' if total_issues > 0 else 'success'}">
            <h3>Total Issues</h3>
            <div class="number">{total_issues}</div>
        </div>
    </div>
"""
        
        if self.analysis_results:
            html_content += """
    <h2>📊 Files Overview</h2>
    <table>
        <thead>
            <tr>
                <th>File</th>
                <th>Links</th>
                <th>Issues</th>
                <th>Words</th>
                <th>Headings</th>
                <th>Images</th>
            </tr>
        </thead>
        <tbody>
"""
            
            for analysis in self.analysis_results:
                relative_path = Path(analysis.file_path).relative_to(self.base_path)
                issue_count = len(analysis.issues)
                row_class = "error" if issue_count > 0 else ""
                
                html_content += f"""
            <tr class="{row_class}">
                <td><code>{relative_path}</code></td>
                <td>{analysis.total_links}</td>
                <td>{issue_count}</td>
                <td>{analysis.word_count}</td>
                <td>{analysis.heading_count}</td>
                <td>{analysis.image_count}</td>
            </tr>
"""
            
            html_content += """
        </tbody>
    </table>
"""
        
        # Detailed issues for each file
        html_content += "<h2>🔍 Detailed Issues</h2>"
        
        files_with_issues = [a for a in self.analysis_results if a.issues]
        
        if not files_with_issues:
            html_content += '<div class="no-issues">🎉 No issues found in any files!</div>'
        else:
            for analysis in files_with_issues:
                relative_path = Path(analysis.file_path).relative_to(self.base_path)
                
                html_content += f"""
    <div class="file-section">
        <div class="file-header">
            <h3>📄 {relative_path}</h3>
            <div class="file-stats">
                <span>Links: {analysis.total_links}</span>
                <span>Issues: {len(analysis.issues)}</span>
                <span>Words: {analysis.word_count}</span>
            </div>
        </div>
        <div class="issues-list">
"""
                
                for issue in analysis.issues:
                    issue_class = "warning" if issue.issue_type == "mismatched_text" else "issue"
                    
                    html_content += f"""
            <div class="{issue_class}">
                <div class="issue-type">{issue.issue_type.replace('_', ' ')}</div>
                <div class="issue-description">{issue.description}</div>
                <div class="issue-details">
                    Line {issue.line_number}: <strong>{issue.original_text}</strong> → <code>{issue.original_link}</code>
"""
                    
                    if issue.suggested_fix:
                        html_content += f'<br>Suggested fix: <span class="suggested-fix">{issue.suggested_fix}</span>'
                    
                    html_content += """
                </div>
            </div>
"""
                
                html_content += """
        </div>
    </div>
"""
        
        html_content += f"""
    <div class="footer">
        <p>Generated by Smart Markdown Tool | {timestamp}</p>
    </div>
</body>
</html>
"""
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"📄 HTML report generated: {output_path}")
        except Exception as e:
            print(f"❌ Error generating HTML report: {e}")
    
    def generate_json_report(self, output_path: Path) -> None:
        """Generate a JSON report of the analysis results."""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'base_path': str(self.base_path),
            'config': self.config,
            'summary': {
                'total_files': len(self.analysis_results),
                'total_links': sum(a.total_links for a in self.analysis_results),
                'total_issues': sum(len(a.issues) for a in self.analysis_results),
                'broken_links': sum(a.broken_links for a in self.analysis_results),
                'mismatched_text': sum(a.mismatched_text for a in self.analysis_results),
                'fixes_applied': self.fixes_applied
            },
            'files': [asdict(analysis) for analysis in self.analysis_results]
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"📄 JSON report generated: {output_path}")
        except Exception as e:
            print(f"❌ Error generating JSON report: {e}")
    
    def run(self, dry_run: bool = True, create_backup: bool = True, 
            generate_reports: bool = True) -> None:
        """Run the complete analysis and fixing process."""
        print("🚀 Smart Markdown Tool")
        print("=" * 50)
        print(f"Working directory: {self.base_path}")
        
        # Find markdown files
        md_files = self.find_markdown_files()
        print(f"📄 Found {len(md_files)} markdown files")
        
        if not md_files:
            print("❌ No markdown files found to process")
            return
        
        # Create backup if requested
        backup_dir = None
        if create_backup and not dry_run:
            backup_dir = self.create_backup()
        
        # Analyze files
        print("\n🔍 Analyzing files...")
        for file_path in md_files:
            print(f"  📄 Analyzing {file_path.name}...")
            analysis = self.analyze_file(file_path)
            self.analysis_results.append(analysis)
        
        # Summary
        total_issues = sum(len(a.issues) for a in self.analysis_results)
        print(f"\n📊 Analysis Summary:")
        print(f"  Files processed: {len(self.analysis_results)}")
        print(f"  Total issues found: {total_issues}")
        
        if total_issues == 0:
            print("  🎉 No issues found!")
        else:
            broken_links = sum(a.broken_links for a in self.analysis_results)
            mismatched_text = sum(a.mismatched_text for a in self.analysis_results)
            print(f"  🔗 Broken links: {broken_links}")
            print(f"  📝 Mismatched text: {mismatched_text}")
        
        # Apply fixes if not dry run
        if not dry_run and total_issues > 0:
            print("\n🔧 Applying fixes...")
            for analysis in self.analysis_results:
                if analysis.issues:
                    print(f"  🔧 Fixing {Path(analysis.file_path).name}...")
                    fixes = self.apply_fixes(analysis, dry_run=False)
                    self.fixes_applied += fixes
            
            print(f"✅ Applied {self.fixes_applied} fixes")
        
        # Generate reports
        if generate_reports:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # HTML Report
            html_report_path = self.base_path / f"md_analysis_report_{timestamp}.html"
            self.generate_html_report(html_report_path)
            
            # JSON Report
            json_report_path = self.base_path / f"md_analysis_report_{timestamp}.json"
            self.generate_json_report(json_report_path)
        
        print(f"\n🎉 Process completed!")
        if backup_dir:
            print(f"📦 Backup: {backup_dir.name}")

def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from a JSON file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Could not load config from {config_path}: {e}")
        return {}

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Smart Markdown Tool - Analyze and fix markdown files")
    parser.add_argument("path", nargs="?", default=".", 
                       help="Path to the project directory (default: current directory)")
    parser.add_argument("--config", "-c", type=str, 
                       help="Path to configuration file (JSON)")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Run analysis without making changes")
    parser.add_argument("--no-backup", action="store_true", 
                       help="Skip creating backup")
    parser.add_argument("--no-reports", action="store_true", 
                       help="Skip generating reports")
    parser.add_argument("--fix-broken-links", action="store_true", default=True,
                       help="Fix broken links (default: True)")
    parser.add_argument("--fix-mismatched-text", action="store_true", default=True,
                       help="Fix mismatched link text (default: True)")
    
    args = parser.parse_args()
    
    # Resolve path
    base_path = Path(args.path).resolve()
    
    if not base_path.exists():
        print(f"❌ Path does not exist: {base_path}")
        return
    
    # Load configuration
    config = {}
    if args.config:
        config = load_config(Path(args.config))
    
    # Create tool instance
    tool = SmartMDTool(base_path, config)
    
    # Override config with command line arguments
    if hasattr(args, 'fix_broken_links'):
        tool.config['fix_broken_links'] = args.fix_broken_links
    if hasattr(args, 'fix_mismatched_text'):
        tool.config['fix_mismatched_text'] = args.fix_mismatched_text
    
    # Run the tool
    tool.run(
        dry_run=args.dry_run,
        create_backup=not args.no_backup,
        generate_reports=not args.no_reports
    )

if __name__ == "__main__":
    main()
