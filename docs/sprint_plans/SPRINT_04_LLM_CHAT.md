# Sprint 4: LLM Chat Integration

**Duration:** 2 weeks  
**Goal:** Seamless chat experience with document context, triggering VS Code's Copilot Chat from within the webview.

---

## Objectives

1. **Chat Panel in Webview** - Collapsible chat interface
2. **VS Code Chat Bridge** - Trigger Copilot Chat with context
3. **Context Assembly** - Smart selection of relevant document content
4. **Tool Invocation** - LLM can trigger MCP tools via chat

---

## User Stories

### US4.1: Open Chat from Webview
**As a** lawyer reviewing a contract,  
**I want** to ask questions without leaving the document view,  
**So that** my review stays focused and efficient.

**Acceptance Criteria:**
- [ ] "Ask Copilot" button in toolbar
- [ ] Chat panel slides open from bottom/side
- [ ] Can type questions naturally
- [ ] Responses appear in chat panel
- [ ] Test: Ask "What does clause 5.1 mean?" → get response

### US4.2: Context from Selection
**As a** lawyer asking about specific clauses,  
**I want** my selected text automatically included in my question,  
**So that** the LLM knows what I'm referring to.

**Acceptance Criteria:**
- [ ] Selected clauses included as context
- [ ] Selection checkboxes in outline/fulltext views
- [ ] Context preview before sending
- [ ] Test: Select 3 clauses → ask question → context included

### US4.3: Context from Full Document
**As a** lawyer asking general questions,  
**I want** the LLM to have access to the whole document,  
**So that** it can answer questions about the overall structure.

**Acceptance Criteria:**
- [ ] "Include full document" option
- [ ] Smart truncation for long documents
- [ ] Section summaries for context efficiency
- [ ] Test: Ask "What are the key obligations?" → LLM uses full doc

### US4.4: Tool Invocation via Chat
**As a** lawyer who wants the LLM to make edits,  
**I want** to say "add a clause about X" and have it done,  
**So that** I don't have to manually type everything.

**Acceptance Criteria:**
- [ ] LLM can call MCP tools
- [ ] User confirmation before edits
- [ ] Edit preview shown
- [ ] Actual edit applied on confirm
- [ ] Test: "Add a confidentiality clause after 5.1" → clause added

### US4.5: Chat History
**As a** lawyer continuing a review session,  
**I want** to see my previous questions and answers,  
**So that** I can track my analysis.

**Acceptance Criteria:**
- [ ] Chat history persists during session
- [ ] Can scroll back through conversation
- [ ] Clear chat option
- [ ] Test: Multiple Q&A → all visible in history

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Webview                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Chat Panel (collapsible)                                │    │
│  │  ┌─────────────────────────────────────────────────────┐│    │
│  │  │ [Context: 3 clauses selected]                       ││    │
│  │  ├─────────────────────────────────────────────────────┤│    │
│  │  │ 👤 What risks does clause 5.1 create?               ││    │
│  │  │                                                     ││    │
│  │  │ 🤖 Clause 5.1 creates the following risks:          ││    │
│  │  │    1. Unlimited liability for indirect damages      ││    │
│  │  │    2. No cap on warranty claims...                  ││    │
│  │  │                                                     ││    │
│  │  │ 👤 Add a liability cap after this clause            ││    │
│  │  │                                                     ││    │
│  │  │ 🤖 I'll add a liability cap clause. Preview:        ││    │
│  │  │    "5.2 The total liability... shall not exceed..." ││    │
│  │  │    [Apply] [Edit] [Cancel]                          ││    │
│  │  └─────────────────────────────────────────────────────┘│    │
│  │  ┌─────────────────────────────────────────────────────┐│    │
│  │  │ [📎 Context] Ask a question...          [Send]      ││    │
│  │  └─────────────────────────────────────────────────────┘│    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐           ┌─────────────────────┐
│  VS Code Chat   │           │     MCP Server      │
│  (Copilot)      │◄─────────►│  (Tool Execution)   │
└─────────────────┘           └─────────────────────┘
```

### Chat Flow Options

**Option A: Direct Copilot Chat Integration**
```
Webview → postMessage → Extension → vscode.commands.executeCommand('workbench.action.chat.open', { query }) 
```
- Uses VS Code's native chat
- Inherits Copilot's capabilities
- Limited control over response handling

**Option B: Custom Chat with LLM API**
```
Webview → postMessage → Extension → Python MCP server → OpenAI/Anthropic API → response
```
- Full control over prompts and responses
- Can integrate tool calling
- Requires API key management

**Recommendation: Hybrid Approach**
- Use VS Code Chat for general questions (leverages Copilot)
- Use custom MCP flow for tool invocations (we control the loop)

---

## Technical Tasks

### T4.1: Chat Panel UI (2 days)
**File:** `extension/src/webview/chat-panel.js` (new)

```javascript
class ChatPanel {
  constructor(container) {
    this.container = container;
    this.messages = [];
    this.isOpen = false;
  }
  
  toggle() {
    this.isOpen = !this.isOpen;
    this.render();
  }
  
  render() {
    this.container.innerHTML = `
      <div class="chat-panel ${this.isOpen ? 'open' : 'closed'}">
        <div class="chat-header">
          <span>Ask Copilot</span>
          <button class="close-btn">×</button>
        </div>
        <div class="chat-messages">
          ${this.messages.map(m => this.renderMessage(m)).join('')}
        </div>
        <div class="chat-input-area">
          <div class="context-indicator">
            ${this.renderContextIndicator()}
          </div>
          <textarea placeholder="Ask a question..."></textarea>
          <button class="send-btn">Send</button>
        </div>
      </div>
    `;
  }
  
  renderMessage(msg) {
    const icon = msg.role === 'user' ? '👤' : '🤖';
    return `
      <div class="message ${msg.role}">
        <span class="icon">${icon}</span>
        <div class="content">${msg.content}</div>
        ${msg.toolPreview ? this.renderToolPreview(msg.toolPreview) : ''}
      </div>
    `;
  }
  
  renderToolPreview(preview) {
    return `
      <div class="tool-preview">
        <div class="preview-header">Proposed change:</div>
        <div class="preview-content">${preview.description}</div>
        <div class="preview-actions">
          <button class="apply-btn" data-tool-id="${preview.id}">Apply</button>
          <button class="edit-btn" data-tool-id="${preview.id}">Edit</button>
          <button class="cancel-btn" data-tool-id="${preview.id}">Cancel</button>
        </div>
      </div>
    `;
  }
  
  async sendMessage(text) {
    // Add user message
    this.messages.push({ role: 'user', content: text });
    this.render();
    
    // Send to extension
    vscode.postMessage({
      command: 'chatMessage',
      text: text,
      context: this.getSelectedContext()
    });
  }
  
  receiveResponse(response) {
    this.messages.push({ 
      role: 'assistant', 
      content: response.text,
      toolPreview: response.toolPreview
    });
    this.render();
  }
}
```

### T4.2: Context Assembly (2 days)
**File:** `extension/src/webview/context-builder.js` (new)

```javascript
class ContextBuilder {
  constructor(blocks, selectedIds) {
    this.blocks = blocks;
    this.selectedIds = selectedIds;
  }
  
  buildContext(options = {}) {
    const context = {
      documentName: currentDocumentName,
      selectedClauses: [],
      fullDocument: null
    };
    
    // Add selected clauses
    if (this.selectedIds.size > 0) {
      context.selectedClauses = Array.from(this.selectedIds)
        .map(id => this.blocks.find(b => b.id === id))
        .filter(Boolean)
        .map(b => ({
          ordinal: b.list?.ordinal || '',
          text: b.text,
          para_id: b.para_id
        }));
    }
    
    // Add full document if requested and small enough
    if (options.includeFullDocument) {
      const fullText = this.blocks.map(b => b.text).join('\n');
      if (fullText.length < 50000) {
        context.fullDocument = fullText;
      } else {
        // Use section summaries instead
        context.documentSummary = this.generateSummary();
      }
    }
    
    return context;
  }
  
  generateSummary() {
    // Group blocks by section, create summary
    // Return: "Definitions (15 clauses), Services (8 clauses), ..."
  }
  
  formatForPrompt() {
    const ctx = this.buildContext({ includeFullDocument: true });
    
    let prompt = `Document: ${ctx.documentName}\n\n`;
    
    if (ctx.selectedClauses.length > 0) {
      prompt += `Selected Clauses:\n`;
      ctx.selectedClauses.forEach(c => {
        prompt += `${c.ordinal}: ${c.text}\n\n`;
      });
    }
    
    if (ctx.fullDocument) {
      prompt += `\nFull Document:\n${ctx.fullDocument}`;
    }
    
    return prompt;
  }
}
```

### T4.3: VS Code Chat Bridge (2 days)
**File:** `extension/src/extension.ts` (modify)

```typescript
// Handle chat message from webview
case 'chatMessage':
  await handleChatMessage(message.text, message.context);
  break;

async function handleChatMessage(text: string, context: any) {
  // Format context for Copilot
  const formattedContext = formatContextForChat(context);
  
  // Check if this looks like a tool request
  if (looksLikeToolRequest(text)) {
    // Use custom MCP flow
    await handleToolRequest(text, context);
  } else {
    // Use VS Code Copilot Chat
    await triggerCopilotChat(text, formattedContext);
  }
}

async function triggerCopilotChat(query: string, context: string) {
  // Copy context to clipboard (workaround for now)
  await vscode.env.clipboard.writeText(context);
  
  // Open chat with the query
  await vscode.commands.executeCommand('workbench.action.chat.open', {
    query: query,
    // Note: as of Dec 2025, direct context injection may need @workspace or chat participant
  });
  
  // Notify webview
  webviewPanel?.webview.postMessage({
    command: 'chatOpened',
    message: 'Opened Copilot Chat. Context copied to clipboard.'
  });
}

function looksLikeToolRequest(text: string): boolean {
  const toolPatterns = [
    /add\s+(a\s+)?(clause|paragraph|section)/i,
    /replace\s+(the\s+)?clause/i,
    /delete\s+(the\s+)?clause/i,
    /insert\s+after/i,
    /modify\s+(the\s+)?text/i
  ];
  return toolPatterns.some(p => p.test(text));
}
```

### T4.4: Tool Request Handler (3 days)
**File:** `extension/src/tool-handler.ts` (new)

```typescript
interface ToolRequest {
  tool: string;
  args: Record<string, any>;
  description: string;
}

async function handleToolRequest(text: string, context: any) {
  // Send to MCP server for interpretation
  const interpretation = await interpretToolRequest(text, context);
  
  if (!interpretation.tool) {
    // Couldn't parse as tool request, fall back to chat
    await triggerCopilotChat(text, formatContextForChat(context));
    return;
  }
  
  // Send preview to webview
  webviewPanel?.webview.postMessage({
    command: 'toolPreview',
    preview: {
      id: interpretation.id,
      tool: interpretation.tool,
      args: interpretation.args,
      description: interpretation.description
    }
  });
}

async function interpretToolRequest(text: string, context: any): Promise<ToolRequest> {
  // Call MCP server to interpret natural language as tool call
  const scriptPath = path.join(__dirname, '..', 'scripts', 'interpret_tool.py');
  const input = JSON.stringify({ text, context });
  
  const { stdout } = await execAsync(
    `"${pythonCmd}" "${scriptPath}"`,
    { input }
  );
  
  return JSON.parse(stdout);
}

async function executeToolRequest(requestId: string) {
  const request = pendingToolRequests.get(requestId);
  if (!request) return;
  
  // Execute via MCP
  const result = await callMcpTool(request.tool, request.args);
  
  // Notify webview
  webviewPanel?.webview.postMessage({
    command: 'toolResult',
    requestId,
    success: result.success,
    message: result.message
  });
  
  // Refresh document
  if (result.success) {
    await reanalyzeAndRefresh();
  }
}
```

### T4.5: Tool Interpretation Script (2 days)
**File:** `extension/scripts/interpret_tool.py` (new)

```python
"""Interpret natural language as MCP tool call."""

import json
import sys
import re

TOOL_PATTERNS = [
    {
        "pattern": r"add\s+(?:a\s+)?(?:clause|paragraph)\s+(?:about\s+)?(.+?)\s+after\s+(?:clause\s+)?(\d+(?:\.\d+)*)",
        "tool": "add_paragraph_after_clause",
        "extract": lambda m: {
            "clause_number": m.group(2),
            "text": f"[Draft clause about: {m.group(1)}]",
            "inherit_numbering": True
        }
    },
    {
        "pattern": r"replace\s+(?:the\s+)?(?:text\s+of\s+)?clause\s+(\d+(?:\.\d+)*)\s+with\s+(.+)",
        "tool": "replace_clause_text_by_ordinal",
        "extract": lambda m: {
            "clause_number": m.group(1),
            "new_text": m.group(2)
        }
    },
    {
        "pattern": r"delete\s+clause\s+(\d+(?:\.\d+)*)",
        "tool": "delete_clause_by_ordinal",
        "extract": lambda m: {
            "clause_number": m.group(1)
        }
    }
]

def interpret(text: str, context: dict) -> dict:
    """Parse natural language into tool call."""
    text = text.lower().strip()
    
    for pattern_def in TOOL_PATTERNS:
        match = re.search(pattern_def["pattern"], text, re.IGNORECASE)
        if match:
            args = pattern_def["extract"](match)
            args["filename"] = context.get("documentPath", "")
            
            return {
                "id": str(uuid.uuid4()),
                "tool": pattern_def["tool"],
                "args": args,
                "description": generate_description(pattern_def["tool"], args)
            }
    
    return {"tool": None}

def generate_description(tool: str, args: dict) -> str:
    if tool == "add_paragraph_after_clause":
        return f"Add new clause after {args['clause_number']}"
    elif tool == "replace_clause_text_by_ordinal":
        return f"Replace text of clause {args['clause_number']}"
    elif tool == "delete_clause_by_ordinal":
        return f"Delete clause {args['clause_number']}"
    return f"Execute {tool}"

if __name__ == "__main__":
    input_data = json.load(sys.stdin)
    result = interpret(input_data["text"], input_data["context"])
    print(json.dumps(result))
```

### T4.6: Chat Panel Styling (1 day)
**File:** `extension/src/webview/style.css` (add)

```css
/* Chat Panel */
.chat-panel {
  position: fixed;
  bottom: 0;
  right: 0;
  width: 400px;
  height: 50vh;
  background: var(--vscode-editor-background);
  border-left: 1px solid var(--vscode-panel-border);
  border-top: 1px solid var(--vscode-panel-border);
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
  z-index: 100;
}

.chat-panel.closed {
  transform: translateY(calc(100% - 40px));
}

.chat-header {
  padding: 10px 15px;
  background: var(--vscode-titleBar-activeBackground);
  display: flex;
  justify-content: space-between;
  cursor: pointer;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
}

.message {
  margin-bottom: 15px;
  display: flex;
  gap: 10px;
}

.message .icon {
  font-size: 18px;
}

.message .content {
  flex: 1;
  line-height: 1.5;
}

.message.user .content {
  font-weight: 500;
}

.tool-preview {
  margin-top: 10px;
  padding: 10px;
  background: var(--vscode-editor-inactiveSelectionBackground);
  border-radius: 4px;
}

.preview-header {
  font-size: 12px;
  color: var(--vscode-descriptionForeground);
  margin-bottom: 5px;
}

.preview-actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
}

.preview-actions button {
  padding: 4px 12px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
}

.apply-btn {
  background: var(--vscode-button-background);
  color: var(--vscode-button-foreground);
}

.chat-input-area {
  padding: 10px 15px;
  border-top: 1px solid var(--vscode-panel-border);
}

.context-indicator {
  font-size: 12px;
  color: var(--vscode-descriptionForeground);
  margin-bottom: 8px;
}

.chat-input-area textarea {
  width: 100%;
  height: 60px;
  resize: none;
  background: var(--vscode-input-background);
  color: var(--vscode-input-foreground);
  border: 1px solid var(--vscode-input-border);
  border-radius: 4px;
  padding: 8px;
}

.send-btn {
  margin-top: 8px;
  float: right;
  padding: 6px 16px;
  background: var(--vscode-button-background);
  color: var(--vscode-button-foreground);
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
```

---

## Testing Plan

### Unit Tests
- `test_context_builder.js`: Context assembly from blocks
- `test_interpret_tool.py`: Natural language parsing

### Integration Tests
- Select clauses → open chat → verify context
- Ask tool question → verify preview
- Confirm tool → verify execution

### Manual Tests
1. Open chat panel, ask general question
2. Select clauses, ask about them
3. Request clause addition, confirm preview
4. Cancel a tool preview
5. Full conversation flow

---

## Definition of Done

- [ ] Chat panel opens/closes from toolbar
- [ ] Messages display with user/assistant styling
- [ ] Selected clauses included as context
- [ ] Can trigger VS Code Copilot for general questions
- [ ] Tool requests parsed and previewed
- [ ] Tool execution on user confirmation
- [ ] Chat history visible during session
- [ ] All tests passing
- [ ] Documentation updated

---

## Dependencies

- Sprint 3 complete (stable editor)
- VS Code Chat API access
- MCP server running with tool registration

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| VS Code Chat API limitations | Medium | High | Use clipboard workaround, plan custom participant |
| Tool parsing errors | Medium | Medium | Fallback to chat, show error gracefully |
| Context too large | Low | Medium | Smart truncation, section summaries |

---

## Future Enhancements

- Custom Copilot Chat Participant (`@effi`)
- Streaming responses
- Voice input
- Multi-turn tool conversations
