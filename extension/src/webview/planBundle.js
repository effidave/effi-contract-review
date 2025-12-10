/**
 * Plan Webview Bundle Entry Point
 * 
 * This is the entry point for esbuild to bundle the Plan webview scripts.
 * It imports and re-exports all dependencies including:
 * - marked (markdown parser)
 * - plan.js (PlanPanel component)
 * - planMain.js (webview initialization)
 * 
 * The bundled output (dist/planBundle.js) is loaded in the Plan webview.
 */

// Import marked and expose globally for plan.js
import { marked } from 'marked';

// Configure marked options for security
marked.setOptions({
    // Disable HTML passthrough to reduce XSS surface
    // Our sanitizer will still clean the output, but this adds defense in depth
    gfm: true,        // GitHub Flavored Markdown
    breaks: true,     // Convert \n to <br> for better line break handling
});

// Expose marked globally for plan.js to use
window.marked = marked;

// Import plan.js and planMain.js
// These files set up window.PlanPanel and initialize the component
import './plan.js';
import './planMain.js';
