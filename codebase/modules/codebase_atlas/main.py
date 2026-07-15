"""
Main entry point for Codebase Atlas.

Orchestrates the complete pipeline:
1. Scan files
2. Parse files (Python, JS, HTML, configs)
3. Analyze dependencies and impact
4. Generate atlas files (base.md + children/*.md)
"""

import sys
import json
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
from .graph.backend.graph_builder import GraphBuilder
from .graph.backend.graph_serializer import GraphSerializer
from .utils import clean_directory, ensure_directory


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
        
        # Recalculate total_loc now that parsers have populated it
        atlas_data.total_loc = sum(f.loc for f in atlas_data.files)
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
        
        # Clean output directory for fresh start,
        # but preserve persisted node positions
        clean_directory(
            output_dir,
            keep_files=[
                "node_pos_dep.json",
                "node_pos_call.json",
                "graphdata.json",
            ],
        )
        
        # Ensure output directory exists
        ensure_directory(output_dir)

        # Record project identity so persisted positions
        # are not reused across different projects
        project_id = str(
            Path(project_dir).resolve()
        )

        try:
            (
                Path(output_dir) /
                "atlas_meta.json"
            ).write_text(
                json.dumps(
                    {"project_id": project_id},
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass

        # Generate base.md
        base_gen = BaseGenerator(config, atlas_data)
        base_path = base_gen.generate(output_dir)
        
        # Generate children/*.md files
        detail_gen = DetailGenerator(config, atlas_data)
        child_paths = detail_gen.generate(output_dir)

        # Always generate graphdata.json (for code_rag tools)
        try:
            output_path = Path(output_dir)
            builder = GraphBuilder(atlas_data)
            unified_graph = builder.build_unified_graph()
            GraphSerializer.save_json(
                unified_graph,
                output_path / "graphdata.json",
            )
        except Exception as e:
            print(f"  ⚠️  Graph generation skipped: {e}")

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
        '--max-files-per-child',
        type=int,
        default=10,
        help='Maximum files per children file (default: 10)'
    )
    
    parser.add_argument(
        '--serve',
        action='store_true',
        help='Start local graph explorer server after analysis'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Port for graph explorer server (default: 8080)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Host for graph explorer server (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--ignore-dirs',
        nargs='+',
        default=[],
        help='Directory names to ignore (e.g. --ignore-dirs data logs temp)'
    )
    
    parser.add_argument(
        '--load',
        action='store_true',
        help='Load previously generated atlas from output-dir and serve it (skips generation)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.load:
            from .graph.backend.graph_serializer import GraphSerializer
            from .graph.backend.serve import create_app

            output_path = Path(args.output_dir)
            unified_json_path = output_path / "graphdata.json"

            if not unified_json_path.exists():
                print("=" * 60)
                print("❌ GRAPHDATA JSON NOT FOUND")
                print("=" * 60)
                print(f"Expected unified graph data in: {unified_json_path}")
                print()
                print("Run with --serve first to generate graph data:")
                print(f"  python -m codebase_atlas.main --serve --project-dir <path>")
                print()
                return 1

            unified_graph = GraphSerializer.load_json(unified_json_path)

            print("=" * 60)
            print("🗺️  LOADED GRAPHDATA JSON")
            print("=" * 60)
            print(f"Loaded from: {args.output_dir}")
            print()

            meta_path = output_path / "atlas_meta.json"
            project_id = None

            if meta_path.exists():
                try:
                    project_id = json.loads(
                        meta_path.read_text(encoding="utf-8")
                    ).get("project_id")
                except Exception:
                    pass

            app = create_app(
                unified_graph=unified_graph,
                output_dir=output_path,
                project_id=project_id,
            )
            print(f"  Graph explorer")
            print(f"    Interactive:  http://{args.host}:{args.port}/view/interactive")
            app.run(host=args.host, port=args.port, debug=False)
            return 0
        
        # Create config from arguments
        config = get_default_config()
        config.max_files_per_child = args.max_files_per_child
        config.ignore_dirs.update(args.ignore_dirs or [])
        
        # Generate atlas
        atlas_data = generate_atlas(
            project_dir=args.project_dir,
            output_dir=args.output_dir,
            config=config
        )

        project_id = str(
            Path(args.project_dir).resolve()
        )
        
        # Start graph explorer if requested
        if args.serve:
            from .graph.backend.graph_builder import GraphBuilder
            from .graph.backend.serve import create_app
            from .graph.backend.graph_serializer import GraphSerializer

            builder = GraphBuilder(atlas_data)
            unified_graph = builder.build_unified_graph()

            output_dir = Path(args.output_dir)

            GraphSerializer.save_json(
                unified_graph,
                output_dir / "graphdata.json",
            )

            app = create_app(
                unified_graph=unified_graph,
                output_dir=output_dir,
                project_id=project_id,
            )
            print(f"  Graph explorer")
            print(f"    Interactive:  http://{args.host}:{args.port}/view/interactive")
            app.run(host=args.host, port=args.port, debug=False)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())