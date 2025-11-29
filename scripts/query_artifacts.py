"""CLI tool for querying analyzed document artifacts.

Usage:
    python scripts/query_artifacts.py "Project Name" --clause 3.2
    python scripts/query_artifacts.py "Project Name" --schedules
    python scripts/query_artifacts.py "Project Name" --outline
    python scripts/query_artifacts.py "Project Name" --search "confidentiality"
    python scripts/query_artifacts.py "Project Name" --stats
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from effilocal.artifact_loader import ArtifactLoader


def find_analysis_dir(project_name: str) -> Path:
    """Find analysis directory for a project."""
    base_dir = Path("EL_Projects")
    
    # Try exact match first
    project_dir = base_dir / project_name
    if project_dir.exists():
        analysis_dir = project_dir / "analysis"
        if analysis_dir.exists():
            return analysis_dir
    
    # Try substring match
    for project_path in base_dir.glob("*"):
        if project_path.is_dir() and project_name.lower() in project_path.name.lower():
            analysis_dir = project_path / "analysis"
            if analysis_dir.exists():
                return analysis_dir
    
    raise FileNotFoundError(f"Could not find analysis directory for project: {project_name}")


def print_clause(loader: ArtifactLoader, ordinal: str) -> None:
    """Print clause details."""
    clause = loader.find_clause_by_ordinal(ordinal)
    
    if not clause:
        print(f"❌ Clause {ordinal} not found")
        return
    
    print(f"\n📄 Clause {ordinal}")
    print(f"   ID: {clause['id']}")
    print(f"   Type: {clause.get('type', 'N/A')}")
    print(f"   Text: {clause.get('text', 'N/A')}")
    
    # Get clause group (main + continuations)
    group = loader.get_clause_group(clause['id'])
    if len(group) > 1:
        print(f"\n   📝 Continuations ({len(group) - 1}):")
        for cont in group[1:]:
            print(f"      • {cont.get('text', 'N/A')[:80]}...")
    
    # Get section context
    section_path = loader.get_section_path(clause.get('section_id', ''))
    if section_path:
        print(f"\n   📂 Section: {' > '.join(section_path)}")


def print_schedules(loader: ArtifactLoader) -> None:
    """Print all schedules."""
    schedules = loader.get_schedules()
    
    if not schedules:
        print("No schedules found")
        return
    
    print(f"\n📋 Schedules ({len(schedules)})")
    for schedule in schedules:
        label = schedule.get('label', 'Unnamed')
        attachment_id = schedule.get('attachment_id')
        
        blocks = loader.get_schedule_blocks(attachment_id)
        
        print(f"\n   {label}")
        print(f"   ID: {attachment_id}")
        print(f"   Blocks: {len(blocks)}")
        
        if blocks:
            print(f"   First block: {blocks[0].get('text', 'N/A')[:60]}...")


def print_outline(loader: ArtifactLoader, max_depth: int = 2) -> None:
    """Print document outline."""
    sections = loader.sections.get('root', {}).get('children', [])
    
    def print_section(section: dict, depth: int = 0) -> None:
        if depth > max_depth:
            return
        
        indent = "  " * depth
        title = section.get('title', 'Untitled')
        block_count = len(section.get('block_ids', []))
        
        print(f"{indent}{'└─' if depth > 0 else '•'} {title} ({block_count} blocks)")
        
        for child in section.get('children', []):
            print_section(child, depth + 1)
    
    print("\n📚 Document Outline")
    for section in sections:
        print_section(section)


def print_search_results(loader: ArtifactLoader, query: str) -> None:
    """Print search results."""
    results = loader.search_blocks(text=query)
    
    if not results:
        print(f"❌ No blocks found matching: {query}")
        return
    
    print(f"\n🔍 Search Results ({len(results)} blocks)")
    for block in results[:10]:  # Limit to first 10
        ordinal = block.get('list', {}).get('ordinal', '')
        text = block.get('text', 'N/A')[:80]
        
        prefix = f"[{ordinal}]" if ordinal else "[...]"
        print(f"\n   {prefix} {text}...")
        print(f"   ID: {block['id']}")
    
    if len(results) > 10:
        print(f"\n   ... and {len(results) - 10} more results")


def print_stats(loader: ArtifactLoader) -> None:
    """Print document statistics."""
    stats = loader.get_stats()
    
    print("\n📊 Document Statistics")
    print(f"   Document ID: {stats.get('doc_id', 'N/A')}")
    print(f"   Total blocks: {stats.get('block_count', 0)}")
    print(f"   Numbered blocks: {stats.get('numbered_blocks', 0)}")
    print(f"   Sections: {stats.get('section_count', 0)}")
    print(f"   Attachments: {stats.get('attachment_count', 0)}")
    print(f"   Hierarchy depth: {stats.get('hierarchy_depth', 0)}")
    print(f"   Styles: {stats.get('style_count', 0)}")


def main():
    parser = argparse.ArgumentParser(description="Query analyzed document artifacts")
    parser.add_argument("project", help="Project name or path")
    parser.add_argument("--clause", help="Show clause by ordinal (e.g., '3.2.1')")
    parser.add_argument("--schedules", action="store_true", help="List all schedules")
    parser.add_argument("--outline", action="store_true", help="Show document outline")
    parser.add_argument("--search", help="Search for text in blocks")
    parser.add_argument("--stats", action="store_true", help="Show document statistics")
    parser.add_argument("--analysis-dir", help="Direct path to analysis directory")
    
    args = parser.parse_args()
    
    try:
        # Find analysis directory
        if args.analysis_dir:
            analysis_dir = Path(args.analysis_dir)
        else:
            analysis_dir = find_analysis_dir(args.project)
        
        print(f"Loading artifacts from: {analysis_dir}")
        loader = ArtifactLoader(analysis_dir)
        
        # Execute command
        if args.clause:
            print_clause(loader, args.clause)
        elif args.schedules:
            print_schedules(loader)
        elif args.outline:
            print_outline(loader)
        elif args.search:
            print_search_results(loader, args.search)
        elif args.stats:
            print_stats(loader)
        else:
            # Default: show stats
            print_stats(loader)
        
        print()  # Final newline
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
