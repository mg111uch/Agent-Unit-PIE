"""
Main entry point for Codebase Atlas.

Orchestrates the complete pipeline:
1. Scan files
2. Parse files (Python, JS, HTML, configs)
3. Analyze dependencies and impact
4. Generate atlas files (base.md + children/*.md)
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from .config import AtlasConfig, get_default_config, validate_config
from .models import AtlasData
from .scanner import FileScanner
from .parsers import (
    PythonParser, JavaScriptParser, ConfigParser, HTMLParser
)
from .analyzers import (
    DependencyAnalyzer, ImpactAnalyzer, EntryPointDetector
)
from .generators import BaseGenerator, DetailGenerator
from .utils import ensure_directory


def generate_atlas(
    project_dir: str,
    output_dir: str,
    config: Optional[AtlasConfig] = None
) -> AtlasData:
    """
    Generate complete codebase atlas.
    
    Args:
        project_dir: Path to project directory to analyze
        output_dir: Path to output directory for atlas files
        config: Atlas configuration (uses default if None)
    
    Returns:
        AtlasData containing complete analysis
    
    Raises:
        ValueError: If configuration is invalid
        FileNotFoundError: If project directory doesn't exist
    """
    # Use default config if not provided
    if config is None:
        config = get_default_config()
    
    # Update config paths
    config.project_dir = project_dir
    config.output_dir = output_dir
    
    # Validate config
    validate_config(config)
    
    # Validate project directory
    if not Path(project_dir).exists():
        raise FileNotFoundError(f"Project directory not found: {project_dir}")
    
    print("=" * 60)
    print("🗺️  CODEBASE ATLAS GENERATOR")
    print("=" * 60)
    print(f"Project: {project_dir}")
    print(f"Output:  {output_dir}")
    print(f"Mode:    {'Verbose' if config.verbose_mode else 'Compact'}")
    print("=" * 60)
    print()
    
    # Initialize atlas data
    atlas_data = AtlasData()
    
    try:
        # Phase 1: Scan files
        print("📋 PHASE 1: File Discovery")
        print("-" * 60)
        scanner = FileScanner(config)
        files = scanner.scan()
        scanner.print_statistics()
        print()
        
        # Add files to atlas data
        for file in files:
            atlas_data.add_file(file)
        
        # Phase 2: Parse files
        print("📋 PHASE 2: Code Analysis")
        print("-" * 60)
        parsers = {
            'python': PythonParser(config),
            'javascript': JavaScriptParser(config),
            'config': ConfigParser(config),
            'html': HTMLParser(config),
        }
        
        parse_count = 0
        error_count = 0
        
        for file_info in files:
            # Find appropriate parser
            parser = None
            if parsers['python'].can_parse(file_info):
                parser = parsers['python']
            elif parsers['javascript'].can_parse(file_info):
                parser = parsers['javascript']
            elif parsers['config'].can_parse(file_info):
                parser = parsers['config']
            elif parsers['html'].can_parse(file_info):
                parser = parsers['html']
            
            # Parse file
            if parser:
                try:
                    parser.parse(file_info)
                    parse_count += 1
                except Exception as e:
                    file_info.error = f"Parser error: {str(e)}"
                    error_count += 1
        
        print(f"✓ Parsed {parse_count} files")
        if error_count > 0:
            print(f"⚠️  {error_count} files had parse errors")
        print()
        
        # Phase 3: Analyze dependencies
        print("📋 PHASE 3: Dependency & Impact Analysis")
        print("-" * 60)
        
        # Dependency graph
        dep_analyzer = DependencyAnalyzer(config)
        atlas_data.dependency_graph = dep_analyzer.analyze(files)
        
        # Impact analysis
        impact_analyzer = ImpactAnalyzer(config)
        atlas_data.impact_nodes = impact_analyzer.analyze(files)
        
        # Entry points
        entry_detector = EntryPointDetector(config)
        atlas_data.entry_points = entry_detector.detect(files)
        
        print()
        
        # Phase 4: Generate output files
        print("📋 PHASE 4: Atlas Generation")
        print("-" * 60)
        
        # Ensure output directory exists
        ensure_directory(output_dir)
        
        # Generate base.md
        base_gen = BaseGenerator(config, atlas_data)
        base_path = base_gen.generate(output_dir)
        
        # Generate children/*.md files
        detail_gen = DetailGenerator(config, atlas_data)
        child_paths = detail_gen.generate(output_dir)
        
        print()
        print("=" * 60)
        print("✅ ATLAS GENERATION COMPLETE")
        print("=" * 60)
        print(f"📄 Base file:     {base_path}")
        print(f"📂 Detail files:  {len(child_paths)} files in {config.children_dir}/")
        print()
        print("🎯 Next Steps:")
        print(f"   1. Read {config.base_filename} for project overview")
        print(f"   2. Read relevant files in {config.children_dir}/ for details")
        print("   3. Read source code for implementation")
        print("=" * 60)
        
        return atlas_data
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR")
        print("=" * 60)
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate codebase atlas for AI agent navigation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate atlas for current directory
  python -m codebase_atlas.main
  
  # Generate atlas for specific project
  python -m codebase_atlas.main --project-dir /path/to/project
  
  # Use verbose mode
  python -m codebase_atlas.main --verbose
  
  # Custom output directory
  python -m codebase_atlas.main --output-dir ./my_atlas
        """
    )
    
    parser.add_argument(
        '--project-dir',
        type=str,
        default='.',
        help='Path to project directory (default: current directory)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./atlas_output',
        help='Path to output directory (default: ./atlas_output)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Use verbose output format (default: compact)'
    )
    
    parser.add_argument(
        '--max-files-per-child',
        type=int,
        default=10,
        help='Maximum files per children file (default: 10)'
    )
    
    args = parser.parse_args()
    
    # Create config from arguments
    config = get_default_config()
    config.verbose_mode = args.verbose
    config.max_files_per_child = args.max_files_per_child
    
    try:
        # Generate atlas
        generate_atlas(
            project_dir=args.project_dir,
            output_dir=args.output_dir,
            config=config
        )
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())