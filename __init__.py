"""Office Word MCP Server package entry point."""

# Lazy import to avoid breaking pytest when dependencies aren't available
def __getattr__(name):
    if name == "run_server":
        from word_document_server.main import run_server
        return run_server
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ["run_server"]
