import json
import subprocess
import sys
import time


def read_until(proc, target_id, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.05)
            continue
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if isinstance(obj, dict) and obj.get("id") == target_id:
            return obj
    return None


def main():
    proc = subprocess.Popen(
        [sys.executable, "-m", "effilocal.mcp_server.main"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "diagnostic", "version": "1.0"},
        },
    }
    proc.stdin.write(json.dumps(init_payload) + "\n")
    proc.stdin.flush()
    init_resp = read_until(proc, 1)
    print("INIT:", init_resp)

    tools_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    }
    proc.stdin.write(json.dumps(tools_payload) + "\n")
    proc.stdin.flush()
    tools_resp = read_until(proc, 2)
    print("TOOLS RESPONSE:")
    if tools_resp and "result" in tools_resp:
        tools = tools_resp["result"].get("tools", [])
        for tool in tools:
            print(f"- {tool.get('name')} (enabled={tool.get('enabled', True)})")
    else:
        print(tools_resp)

    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()


if __name__ == "__main__":
    main()
