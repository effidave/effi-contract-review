#!/usr/bin/env python3
"""Get document outline from artifact loader for webview display.

Usage:
    python get_outline.py <analysis_dir>

Returns JSON to stdout with outline structure.
"""
import json
import sys
from pathlib import Path

# Add parent directory to path to import effilocal
sys.path.insert(0, str(Path(__file__).parent.parent))

from effilocal.artifact_loader import ArtifactLoader


def get_outline_json(analysis_dir: str) -> str:
    """Load analysis and return outline as JSON.
    
    Returns ALL blocks with checkboxes, showing ordinal for numbered blocks
    and type/style info for unnumbered blocks.
    """
    try:
        loader = ArtifactLoader(analysis_dir)
        
        # Get ALL blocks for the outline
        outline_items = []
        
        for block in loader.blocks:
            list_meta = block.get('list') or {}
            ordinal = list_meta.get('ordinal', '')
            level = list_meta.get('level', 0)
            block_type = block.get('type', 'paragraph')
            text = block.get('text', '')[:100]  # Limit to 100 chars
            
            # For unnumbered blocks, show style or type as label
            if not ordinal:
                style = block.get('style', '')
                if block_type == 'heading':
                    ordinal = f'[{style or "Heading"}]'
                elif block_type == 'table_cell':
                    table_info = block.get('table', {})
                    ordinal = f'[Table R{table_info.get("row", 0)+1}C{table_info.get("col", 0)+1}]'
                else:
                    # No label for regular paragraphs - just show the text
                    ordinal = ''
            
            outline_items.append({
                'id': block['id'],
                'ordinal': ordinal,
                'text': text,
                'level': level,
                'type': block_type,
                'section_id': block.get('section_id'),
                'is_numbered': bool(list_meta.get('ordinal')),
            })
        
        return json.dumps({
            'success': True,
            'outline': outline_items,
            'count': len(outline_items)
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            'success': False,
            'error': str(e)
        }, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'success': False, 'error': 'Usage: get_outline.py <analysis_dir>'}))
        sys.exit(1)
    
    analysis_dir = sys.argv[1]
    print(get_outline_json(analysis_dir))
