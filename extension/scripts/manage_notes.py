import sys
import json
import os
import asyncio

# Add workspace root to sys.path to allow importing effilocal
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_root = os.path.dirname(os.path.dirname(current_dir))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from effilocal.mcp_server.tools import comment_tools

async def get_notes_async(filename, analysis_dir):
    try:
        result_json = await comment_tools.get_all_comments(filename)
        result = json.loads(result_json)
        
        if not result.get('success'):
            return {'success': False, 'error': result.get('error')}
            
        comments = result.get('comments', [])
        notes = {} # para_idx -> text
        
        for c in comments:
            text = c.get('text', '')
            if text.startswith('EFFI_NOTE:'):
                note_content = text[len('EFFI_NOTE:'):].strip()
                # Now we have paragraph_index thanks to updates in effilocal core
                para_idx = c.get('paragraph_index')
                if para_idx is not None:
                    notes[str(para_idx)] = note_content
            
        # Map to block_id
        blocks_path = os.path.join(analysis_dir, 'blocks.jsonl')
        block_notes = {}
        
        if os.path.exists(blocks_path):
            with open(blocks_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        block = json.loads(line)
                        if 'para_idx' in block:
                            pid = str(block['para_idx'])
                            if pid in notes:
                                block_notes[block['id']] = notes[pid]
                    except:
                        pass
                        
        return {'success': True, 'notes': block_notes}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def save_note_async(filename, para_idx, text):
    note_text = f"EFFI_NOTE: {text}"
    try:
        # Check for existing note
        result_json = await comment_tools.get_all_comments(filename)
        result = json.loads(result_json)
        
        existing_cid = None
        if result.get('success'):
            comments = result.get('comments', [])
            for c in comments:
                if c.get('paragraph_index') == para_idx and c.get('text', '').startswith('EFFI_NOTE:'):
                    existing_cid = c.get('comment_id') # Use the XML ID
                    break
        
        if existing_cid:
            res = await comment_tools.update_comment(filename, existing_cid, note_text)
        else:
            res = await comment_tools.add_comment_for_paragraph(filename, para_idx, note_text)
            
        return json.loads(res)
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'success': False, 'error': 'Invalid arguments'}))
        return

    action = sys.argv[1]
    
    if action == 'get_notes':
        filename = sys.argv[2]
        analysis_dir = sys.argv[3]
        result = asyncio.run(get_notes_async(filename, analysis_dir))
        print(json.dumps(result))

    elif action == 'save_note':
        filename = sys.argv[2]
        para_idx = int(sys.argv[3])
        text = sys.argv[4]
        result = asyncio.run(save_note_async(filename, para_idx, text))
        print(json.dumps(result))

if __name__ == '__main__':
    main()
