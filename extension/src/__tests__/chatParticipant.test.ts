/**
 * Tests for EffiChatParticipant
 * 
 * Tests the chat participant that provides contract-aware LLM responses
 * via VS Code's Chat Participant API.
 */

// Mock vscode module before imports
jest.mock('vscode', () => ({
    LanguageModelChatMessage: {
        User: jest.fn((content: string) => ({ role: 'user', content })),
        Assistant: jest.fn((content: string) => ({ role: 'assistant', content }))
    },
    LanguageModelError: class LanguageModelError extends Error {
        code: string;
        constructor(message: string, code?: string) {
            super(message);
            this.code = code || 'Unknown';
        }
    },
    LanguageModelTextPart: class LanguageModelTextPart {
        value: string;
        constructor(value: string) {
            this.value = value;
        }
    },
    LanguageModelToolCallPart: class LanguageModelToolCallPart {
        name: string;
        input: any;
        constructor(name: string, input: any) {
            this.name = name;
            this.input = input;
        }
    },
    lm: {
        tools: [],  // Empty tools array for tests
        invokeTool: jest.fn()
    }
}), { virtual: true });

import { EffiChatParticipant } from '../chatParticipant';
import * as vscode from 'vscode';

// ============================================================================
// Mock Types
// ============================================================================

interface MockChatRequest {
    prompt: string;
    command?: string;
    model: MockLanguageModel;
    toolInvocationToken?: any;
}

interface MockChatContext {
    history: any[];
}

interface MockChatResponseStream {
    markdown: jest.Mock;
    progress: jest.Mock;
    reference: jest.Mock;
    button: jest.Mock;
}

interface MockLanguageModel {
    sendRequest: jest.Mock;
    id: string;
    name: string;
    vendor: string;
    family: string;
    version: string;
    maxInputTokens: number;
}

interface MockLanguageModelResponse {
    text: AsyncIterable<string>;
    stream: AsyncIterable<any>;  // Stream of LanguageModelTextPart or LanguageModelToolCallPart
}

// ============================================================================
// Helper Functions
// ============================================================================

function createMockStream(): MockChatResponseStream {
    return {
        markdown: jest.fn(),
        progress: jest.fn(),
        reference: jest.fn(),
        button: jest.fn()
    };
}

function createMockModel(responseFragments: string[] = ['Hello', ' world']): MockLanguageModel {
    // Create text parts for the stream
    const textParts = responseFragments.map(fragment => {
        const part = new (vscode as any).LanguageModelTextPart(fragment);
        return part;
    });

    const mockResponse: MockLanguageModelResponse = {
        text: (async function* () {
            for (const fragment of responseFragments) {
                yield fragment;
            }
        })(),
        stream: (async function* () {
            for (const part of textParts) {
                yield part;
            }
        })()
    };

    return {
        sendRequest: jest.fn().mockResolvedValue(mockResponse),
        id: 'copilot-gpt-4o',
        name: 'GPT-4o',
        vendor: 'copilot',
        family: 'gpt-4o',
        version: '1.0',
        maxInputTokens: 64000
    };
}

function createMockRequest(prompt: string, model?: MockLanguageModel): MockChatRequest {
    return {
        prompt,
        model: model || createMockModel(),
        toolInvocationToken: { /* mock token */ } as any
    };
}

function createMockContext(): MockChatContext {
    return {
        history: []
    };
}

function createMockToken(): vscode.CancellationToken {
    return {
        isCancellationRequested: false,
        onCancellationRequested: jest.fn()
    };
}

// ============================================================================
// Test Suite: EffiChatParticipant Class
// ============================================================================

describe('EffiChatParticipant', () => {
    
    // ------------------------------------------------------------------------
    // Constructor Tests
    // ------------------------------------------------------------------------
    
    describe('constructor', () => {
        it('should create instance with document path callback', () => {
            const getDocPath = () => '/path/to/doc.docx';
            const participant = new EffiChatParticipant(getDocPath);
            
            expect(participant).toBeInstanceOf(EffiChatParticipant);
        });

        it('should create instance with undefined document path callback', () => {
            const getDocPath = () => undefined;
            const participant = new EffiChatParticipant(getDocPath);
            
            expect(participant).toBeInstanceOf(EffiChatParticipant);
        });
    });

    // ------------------------------------------------------------------------
    // getHandler Tests
    // ------------------------------------------------------------------------
    
    describe('getHandler', () => {
        it('should return a function', () => {
            const participant = new EffiChatParticipant(() => undefined);
            const handler = participant.getHandler();
            
            expect(typeof handler).toBe('function');
        });

        it('should return the same handler on multiple calls', () => {
            const participant = new EffiChatParticipant(() => undefined);
            const handler1 = participant.getHandler();
            const handler2 = participant.getHandler();
            
            expect(handler1).toBe(handler2);
        });
    });

    // ------------------------------------------------------------------------
    // Handler Execution Tests
    // ------------------------------------------------------------------------
    
    describe('handler execution', () => {
        it('should call model.sendRequest with messages', async () => {
            const participant = new EffiChatParticipant(() => undefined);
            const handler = participant.getHandler();
            
            const model = createMockModel(['Test response']);
            const request = createMockRequest('What is this contract about?', model);
            const context = createMockContext();
            const stream = createMockStream();
            const token = createMockToken();
            
            await handler(
                request as any,
                context as any,
                stream as any,
                token
            );
            
            expect(model.sendRequest).toHaveBeenCalledTimes(1);
        });

        it('should stream response fragments via stream.markdown', async () => {
            const participant = new EffiChatParticipant(() => undefined);
            const handler = participant.getHandler();
            
            const fragments = ['This ', 'is ', 'a ', 'test.'];
            const model = createMockModel(fragments);
            const request = createMockRequest('Summarize', model);
            const context = createMockContext();
            const stream = createMockStream();
            const token = createMockToken();
            
            await handler(
                request as any,
                context as any,
                stream as any,
                token
            );
            
            // Each fragment should be streamed
            expect(stream.markdown).toHaveBeenCalledTimes(fragments.length);
            fragments.forEach((fragment, index) => {
                expect(stream.markdown).toHaveBeenNthCalledWith(index + 1, fragment);
            });
        });

        it('should include user prompt in messages sent to model', async () => {
            const participant = new EffiChatParticipant(() => undefined);
            const handler = participant.getHandler();
            
            const model = createMockModel(['Response']);
            const userPrompt = 'What are the key obligations?';
            const request = createMockRequest(userPrompt, model);
            const context = createMockContext();
            const stream = createMockStream();
            const token = createMockToken();
            
            await handler(
                request as any,
                context as any,
                stream as any,
                token
            );
            
            // Check that sendRequest was called with messages containing user prompt
            const callArgs = model.sendRequest.mock.calls[0];
            const messages = callArgs[0];
            
            expect(messages).toBeInstanceOf(Array);
            expect(messages.length).toBeGreaterThan(0);
            
            // At least one message should contain the user prompt
            const hasUserPrompt = messages.some((msg: any) => 
                msg.content && msg.content.includes(userPrompt)
            );
            expect(hasUserPrompt).toBe(true);
        });
    });

    // ------------------------------------------------------------------------
    // Contract Context Tests
    // ------------------------------------------------------------------------
    
    describe('contract context handling', () => {
        it('should include contract context when document path is available', async () => {
            // Mock fs.existsSync and fs.readFileSync
            const mockContractText = 'This is a sample contract with terms and conditions.';
            const mockDocPath = '/path/to/contract.docx';
            
            const participant = new EffiChatParticipant(
                () => mockDocPath,
                () => mockContractText  // Context loader callback for testing
            );
            const handler = participant.getHandler();
            
            const model = createMockModel(['Response']);
            const request = createMockRequest('Summarize this', model);
            const context = createMockContext();
            const stream = createMockStream();
            const token = createMockToken();
            
            await handler(
                request as any,
                context as any,
                stream as any,
                token
            );
            
            // Check that contract context was included in messages
            const callArgs = model.sendRequest.mock.calls[0];
            const messages = callArgs[0];
            
            const hasContractContext = messages.some((msg: any) =>
                msg.content && msg.content.includes('This is a sample')
            );
            expect(hasContractContext).toBe(true);
        });

        it('should truncate context to 200 characters for PoC', async () => {
            // Use a distinctive marker to count
            const longText = 'X'.repeat(500);
            const mockDocPath = '/path/to/contract.docx';
            
            const participant = new EffiChatParticipant(
                () => mockDocPath,
                () => longText
            );
            const handler = participant.getHandler();
            
            const model = createMockModel(['Response']);
            const request = createMockRequest('Summarize', model);
            const context = createMockContext();
            const stream = createMockStream();
            const token = createMockToken();
            
            await handler(
                request as any,
                context as any,
                stream as any,
                token
            );
            
            // Check that context was truncated
            const callArgs = model.sendRequest.mock.calls[0];
            const messages = callArgs[0];
            
            // Find the message with contract context (X's are distinctive)
            const contextMessage = messages.find((msg: any) =>
                msg.content && msg.content.includes('XXX')
            );
            
            expect(contextMessage).toBeDefined();
            // Should contain exactly 200 X's (truncated from 500)
            const xCount = (contextMessage.content.match(/X/g) || []).length;
            expect(xCount).toBe(200);
        });

        it('should work without document context when path is undefined', async () => {
            const participant = new EffiChatParticipant(() => undefined);
            const handler = participant.getHandler();
            
            const model = createMockModel(['Response without context']);
            const request = createMockRequest('General question', model);
            const context = createMockContext();
            const stream = createMockStream();
            const token = createMockToken();
            
            await handler(
                request as any,
                context as any,
                stream as any,
                token
            );
            
            expect(model.sendRequest).toHaveBeenCalled();
            expect(stream.markdown).toHaveBeenCalledWith('Response without context');
        });

        it('should indicate no document loaded when path is undefined', async () => {
            const participant = new EffiChatParticipant(() => undefined);
            const handler = participant.getHandler();
            
            const model = createMockModel(['Response']);
            const request = createMockRequest('What is in the contract?', model);
            const context = createMockContext();
            const stream = createMockStream();
            const token = createMockToken();
            
            await handler(
                request as any,
                context as any,
                stream as any,
                token
            );
            
            // Check that system message mentions no document
            const callArgs = model.sendRequest.mock.calls[0];
            const messages = callArgs[0];
            
            const hasNoDocMessage = messages.some((msg: any) =>
                msg.content && msg.content.toLowerCase().includes('no document')
            );
            expect(hasNoDocMessage).toBe(true);
        });
    });

    // ------------------------------------------------------------------------
    // Error Handling Tests
    // ------------------------------------------------------------------------
    
    describe('error handling', () => {
        it('should handle model request errors gracefully', async () => {
            const participant = new EffiChatParticipant(() => undefined);
            const handler = participant.getHandler();
            
            const model = createMockModel([]);
            model.sendRequest.mockRejectedValue(new Error('Model unavailable'));
            
            const request = createMockRequest('Test', model);
            const context = createMockContext();
            const stream = createMockStream();
            const token = createMockToken();
            
            // Should not throw
            await expect(handler(
                request as any,
                context as any,
                stream as any,
                token
            )).resolves.not.toThrow();
            
            // Should display error message to user
            expect(stream.markdown).toHaveBeenCalledWith(
                expect.stringContaining('Error')
            );
        });

        it('should handle LanguageModelError for consent issues', async () => {
            const participant = new EffiChatParticipant(() => undefined);
            const handler = participant.getHandler();
            
            const model = createMockModel([]);
            const consentError = new Error('User consent required');
            (consentError as any).code = 'NoAccess';
            model.sendRequest.mockRejectedValue(consentError);
            
            const request = createMockRequest('Test', model);
            const context = createMockContext();
            const stream = createMockStream();
            const token = createMockToken();
            
            await handler(
                request as any,
                context as any,
                stream as any,
                token
            );
            
            expect(stream.markdown).toHaveBeenCalledWith(
                expect.stringContaining('Error')
            );
        });

        it('should handle streaming errors during response', async () => {
            const participant = new EffiChatParticipant(() => undefined);
            const handler = participant.getHandler();
            
            // Create a response that throws during iteration
            const errorResponse = {
                text: (async function* () {
                    yield 'Start...';
                    throw new Error('Network interrupted');
                })(),
                stream: (async function* () {
                    yield new (vscode as any).LanguageModelTextPart('Start...');
                    throw new Error('Network interrupted');
                })()
            };
            
            const model = createMockModel([]);
            model.sendRequest.mockResolvedValue(errorResponse);
            
            const request = createMockRequest('Test', model);
            const context = createMockContext();
            const stream = createMockStream();
            const token = createMockToken();
            
            await handler(
                request as any,
                context as any,
                stream as any,
                token
            );
            
            // Should have streamed the first fragment
            expect(stream.markdown).toHaveBeenCalledWith('Start...');
            
            // Should have shown error for the interruption
            expect(stream.markdown).toHaveBeenCalledWith(
                expect.stringContaining('Error')
            );
        });

        it('should handle context loading errors', async () => {
            const participant = new EffiChatParticipant(
                () => '/path/to/doc.docx',
                () => { throw new Error('File not found'); }
            );
            const handler = participant.getHandler();
            
            const model = createMockModel(['Response']);
            const request = createMockRequest('Summarize', model);
            const context = createMockContext();
            const stream = createMockStream();
            const token = createMockToken();
            
            // Should not throw
            await expect(handler(
                request as any,
                context as any,
                stream as any,
                token
            )).resolves.not.toThrow();
            
            // Should still call the model (without context)
            expect(model.sendRequest).toHaveBeenCalled();
        });
    });

    // ------------------------------------------------------------------------
    // Message Building Tests
    // ------------------------------------------------------------------------
    
    describe('message building', () => {
        it('should include system context about being a contract assistant', async () => {
            const participant = new EffiChatParticipant(() => undefined);
            const handler = participant.getHandler();
            
            const model = createMockModel(['Response']);
            const request = createMockRequest('Hello', model);
            const context = createMockContext();
            const stream = createMockStream();
            const token = createMockToken();
            
            await handler(
                request as any,
                context as any,
                stream as any,
                token
            );
            
            const callArgs = model.sendRequest.mock.calls[0];
            const messages = callArgs[0];
            
            // Should have context about being a contract assistant
            const hasAssistantContext = messages.some((msg: any) =>
                msg.content && (
                    msg.content.toLowerCase().includes('contract') ||
                    msg.content.toLowerCase().includes('legal') ||
                    msg.content.toLowerCase().includes('lawyer')
                )
            );
            expect(hasAssistantContext).toBe(true);
        });

        it('should pass cancellation token to model', async () => {
            const participant = new EffiChatParticipant(() => undefined);
            const handler = participant.getHandler();
            
            const model = createMockModel(['Response']);
            const request = createMockRequest('Test', model);
            const context = createMockContext();
            const stream = createMockStream();
            const token = createMockToken();
            
            await handler(
                request as any,
                context as any,
                stream as any,
                token
            );
            
            // Token should be passed as third argument to sendRequest
            const callArgs = model.sendRequest.mock.calls[0];
            expect(callArgs[2]).toBe(token);
        });
    });

    // ------------------------------------------------------------------------
    // Return Value Tests
    // ------------------------------------------------------------------------
    
    describe('return value', () => {
        it('should return a result object', async () => {
            const participant = new EffiChatParticipant(() => undefined);
            const handler = participant.getHandler();
            
            const model = createMockModel(['Response']);
            const request = createMockRequest('Test', model);
            const context = createMockContext();
            const stream = createMockStream();
            const token = createMockToken();
            
            const result = await handler(
                request as any,
                context as any,
                stream as any,
                token
            );
            
            expect(result).toBeDefined();
            expect(typeof result).toBe('object');
        });

        it('should include metadata in result', async () => {
            const participant = new EffiChatParticipant(() => '/path/to/doc.docx');
            const handler = participant.getHandler();
            
            const model = createMockModel(['Response']);
            const request = createMockRequest('Test', model);
            const context = createMockContext();
            const stream = createMockStream();
            const token = createMockToken();
            
            const result = await handler(
                request as any,
                context as any,
                stream as any,
                token
            );
            
            expect(result).toHaveProperty('metadata');
        });
    });
});

// ============================================================================
// Test Suite: Integration with VS Code Types
// ============================================================================

describe('EffiChatParticipant VS Code Integration', () => {
    it('should be compatible with vscode.ChatRequestHandler signature', () => {
        const participant = new EffiChatParticipant(() => undefined);
        const handler = participant.getHandler();
        
        // TypeScript would catch this at compile time, but we verify at runtime
        expect(handler.length).toBe(4); // (request, context, stream, token)
    });
});
