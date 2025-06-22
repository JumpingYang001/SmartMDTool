# Smart Markdown Tool

A powerful, generic tool for analyzing and fixing markdown files across different projects. This tool can identify broken links, mismatched link text, and generate comprehensive HTML and JSON reports.

## Features

🔍 **Comprehensive Analysis**
- Detects broken internal links
- Identifies mismatched link text vs. actual filenames
- Counts words, headings, and images
- Supports custom link patterns

🔧 **Smart Fixing**
- Fuzzy matching to find similar filenames
- Automatic link text correction
- Safe backup creation before making changes
- Configurable fix policies

📊 **Detailed Reporting**
- Beautiful HTML reports with statistics
- JSON reports for programmatic processing
- File-by-file issue breakdown
- Summary statistics and charts

🎯 **Project Agnostic**
- Works with any markdown-based project
- Configurable include/exclude patterns
- Custom link pattern support
- Flexible directory structure handling

## Installation

1. Ensure you have Python 3.7+ installed
2. Copy `smart_md_tool.py` to your project or a central location
3. Make it executable (Unix/Linux/Mac):
   ```bash
   chmod +x smart_md_tool.py
   ```

## Usage

### Basic Usage

```bash
# Analyze current directory (dry run)
python smart_md_tool.py --dry-run

# Analyze specific directory
python smart_md_tool.py /path/to/your/project --dry-run

# Apply fixes with backup
python smart_md_tool.py /path/to/your/project

# Skip backup creation
python smart_md_tool.py /path/to/your/project --no-backup
```

### Advanced Usage

```bash
# Use custom configuration
python smart_md_tool.py --config my_config.json

# Skip report generation
python smart_md_tool.py --no-reports

# Just analyze, don't fix anything
python smart_md_tool.py --dry-run --no-backup
```

### Command Line Options

- `path` - Path to project directory (default: current directory)
- `--config`, `-c` - Path to JSON configuration file
- `--dry-run` - Analyze without making changes
- `--no-backup` - Skip creating backup before fixes
- `--no-reports` - Skip generating HTML/JSON reports
- `--fix-broken-links` - Enable/disable broken link fixing (default: True)
- `--fix-mismatched-text` - Enable/disable text mismatch fixing (default: True)

## Configuration

Create a JSON configuration file to customize behavior:

```json
{
  "include_patterns": ["**/*.md"],
  "exclude_patterns": [
    "**/.backup_*",
    "**/__pycache__",
    "**/.git",
    "**/node_modules"
  ],
  "link_patterns": [
    "\\[([^\\]]*)\\]\\(([^)]+)\\)",
    "\\[See details in ([^]]+\\.md)\\]\\(([^)]+)\\)"
  ],
  "similarity_threshold": 0.6,
  "max_backup_files": 500,
  "fix_broken_links": true,
  "fix_mismatched_text": true
}
```

### Configuration Options

- **include_patterns**: Glob patterns for files to include
- **exclude_patterns**: Glob patterns for files/directories to exclude
- **link_patterns**: Regular expressions to match different link formats
- **similarity_threshold**: Minimum similarity score for fuzzy matching (0.0-1.0)
- **max_backup_files**: Maximum number of files to include in backup
- **fix_broken_links**: Whether to attempt fixing broken links
- **fix_mismatched_text**: Whether to fix mismatched link text

## Output Files

### HTML Report
- Interactive report with statistics and issue details
- File: `md_analysis_report_YYYYMMDD_HHMMSS.html`
- Includes:
  - Summary dashboard
  - File-by-file breakdown
  - Issue details with suggested fixes
  - Statistics and charts

### JSON Report
- Machine-readable analysis results
- File: `md_analysis_report_YYYYMMDD_HHMMSS.json`
- Contains:
  - Complete analysis data
  - Configuration used
  - Timestamps and metadata

### Backup
- Safe backup of all processed markdown files
- Directory: `.backup_smart_md_YYYYMMDD_HHMMSS/`
- Preserves directory structure
- Excludes problematic files/directories

## Examples

### For Documentation Projects
```bash
# Analyze documentation with custom patterns
python smart_md_tool.py ./docs --config docs_config.json
```

### For Learning/Tutorial Projects
```bash
# Process learning materials with fuzzy matching
python smart_md_tool.py ./learning-path --dry-run
```

### For API Documentation
```bash
# Strict analysis for API docs
python smart_md_tool.py ./api-docs --config api_config.json --no-backup
```

### For Large Projects
```bash
# Process with limited backup size
python smart_md_tool.py ./large-project --config large_project_config.json
```

## Link Pattern Matching

The tool supports various link formats:

1. **Standard Markdown Links**
   ```markdown
   [Link Text](relative/path/file.md)
   [External Link](https://example.com)
   ```

2. **Reference-style Links**
   ```markdown
   [See details in file.md](./path/to/file.md)
   [Read more in documentation.md](../docs/documentation.md)
   ```

3. **Custom Patterns** (configurable)
   ```markdown
   [View API Reference](api/reference.md)
   [Check Tutorial](tutorials/getting-started.md)
   ```

## Fuzzy Matching Algorithm

The tool uses intelligent fuzzy matching to find the best file matches:

1. **Number Prefix Matching**: Matches files with same numeric prefix (e.g., `01_Introduction.md`)
2. **Similarity Scoring**: Uses SequenceMatcher for text similarity
3. **Threshold Filtering**: Only suggests matches above similarity threshold
4. **Context Awareness**: Considers directory structure and relative paths

## Error Handling

- **File Access Errors**: Gracefully handles permission issues
- **Encoding Issues**: Supports UTF-8 and fallback encodings
- **Path Resolution**: Handles different path formats and structures
- **Backup Limits**: Prevents excessive backup creation
- **Memory Management**: Processes files efficiently for large projects

## Integration

### Pre-commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: markdown-link-check
        name: Check Markdown Links
        entry: python smart_md_tool.py --dry-run --no-backup --no-reports .
        language: system
        files: '\.md$'
```

### CI/CD Pipeline
```yaml
# GitHub Actions example
- name: Check Markdown Links
  run: |
    python smart_md_tool.py --dry-run --config .github/md_config.json
    if [ $? -ne 0 ]; then
      echo "Markdown link issues found"
      exit 1
    fi
```

### Build Scripts
```bash
#!/bin/bash
# build.sh
echo "Checking markdown files..."
python smart_md_tool.py --dry-run
if [ $? -eq 0 ]; then
    echo "All markdown files are valid"
else
    echo "Please fix markdown issues before building"
    exit 1
fi
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure write permissions for backup directory
   - Run with appropriate user privileges

2. **No Files Found**
   - Check include/exclude patterns
   - Verify working directory

3. **Encoding Errors**
   - Ensure files are UTF-8 encoded
   - Check for BOM markers

4. **Memory Issues**
   - Reduce max_backup_files limit
   - Process smaller directory subsets

### Debug Mode
Set environment variable for verbose output:
```bash
export SMART_MD_DEBUG=1
python smart_md_tool.py --dry-run
```

## Contributing

Feel free to extend the tool for your specific needs:

1. **Custom Link Patterns**: Add regex patterns for your link formats
2. **Additional Checks**: Extend analysis to check for other issues
3. **Output Formats**: Add support for other report formats
4. **Integration**: Create plugins for your favorite tools

## License

This tool is provided as-is for educational and productivity purposes. Feel free to modify and distribute according to your needs.

## Changelog

### Version 1.0.0
- Initial release
- Basic link analysis and fixing
- HTML and JSON report generation
- Configurable patterns and thresholds
- Safe backup creation
- Fuzzy matching algorithm
