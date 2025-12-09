/**
 * Markdown Rendering Tests
 * 
 * Tests for markdown rendering in the Plan panel.
 * Task descriptions support markdown syntax which should be:
 * 1. Parsed via the marked library
 * 2. Sanitized to prevent XSS attacks
 * 3. Rendered as HTML in the task description element
 * 
 * TDD Approach: These tests are written to FAIL initially.
 * Implement the feature to make them pass.
 */

// Mock marked library for Node.js test environment
const { marked } = require('marked');

// Set up global marked before importing plan.js
global.marked = marked;

// Import the functions we'll test
// These will be exported from plan.js after implementation
const { 
    sanitizeMarkdownHtml,
    renderMarkdown,
    ALLOWED_TAGS,
    ALLOWED_ATTRIBUTES
} = require('../plan.js');

describe('Markdown Rendering', () => {
    
    describe('sanitizeMarkdownHtml', () => {
        
        describe('allowed tags', () => {
            test('should allow paragraph tags', () => {
                const input = '<p>Hello world</p>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).toBe('<p>Hello world</p>');
            });
            
            test('should allow strong/bold tags', () => {
                const input = '<strong>bold text</strong>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).toBe('<strong>bold text</strong>');
            });
            
            test('should allow em/italic tags', () => {
                const input = '<em>italic text</em>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).toBe('<em>italic text</em>');
            });
            
            test('should allow code tags', () => {
                const input = '<code>const x = 1;</code>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).toBe('<code>const x = 1;</code>');
            });
            
            test('should allow pre tags', () => {
                const input = '<pre>multiline\ncode</pre>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).toBe('<pre>multiline\ncode</pre>');
            });
            
            test('should allow unordered list tags', () => {
                const input = '<ul><li>item 1</li><li>item 2</li></ul>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).toBe('<ul><li>item 1</li><li>item 2</li></ul>');
            });
            
            test('should allow ordered list tags', () => {
                const input = '<ol><li>first</li><li>second</li></ol>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).toBe('<ol><li>first</li><li>second</li></ol>');
            });
            
            test('should allow anchor tags with href', () => {
                const input = '<a href="https://example.com">link</a>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).toBe('<a href="https://example.com">link</a>');
            });
            
            test('should allow br tags', () => {
                const input = 'line1<br>line2';
                const result = sanitizeMarkdownHtml(input);
                expect(result).toBe('line1<br>line2');
            });
            
            test('should allow heading tags h1-h6', () => {
                const input = '<h1>Title</h1><h2>Subtitle</h2>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).toBe('<h1>Title</h1><h2>Subtitle</h2>');
            });
            
            test('should allow blockquote tags', () => {
                const input = '<blockquote>quoted text</blockquote>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).toBe('<blockquote>quoted text</blockquote>');
            });
        });
        
        describe('disallowed tags', () => {
            test('should strip script tags', () => {
                const input = '<script>alert("xss")</script>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).not.toContain('<script');
                expect(result).not.toContain('alert');
            });
            
            test('should strip style tags', () => {
                const input = '<style>body{display:none}</style>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).not.toContain('<style');
            });
            
            test('should strip iframe tags', () => {
                const input = '<iframe src="evil.com"></iframe>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).not.toContain('<iframe');
            });
            
            test('should strip object tags', () => {
                const input = '<object data="evil.swf"></object>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).not.toContain('<object');
            });
            
            test('should strip embed tags', () => {
                const input = '<embed src="evil.swf">';
                const result = sanitizeMarkdownHtml(input);
                expect(result).not.toContain('<embed');
            });
            
            test('should strip form tags', () => {
                const input = '<form action="evil.com"><input></form>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).not.toContain('<form');
            });
            
            test('should strip img tags (potential XSS vector)', () => {
                const input = '<img src="x" onerror="alert(1)">';
                const result = sanitizeMarkdownHtml(input);
                expect(result).not.toContain('<img');
                expect(result).not.toContain('onerror');
            });
        });
        
        describe('dangerous attributes', () => {
            test('should strip onclick attributes', () => {
                const input = '<p onclick="alert(1)">text</p>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).not.toContain('onclick');
                expect(result).toContain('<p>text</p>');
            });
            
            test('should strip onmouseover attributes', () => {
                const input = '<a href="#" onmouseover="alert(1)">link</a>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).not.toContain('onmouseover');
            });
            
            test('should strip onerror attributes', () => {
                const input = '<p onerror="alert(1)">text</p>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).not.toContain('onerror');
            });
            
            test('should strip javascript: URLs in href', () => {
                const input = '<a href="javascript:alert(1)">link</a>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).not.toContain('javascript:');
            });
            
            test('should strip data: URLs in href', () => {
                const input = '<a href="data:text/html,<script>alert(1)</script>">link</a>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).not.toContain('data:');
            });
            
            test('should allow safe href URLs', () => {
                const input = '<a href="https://example.com">link</a>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).toContain('href="https://example.com"');
            });
            
            test('should allow relative href URLs', () => {
                const input = '<a href="/path/to/page">link</a>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).toContain('href="/path/to/page"');
            });
        });
        
        describe('edge cases', () => {
            test('should handle empty string', () => {
                expect(sanitizeMarkdownHtml('')).toBe('');
            });
            
            test('should handle null input', () => {
                expect(sanitizeMarkdownHtml(null)).toBe('');
            });
            
            test('should handle undefined input', () => {
                expect(sanitizeMarkdownHtml(undefined)).toBe('');
            });
            
            test('should handle plain text without tags', () => {
                const input = 'Just plain text';
                expect(sanitizeMarkdownHtml(input)).toBe('Just plain text');
            });
            
            test('should handle nested allowed tags', () => {
                const input = '<ul><li><strong>bold</strong> and <em>italic</em></li></ul>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).toBe('<ul><li><strong>bold</strong> and <em>italic</em></li></ul>');
            });
            
            test('should handle mixed allowed and disallowed tags', () => {
                const input = '<p>Hello</p><script>evil()</script><p>World</p>';
                const result = sanitizeMarkdownHtml(input);
                expect(result).toContain('<p>Hello</p>');
                expect(result).toContain('<p>World</p>');
                expect(result).not.toContain('<script');
            });
            
            test('should preserve text content when stripping tags', () => {
                const input = '<div>Some <span>text</span> here</div>';
                const result = sanitizeMarkdownHtml(input);
                // div and span are stripped, but text content preserved
                expect(result).toContain('Some');
                expect(result).toContain('text');
                expect(result).toContain('here');
            });
        });
    });
    
    describe('renderMarkdown', () => {
        
        test('should render bold text', () => {
            const result = renderMarkdown('**bold**');
            expect(result).toContain('<strong>bold</strong>');
        });
        
        test('should render italic text', () => {
            const result = renderMarkdown('*italic*');
            expect(result).toContain('<em>italic</em>');
        });
        
        test('should render inline code', () => {
            const result = renderMarkdown('`code`');
            expect(result).toContain('<code>code</code>');
        });
        
        test('should render code blocks', () => {
            const result = renderMarkdown('```\ncode block\n```');
            expect(result).toContain('<pre>');
            expect(result).toContain('<code>');
            expect(result).toContain('code block');
        });
        
        test('should render unordered lists', () => {
            const result = renderMarkdown('- item 1\n- item 2');
            expect(result).toContain('<ul>');
            expect(result).toContain('<li>');
            expect(result).toContain('item 1');
            expect(result).toContain('item 2');
        });
        
        test('should render ordered lists', () => {
            const result = renderMarkdown('1. first\n2. second');
            expect(result).toContain('<ol>');
            expect(result).toContain('<li>');
            expect(result).toContain('first');
            expect(result).toContain('second');
        });
        
        test('should render links', () => {
            const result = renderMarkdown('[link text](https://example.com)');
            expect(result).toContain('<a');
            expect(result).toContain('href="https://example.com"');
            expect(result).toContain('link text');
        });
        
        test('should render headings', () => {
            const result = renderMarkdown('# Heading 1\n## Heading 2');
            expect(result).toContain('<h1');
            expect(result).toContain('Heading 1');
            expect(result).toContain('<h2');
            expect(result).toContain('Heading 2');
        });
        
        test('should render blockquotes', () => {
            const result = renderMarkdown('> quoted text');
            expect(result).toContain('<blockquote>');
            expect(result).toContain('quoted text');
        });
        
        test('should sanitize the output', () => {
            // Markdown that produces unsafe HTML
            const result = renderMarkdown('[click me](javascript:alert(1))');
            expect(result).not.toContain('javascript:');
        });
        
        test('should handle empty string', () => {
            expect(renderMarkdown('')).toBe('');
        });
        
        test('should handle null', () => {
            expect(renderMarkdown(null)).toBe('');
        });
        
        test('should handle undefined', () => {
            expect(renderMarkdown(undefined)).toBe('');
        });
        
        test('should handle plain text', () => {
            const result = renderMarkdown('Just plain text');
            expect(result).toContain('Just plain text');
        });
        
        test('should handle complex markdown', () => {
            const markdown = `
## Task Description

This task involves:
- **Important** item
- *Secondary* item
- Regular item

See [documentation](https://docs.example.com) for details.

\`\`\`javascript
const x = 1;
\`\`\`
`;
            const result = renderMarkdown(markdown);
            expect(result).toContain('<h2');
            expect(result).toContain('<ul>');
            expect(result).toContain('<strong>Important</strong>');
            expect(result).toContain('<em>Secondary</em>');
            expect(result).toContain('<a');
            expect(result).toContain('<pre>');
        });
    });
    
    describe('ALLOWED_TAGS constant', () => {
        test('should be an array', () => {
            expect(Array.isArray(ALLOWED_TAGS)).toBe(true);
        });
        
        test('should include common formatting tags', () => {
            expect(ALLOWED_TAGS).toContain('p');
            expect(ALLOWED_TAGS).toContain('strong');
            expect(ALLOWED_TAGS).toContain('em');
            expect(ALLOWED_TAGS).toContain('code');
            expect(ALLOWED_TAGS).toContain('pre');
        });
        
        test('should include list tags', () => {
            expect(ALLOWED_TAGS).toContain('ul');
            expect(ALLOWED_TAGS).toContain('ol');
            expect(ALLOWED_TAGS).toContain('li');
        });
        
        test('should include link and heading tags', () => {
            expect(ALLOWED_TAGS).toContain('a');
            expect(ALLOWED_TAGS).toContain('h1');
            expect(ALLOWED_TAGS).toContain('h2');
            expect(ALLOWED_TAGS).toContain('h3');
        });
        
        test('should NOT include dangerous tags', () => {
            expect(ALLOWED_TAGS).not.toContain('script');
            expect(ALLOWED_TAGS).not.toContain('style');
            expect(ALLOWED_TAGS).not.toContain('iframe');
            expect(ALLOWED_TAGS).not.toContain('object');
            expect(ALLOWED_TAGS).not.toContain('embed');
            expect(ALLOWED_TAGS).not.toContain('form');
            expect(ALLOWED_TAGS).not.toContain('input');
        });
    });
    
    describe('ALLOWED_ATTRIBUTES constant', () => {
        test('should be an object', () => {
            expect(typeof ALLOWED_ATTRIBUTES).toBe('object');
        });
        
        test('should allow href on anchor tags', () => {
            expect(ALLOWED_ATTRIBUTES.a).toContain('href');
        });
        
        test('should NOT allow event handlers', () => {
            const allAttrs = Object.values(ALLOWED_ATTRIBUTES).flat();
            expect(allAttrs).not.toContain('onclick');
            expect(allAttrs).not.toContain('onmouseover');
            expect(allAttrs).not.toContain('onerror');
            expect(allAttrs).not.toContain('onload');
        });
    });
});

describe('PlanPanel markdown integration', () => {
    
    // These tests verify that renderMarkdown produces the expected output
    // that would be assigned to innerHTML in _renderTask
    
    test('task description should use innerHTML when markdown is present', () => {
        // Simulates what _renderTask does:
        // descEl.innerHTML = renderMarkdown(task.description)
        const description = '**Bold** and *italic*';
        const result = renderMarkdown(description);
        
        // Should produce proper HTML, not escaped markdown
        expect(result).toContain('<strong>Bold</strong>');
        expect(result).toContain('<em>italic</em>');
    });
    
    test('task description should sanitize markdown output', () => {
        // If markdown contains script tags, they should be stripped
        const description = '<script>alert(1)</script>Normal text';
        const result = renderMarkdown(description);
        
        expect(result).not.toContain('<script>');
        expect(result).toContain('Normal text');
    });
    
    test('empty description should return empty string', () => {
        // Empty descriptions are handled by _renderTask using placeholder text
        // but renderMarkdown should just return empty string
        expect(renderMarkdown('')).toBe('');
        expect(renderMarkdown(null)).toBe('');
        expect(renderMarkdown(undefined)).toBe('');
    });
});
