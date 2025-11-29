#!/usr/bin/env python3
"""Get detailed text for specific clauses by ID."""
import json
import sys
from pathlib import Path

# Add parent directory to path to import effilocal
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from effilocal.artifact_loader import ArtifactLoader


def get_clause_details(analysis_dir: str, clause_ids: list) -> str:
    """Get full text for specified clause IDs.
    
    Args:
        analysis_dir: Path to analysis directory
        clause_ids: List of block IDs to retrieve
        
    Returns:
        JSON string with success status and clause details
    """
    try:
        loader = ArtifactLoader(analysis_dir)
        clauses = []
        
        # Build lookup dict from blocks
        clause_id_set = set(clause_ids)
        
        for block in loader.blocks:
            if block.get('id') in clause_id_set:
                list_meta = block.get('list', {})
                clauses.append({
                    'id': block['id'],
                    'ordinal': list_meta.get('ordinal', ''),
                    'text': block.get('text', ''),
                    'type': block.get('type', ''),
                    'level': list_meta.get('level', 0),
                    'section_id': block.get('section_id', '')
                })
        
        return json.dumps({
            'success': True,
            'clauses': clauses,
            'count': len(clauses)
        })
    except Exception as e:
        return json.dumps({
            'success': False,
            'error': str(e),
            'clauses': []
        })


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'Usage: get_clause_details.py <analysis_dir> (clause_ids via stdin)'
        }))
        sys.exit(1)
    
    analysis_dir = sys.argv[1]
    # Read clause IDs from stdin
    clause_ids_json = sys.stdin.read().strip()
    clause_ids = json.loads(clause_ids_json)
    
    print(get_clause_details(analysis_dir, clause_ids))
