"""Diagnostic script to show ordinals in numbering_restart.docx"""
from pathlib import Path
from effilocal.doc.direct_docx import iter_paragraph_blocks

blocks = list(iter_paragraph_blocks(Path('fixtures/numbering_restart.docx')))
level_0 = [b for b in blocks if b.get('list') and b['list']['level'] == 0]

print(f'\nFound {len(level_0)} level-0 numbered blocks:\n')
for i, b in enumerate(level_0):
    ordinal = b['list']['ordinal']
    counters = b['list']['counters']
    restart = b['list']['restart_boundary']
    group = b.get('restart_group_id', '')[-8:]
    text = b.get('text', '')[:40]
    print(f'{i+1:2}. ordinal={ordinal:4} counters={counters} restart={restart} group=...{group} text="{text}"')
