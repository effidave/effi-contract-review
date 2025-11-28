import requests
import json

URL = "http://127.0.0.1:8000/mcp"
HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
}

def initialize():
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"listChanged": True},
                "prompts": {"listChanged": True},
            },
            "clientInfo": {"name": "test_client", "version": "0.1"}
        }
    }
    resp = requests.post(URL, headers=HEADERS, json=payload, stream=True)
    sid = resp.headers.get("Mcp-Session-Id")
    print("Init status:", resp.status_code, "sid:", sid)
    for line in resp.iter_lines(decode_unicode=True):
        if line:
            print("INIT:", line)
    return sid

def call_tool(session_id, tool_name, tool_params: dict, req_id):
    headers = HEADERS.copy()
    headers["Mcp-Session-Id"] = session_id
    # Use nested arguments style
    data = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": tool_params
        }
    }
    print("REQUEST:", json.dumps(data))
    resp = requests.post(URL, headers=headers, json=data, stream=True)
    print(f"Call {tool_name} status:", resp.status_code)
    for line in resp.iter_lines(decode_unicode=True):
        if line:
            print("RESPONSE:", line)

if __name__ == "__main__":
    sid = initialize()
    if not sid:
        raise RuntimeError("No session ID from initialize")

    # Try operations
    #call_tool(sid, "create_document", {"filename": "test.docx", "title": "My Test"}, req_id=2)
    #call_tool(sid, "add_paragraph", {"filename": "test.docx", "text": "Hello world."}, req_id=3)
    #call_tool(sid, "add_heading", {"filename": "test.docx", "text": "Heading 1", "level": 1}, req_id=4)
    #call_tool(sid, "list_available_documents", {"directory": "C:/Users/DavidSant/Contract Tools"}, req_id=10)
