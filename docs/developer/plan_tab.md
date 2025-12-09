Recommended Order
Core Classes (TypeScript)

Edit class (simplest, no dependencies)
WorkTask class (depends on Edit)
WorkPlan class (depends on WorkTask)
Unit tests for all class methods
Persistence Layer

edits.jsonl read/write utilities
plan.md YAML frontmatter serialization/deserialization
plan.meta.json save/load (optional, for fast loading)
Ensure folder/file creation if missing
Tests for persistence
Extension Integration

Wire WorkPlan into extension host (extension.ts)
Add message handlers for webview ↔ extension communication
Tests for message handling
Webview UI

Add tab bar with "Contract Analysis" and "Plan" tabs
Plan tab content area (markdown display, View/Edit toggle)
Wire up auto-save on edit
UI tests
LLM/MCP Integration

Hook MCP tool calls to log Edit objects automatically
Tests for edit logging
Further Considerations
Start with tests? For each step, write tests first (TDD), then implement. This ensures correctness and catches regressions.
Parallel work? Steps 1–2 are independent of the UI, so you could review/iterate on the class design while UI is in progress.