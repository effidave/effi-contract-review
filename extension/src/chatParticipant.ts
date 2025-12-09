/**
 * EffiChatParticipant - VS Code Chat Participant for contract review
 * 
 * Provides a @effi chat participant that answers questions about
 * the currently loaded contract using VS Code's Language Model API.
 */

import * as vscode from 'vscode';

// ============================================================================
// Types
// ============================================================================

/**
 * Result returned from chat participant handler
 */
export interface EffiChatResult {
    metadata: {
        documentPath?: string;
        contextIncluded: boolean;
    };
}

/**
 * Callback type for getting the current document path
 */
export type DocumentPathGetter = () => string | undefined;

/**
 * Callback type for loading contract context (for testing/DI)
 */
export type ContextLoader = () => string;

/**
 * Callback type for getting blocks from the loaded analysis
 */
export type BlocksGetter = () => any[] | undefined;

// ============================================================================
// Constants
// ============================================================================

/** Maximum characters of contract context to include (PoC limit) */
const MAX_CONTEXT_LENGTH = 200;

/** System prompt for the contract assistant */
const SYSTEM_PROMPT = `You are Effi, an expert legal contract assistant. You help lawyers review and understand commercial contracts.

Your capabilities:
- Explain contract clauses in plain language
- Identify potential risks and issues
- Suggest improvements and alternatives
- Answer questions about contract terms and obligations

Be concise, professional, and focus on practical legal advice.`;

// ============================================================================
// EffiChatParticipant Class
// ============================================================================

/**
 * Chat participant class for contract-aware LLM interactions.
 * 
 * Implements the VS Code Chat Participant pattern with:
 * - Dependency injection for document path access
 * - Optional context loader for testing
 * - Streaming response handling
 * - Error handling for LLM failures
 */
export class EffiChatParticipant {
    private readonly getDocumentPath: DocumentPathGetter;
    private readonly loadContext: ContextLoader | undefined;
    private readonly getBlocks: BlocksGetter | undefined;
    private handler: vscode.ChatRequestHandler | undefined;

    /**
     * Create a new chat participant
     * 
     * @param getDocumentPath - Callback to get current document path
     * @param loadContext - Optional callback to load context (for testing)
     * @param getBlocks - Optional callback to get loaded blocks (for production)
     */
    constructor(
        getDocumentPath: DocumentPathGetter,
        loadContext?: ContextLoader,
        getBlocks?: BlocksGetter
    ) {
        this.getDocumentPath = getDocumentPath;
        this.loadContext = loadContext;
        this.getBlocks = getBlocks;
    }

    /**
     * Get the chat request handler function.
     * Returns the same handler instance on subsequent calls.
     * 
     * @returns The ChatRequestHandler bound to this instance
     */
    public getHandler(): vscode.ChatRequestHandler {
        if (!this.handler) {
            this.handler = this.handleRequest.bind(this);
        }
        return this.handler;
    }

    /**
     * Main request handler - processes chat requests
     */
    private async handleRequest(
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<EffiChatResult> {
        const documentPath = this.getDocumentPath();
        let contextIncluded = false;
        let contractContext: string | undefined;

        // Try to load contract context
        try {
            contractContext = this.loadContractContext();
            contextIncluded = !!contractContext;
        } catch (error) {
            // Context loading failed - continue without context
            console.error('Failed to load contract context:', error);
        }

        // Build messages for the LLM
        const messages = this.buildMessages(request.prompt, contractContext);

        // Send request to LLM and stream response (with tool support)
        try {
            await this.streamResponseWithTools(request, messages, stream, token);
        } catch (error) {
            // Handle errors gracefully
            this.handleError(error, stream);
        }

        return {
            metadata: {
                documentPath,
                contextIncluded
            }
        };
    }

    /**
     * Load contract context from the current document
     * 
     * @returns Truncated contract text (first 200 chars for PoC)
     */
    private loadContractContext(): string | undefined {
        const docPath = this.getDocumentPath();
        
        if (!docPath) {
            return undefined;
        }

        // Use injected test loader if available (for testing)
        if (this.loadContext) {
            const fullContext = this.loadContext();
            return this.truncateContext(fullContext);
        }

        // Use in-memory blocks from the Contract Analysis panel
        if (this.getBlocks) {
            const blocks = this.getBlocks();
            if (blocks && blocks.length > 0) {
                const texts: string[] = [];
                for (const block of blocks) {
                    if (block.text) {
                        texts.push(block.text);
                    }
                }
                const fullText = texts.join('\n');
                console.log(`Chat participant using ${blocks.length} blocks, ${fullText.length} chars total`);
                return this.truncateContext(fullText);
            }
        }

        // No context available
        console.log('No contract context available for chat participant');
        return undefined;
    }

    /**
     * Truncate context to maximum length
     */
    private truncateContext(text: string): string {
        if (text.length <= MAX_CONTEXT_LENGTH) {
            return text;
        }
        return text.substring(0, MAX_CONTEXT_LENGTH);
    }

    /**
     * Build the message array for the LLM request
     */
    private buildMessages(
        userPrompt: string,
        contractContext: string | undefined
    ): vscode.LanguageModelChatMessage[] {
        const messages: vscode.LanguageModelChatMessage[] = [];

        // Add system context
        let systemMessage = SYSTEM_PROMPT;
        
        if (contractContext) {
            systemMessage += `\n\nContract context:\n${contractContext}`;
        } else {
            systemMessage += '\n\nNote: No document is currently loaded.';
        }
        
        messages.push(vscode.LanguageModelChatMessage.User(systemMessage));

        // Add user's question
        messages.push(vscode.LanguageModelChatMessage.User(userPrompt));

        return messages;
    }

    /**
     * Send request to LLM with tool support and stream response
     * 
     * Gets available MCP tools and passes them to the model.
     * When the model requests a tool call, executes it via vscode.lm.invokeTool.
     */
    private async streamResponseWithTools(
        request: vscode.ChatRequest,
        messages: vscode.LanguageModelChatMessage[],
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        // Get MCP tools (effi-local tools are tagged or we can use all)
        const tools = vscode.lm.tools;
        console.log(`Chat participant has access to ${tools.length} tools`);

        // Convert to chat tool format for the model
        const chatTools: vscode.LanguageModelChatTool[] = tools.map(tool => ({
            name: tool.name,
            description: tool.description,
            inputSchema: tool.inputSchema as Record<string, unknown> | undefined
        }));

        // Send request with tools available
        const response = await request.model.sendRequest(
            messages,
            { tools: chatTools },
            token
        );

        // Process the response stream
        for await (const part of response.stream) {
            if (part instanceof vscode.LanguageModelTextPart) {
                // Regular text - stream it
                stream.markdown(part.value);
            } else if (part instanceof vscode.LanguageModelToolCallPart) {
                // Model wants to call a tool!
                console.log(`Tool call requested: ${part.name}`, part.input);
                
                try {
                    // Execute the tool via VS Code's tool invocation
                    const toolResult = await vscode.lm.invokeTool(part.name, {
                        input: part.input,
                        toolInvocationToken: request.toolInvocationToken
                    }, token);

                    // Show the tool result to the user
                    stream.markdown(`\n\n**Tool executed:** ${part.name}\n`);
                    
                    // Extract text from tool result
                    for (const resultPart of toolResult.content) {
                        if (resultPart instanceof vscode.LanguageModelTextPart) {
                            stream.markdown(resultPart.value);
                        }
                    }
                } catch (toolError) {
                    stream.markdown(`\n\n**Tool error:** ${(toolError as Error).message}`);
                }
            }
        }
    }

    /**
     * Send request to LLM and stream response fragments (no tools)
     */
    private async streamResponse(
        model: vscode.LanguageModelChat,
        messages: vscode.LanguageModelChatMessage[],
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<void> {
        const response = await model.sendRequest(messages, {}, token);

        try {
            for await (const fragment of response.text) {
                stream.markdown(fragment);
            }
        } catch (streamError) {
            // Handle streaming errors separately
            stream.markdown(`\n\n**Error:** Streaming interrupted: ${(streamError as Error).message}`);
        }
    }

    /**
     * Handle errors and display user-friendly messages
     */
    private handleError(error: unknown, stream: vscode.ChatResponseStream): void {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        
        if (error instanceof vscode.LanguageModelError) {
            // Handle specific LLM errors
            switch (error.code) {
                case 'NoAccess':
                    stream.markdown('**Error:** Access denied. Please ensure you have consented to use the language model.');
                    break;
                case 'Blocked':
                    stream.markdown('**Error:** Request was blocked. Please try rephrasing your question.');
                    break;
                default:
                    stream.markdown(`**Error:** ${error.message}`);
            }
        } else {
            stream.markdown(`**Error:** ${errorMessage}`);
        }
    }
}
