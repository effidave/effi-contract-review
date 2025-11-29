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
    """Load analysis and return outline as JSON."""
    try:
        loader = ArtifactLoader(analysis_dir)
        
        # Get outline data using artifact loader queries
        outline_items = []
        
        # Query for heading blocks with ordinals
        for block in loader.blocks:
            if block.get('type') in ('heading', 'list_item'):
                list_meta = block.get('list')
                
                # Only include blocks with list numbering
                if list_meta and list_meta.get('ordinal'):
                    outline_items.append({
                        'id': block['id'],
                        'ordinal': list_meta['ordinal'],
                        'text': block.get('text', '')[:100],  # Limit to 100 chars
                        'level': list_meta.get('level', 0),
                        'type': block.get('type'),
                        'section_id': block.get('section_id'),
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
