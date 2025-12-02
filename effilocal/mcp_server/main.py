"""
Main entry point for the effilocal MCP Server.

This is the effilocal-customized MCP server that uses:
- Upstream word_document_server tools (pass-through where not overridden)
- effilocal override modules with extended functionality
- effilocal-specific tools (attachment, numbering, review)

All imports are from effilocal.mcp_server which provides the override pattern,
ensuring contract-specific enhancements while maintaining upstream compatibility.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging to stderr so MCP stdio parser isn't broken by plain prints
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Loading configuration from .env file...")
load_dotenv()
# Set required environment variable for FastMCP 2.8.1+
os.environ.setdefault('FASTMCP_LOG_LEVEL', 'INFO')

from fastmcp import FastMCP

# Import from effilocal override modules (which import from upstream where appropriate)
from effilocal.mcp_server.tools import (
    document_tools,
    content_tools,
    format_tools,
    comment_tools,
    attachment_tools,
    numbering_tools,
    review_tools,
    relationship_tools,
    clause_editing_tools,
)

# Import directly from upstream for tools we don't override
from word_document_server.tools import (
    protection_tools,
    footnote_tools,
    extended_document_tools,
)


def get_transport_config():
    """
    Get transport configuration from environment variables.
    
    Returns:
        dict: Transport configuration with type, host, port, and other settings
    """
    # Default configuration
    config = {
        'transport': 'stdio',  # Default to stdio for backward compatibility
        'host': '0.0.0.0',
        'port': 8000,
        'path': '/mcp',
        'sse_path': '/sse'
    }
    
    # Override with environment variables if provided
    transport = os.getenv('MCP_TRANSPORT', 'stdio').lower()
    print(f"Transport: {transport}")
    
    # Validate transport type
    valid_transports = ['stdio', 'streamable-http', 'sse']
    if transport not in valid_transports:
        print(f"Warning: Invalid transport '{transport}'. Falling back to 'stdio'.")
        transport = 'stdio'
    
    config['transport'] = transport
    config['host'] = os.getenv('MCP_HOST', config['host'])
    # Use PORT from Render if available, otherwise fall back to MCP_PORT or default
    config['port'] = int(os.getenv('PORT', os.getenv('MCP_PORT', config['port'])))
    config['path'] = os.getenv('MCP_PATH', config['path'])
    config['sse_path'] = os.getenv('MCP_SSE_PATH', config['sse_path'])
    
    return config


def setup_logging(debug_mode):
    """
    Setup logging based on debug mode.
    
    Args:
        debug_mode (bool): Whether to enable debug logging
    """
    import logging
    
    if debug_mode:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        print("Debug logging enabled")
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )


# Initialize FastMCP server
mcp = FastMCP("effilocal Document Server")


def register_tools():
    """Register all tools with the MCP server using FastMCP decorators."""
    
    # ========================================================================
    # Document tools (create, copy, info, etc.)
    # ========================================================================
    
    @mcp.tool()
    def create_document(filename: str, title: str = None, author: str = None):
        """Create a new Word document with optional metadata."""
        return document_tools.create_document(filename, title, author)
    
    @mcp.tool()
    def copy_document(source_filename: str, destination_filename: str = None):
        """Create a copy of a Word document."""
        return document_tools.create_document_copy(source_filename, destination_filename)
    
    @mcp.tool()
    def get_document_info(filename: str):
        """Get information about a Word document."""
        return document_tools.get_document_info(filename)
    
    @mcp.tool()
    def get_document_text(filename: str):
        """Extract all text from a Word document."""
        return document_tools.get_document_text(filename)
    
    @mcp.tool()
    def get_document_outline(filename: str):
        """Get the structure of a Word document."""
        return document_tools.get_document_outline(filename)
    
    @mcp.tool()
    def list_available_documents(directory: str = "."):
        """List all .docx files in the specified directory."""
        return document_tools.list_available_documents(directory)
    
    @mcp.tool()
    async def save_document_as_markdown(filename: str):
        """Extract all text from a Word document and save as a Markdown (.md) file."""
        return await document_tools.save_document_as_markdown(filename)
    
    # ========================================================================
    # Content tools (paragraphs, headings, tables, etc.)
    # ========================================================================
    
    @mcp.tool()
    async def add_paragraph(filename: str, text: str, style: str = None,
                      font_name: str = None, font_size: int = None,
                      bold: bool = None, italic: bool = None, color: str = None):
        """Add a paragraph to a Word document with optional formatting."""
        return await content_tools.add_paragraph(
            filename, text, style, font_name, font_size, bold, italic, color
        )
    
    @mcp.tool()
    async def add_heading(filename: str, text: str, level: int = 1,
                    font_name: str = None, font_size: int = None,
                    bold: bool = None, italic: bool = None,
                    border_bottom: bool = False, color: str = None):
        """Add a heading to a Word document with optional formatting including color."""
        return await content_tools.add_heading(
            filename, text, level, font_name, font_size, bold, italic, border_bottom,
            color=color
        )
    
    @mcp.tool()
    async def add_picture(filename: str, image_path: str, width: float = None):
        """Add an image to a Word document."""
        return await content_tools.add_picture(filename, image_path, width)
    
    @mcp.tool()
    async def add_table(filename: str, rows: int, cols: int, data: list = None):
        """Add a table to a Word document."""
        return await content_tools.add_table(filename, rows, cols, data)
    
    @mcp.tool()
    async def add_page_break(filename: str):
        """Add a page break to the document."""
        return await content_tools.add_page_break(filename)
    
    @mcp.tool()
    async def delete_paragraph(filename: str, paragraph_index: int):
        """Delete a paragraph from a document."""
        return await content_tools.delete_paragraph(filename, paragraph_index)
    
    @mcp.tool()
    async def search_and_replace(filename: str, find_text: str, replace_text: str, 
                                 whole_word_only: bool = False):
        """Search for text and replace all occurrences with optional whole-word matching."""
        return await content_tools.search_and_replace(filename, find_text, replace_text, whole_word_only)
    
    @mcp.tool()
    async def edit_run_text(filename: str, paragraph_index: int, run_index: int, new_text: str, 
                     start_offset: int = None, end_offset: int = None):
        """Edit text within a specific run of a paragraph."""
        return await content_tools.edit_run_text_tool(
            filename, paragraph_index, run_index, new_text, start_offset, end_offset
        )
    
    @mcp.tool()
    async def insert_header_near_text(filename: str, target_text: str = None, header_title: str = None, 
                                position: str = 'after', header_style: str = 'Heading 1', 
                                target_paragraph_index: int = None):
        """Insert a header near target text or at a specific paragraph index."""
        return await content_tools.insert_header_near_text_tool(
            filename, target_text, header_title, position, header_style, target_paragraph_index
        )
    
    @mcp.tool()
    async def insert_line_or_paragraph_near_text(filename: str, target_text: str = None, 
                                           line_text: str = None, position: str = 'after', 
                                           line_style: str = None, target_paragraph_index: int = None):
        """Insert a new line or paragraph near target text or at a specific paragraph index."""
        return await content_tools.insert_line_or_paragraph_near_text_tool(
            filename, target_text, line_text, position, line_style, target_paragraph_index
        )
    
    @mcp.tool()
    async def insert_numbered_list_near_text(filename: str, target_text: str = None, 
                                       list_items: list = None, position: str = 'after', 
                                       target_paragraph_index: int = None, bullet_type: str = 'bullet'):
        """Insert a bulleted or numbered list near target text or at a specific paragraph index."""
        return await content_tools.insert_numbered_list_near_text_tool(
            filename, target_text, list_items, position, target_paragraph_index, bullet_type
        )
    
    @mcp.tool()
    async def replace_block_between_manual_anchors(filename: str, start_anchor_text: str, 
                                              new_paragraphs: list, end_anchor_text: str = None, 
                                              new_paragraph_style: str = None):
        """Replace all content between start and end anchor text."""
        return await content_tools.replace_block_between_manual_anchors_tool(
            filename, start_anchor_text, new_paragraphs, end_anchor_text, None, new_paragraph_style
        )
    
    # ========================================================================
    # Format tools (styling, text formatting, etc.)
    # ========================================================================
    
    @mcp.tool()
    async def create_custom_style(filename: str, style_name: str, bold: bool = None, 
                          italic: bool = None, font_size: int = None, 
                          font_name: str = None, color: str = None, 
                          base_style: str = None):
        """Create a custom style in the document."""
        return await format_tools.create_custom_style(
            filename, style_name, bold, italic, font_size, font_name, color, base_style
        )
    
    @mcp.tool()
    async def format_text(filename: str, paragraph_index: int, start_pos: int, end_pos: int,
                   bold: bool = None, italic: bool = None, underline: bool = None,
                   color: str = None, font_size: int = None, font_name: str = None):
        """Format a specific range of text within a paragraph."""
        return await format_tools.format_text(
            filename, paragraph_index, start_pos, end_pos, bold, italic, 
            underline, color, font_size, font_name
        )
    
    @mcp.tool()
    async def set_background_highlight(filename: str, paragraph_index: int, start_pos: int, end_pos: int,
                                 color: str = "0000FF", use_shading: bool = True):
        """Apply background highlighting to a span of text within a paragraph."""
        return await format_tools.set_background_highlight(
            filename, paragraph_index, start_pos, end_pos, color, use_shading
        )
    
    @mcp.tool()
    def get_document_runs(filename: str, paragraph_index: int):
        """Get a snapshot of all runs in a paragraph for debugging formatting."""
        return format_tools.get_document_runs(filename, paragraph_index)
    
    # ========================================================================
    # Comment tools (from effilocal with status support)
    # ========================================================================
    
    @mcp.tool()
    async def get_all_comments(filename: str):
        """Extract all comments from a Word document including status (active/resolved)."""
        return await comment_tools.get_all_comments(filename)
    
    @mcp.tool()
    async def get_comments_by_author(filename: str, author: str):
        """Extract comments from a specific author in a Word document."""
        return await comment_tools.get_comments_by_author(filename, author)
    
    @mcp.tool()
    async def get_comments_for_paragraph(filename: str, paragraph_index: int):
        """Extract comments for a specific paragraph in a Word document."""
        return await comment_tools.get_paragraph_comments(filename, paragraph_index)
    
    @mcp.tool()
    async def add_comment_after_text(filename: str, search_text: str, comment_text: str,
                               author: str = None, initials: str = None):
        """Add a Word comment to the first occurrence of search_text."""
        return await comment_tools.add_comment_after_text(
            filename, search_text, comment_text, author, initials
        )
    
    @mcp.tool()
    async def add_comment_for_paragraph(filename: str, paragraph_index: int, comment_text: str,
                                  author: str = None, initials: str = None):
        """Add a Word comment anchored to an entire paragraph."""
        return await comment_tools.add_comment_for_paragraph(
            filename, paragraph_index, comment_text, author, initials
        )
    
    @mcp.tool()
    async def update_comment(filename: str, comment_id: str, new_text: str):
        """Update the text of an existing comment."""
        return await comment_tools.update_comment(filename, comment_id, new_text)
    
    # ========================================================================
    # Numbering analysis tools (effilocal-specific)
    # ========================================================================
    
    @mcp.tool()
    def analyze_document_numbering(filename: str, debug: bool = False, 
                                   include_non_numbered: bool = False):
        """Analyze the numbering structure of a Word document using NumberingInspector."""
        return numbering_tools.analyze_document_numbering(filename, debug, include_non_numbered)
    
    @mcp.tool()
    def get_numbering_summary(filename: str):
        """Get a high-level summary of numbering styles used in a document."""
        return numbering_tools.get_numbering_summary(filename)
    
    @mcp.tool()
    def extract_outline_structure(filename: str, max_level: int = None):
        """Extract the document outline based on numbering structure."""
        return numbering_tools.extract_outline_structure(filename, max_level)
    
    # ========================================================================
    # Relationship tools (artifact-level analysis)
    # ========================================================================

    @mcp.tool()
    def get_relationship_metadata(
        analysis_dir: str,
        block_id: str,
        include_block_details: bool = False,
    ):
        """Get relationship metadata for a block using precomputed artifacts."""
        return relationship_tools.get_relationship_metadata(
            analysis_dir, block_id, include_block_details
        )

    # ========================================================================
    # Clause-based paragraph insertion tools (effilocal contract-specific)
    # ========================================================================
    
    @mcp.tool()
    async def add_paragraph_after_clause(filename: str, clause_number: str, text: str,
                                   style: str = None, inherit_numbering: bool = True):
        """Add a paragraph after a specific clause number (e.g., '1.2.3', '7.1(a)')."""
        return await content_tools.add_paragraph_after_clause(
            filename, clause_number, text, style, inherit_numbering
        )
    
    @mcp.tool()
    async def add_paragraphs_after_clause(filename: str, clause_number: str, paragraphs: list,
                                    style: str = None, inherit_numbering: bool = True):
        """Add multiple paragraphs after a specific clause number."""
        return await content_tools.add_paragraphs_after_clause(
            filename, clause_number, paragraphs, style, inherit_numbering
        )
    
    # ========================================================================
    # Attachment-based paragraph insertion tools (effilocal contract-specific)
    # ========================================================================
    
    @mcp.tool()
    async def add_paragraph_after_attachment(filename: str, attachment_identifier: str, text: str,
                                       style: str = None, inherit_numbering: bool = True):
        """Add a paragraph after a specific attachment (Schedule, Annex, Exhibit, etc.)."""
        return await attachment_tools.add_paragraph_after_attachment(
            filename, attachment_identifier, text, style, inherit_numbering
        )
    
    @mcp.tool()
    async def add_paragraphs_after_attachment(filename: str, attachment_identifier: str, 
                                        paragraphs: list, style: str = None, 
                                        inherit_numbering: bool = True):
        """Add multiple paragraphs after a specific attachment."""
        return await attachment_tools.add_paragraphs_after_attachment(
            filename, attachment_identifier, paragraphs, style, inherit_numbering
        )
    
    @mcp.tool()
    async def add_new_attachment_after(filename: str, after_attachment: str, 
                                 new_attachment_text: str, content: str = None):
        """Add a new attachment (Schedule, Annex, Exhibit) after an existing attachment."""
        return await attachment_tools.add_new_attachment_after(
            filename, after_attachment, new_attachment_text, content
        )
    
    # ========================================================================
    # Protection tools (upstream pass-through)
    # ========================================================================
    
    @mcp.tool()
    async def protect_document(filename: str, password: str):
        """Add password protection to a Word document."""
        return await protection_tools.protect_document(filename, password)
    
    @mcp.tool()
    async def unprotect_document(filename: str, password: str):
        """Remove password protection from a Word document."""
        return await protection_tools.unprotect_document(filename, password)
    
    # ========================================================================
    # Footnote tools (upstream pass-through)
    # ========================================================================
    
    @mcp.tool()
    async def add_footnote_to_document(filename: str, paragraph_index: int, footnote_text: str):
        """Add a footnote to a specific paragraph in a Word document."""
        return await footnote_tools.add_footnote_to_document(filename, paragraph_index, footnote_text)
    
    @mcp.tool()
    async def add_footnote_after_text(filename: str, search_text: str, footnote_text: str, 
                               output_filename: str = None):
        """Add a footnote after specific text with proper superscript formatting."""
        return await footnote_tools.add_footnote_after_text(
            filename, search_text, footnote_text, output_filename
        )
    
    @mcp.tool()
    async def customize_footnote_style(filename: str, numbering_format: str = "1, 2, 3",
                                start_number: int = 1, font_name: str = None,
                                font_size: int = None):
        """Customize footnote numbering and formatting in a Word document."""
        return await footnote_tools.customize_footnote_style(
            filename, numbering_format, start_number, font_name, font_size
        )
    
    @mcp.tool()
    async def delete_footnote_from_document(filename: str, footnote_id: int = None,
                                     search_text: str = None, output_filename: str = None):
        """Delete a footnote from a Word document."""
        return await footnote_tools.delete_footnote_from_document(
            filename, footnote_id, search_text, output_filename
        )
    
    # ========================================================================
    # Extended document tools (upstream pass-through)
    # ========================================================================
    
    @mcp.tool()
    async def get_paragraph_text_from_document(filename: str, paragraph_index: int):
        """Get text from a specific paragraph in a Word document."""
        return await extended_document_tools.get_paragraph_text_from_document(filename, paragraph_index)
    
    @mcp.tool()
    async def find_text_in_document(filename: str, text_to_find: str, match_case: bool = True,
                             whole_word: bool = False):
        """Find occurrences of specific text in a Word document."""
        return await extended_document_tools.find_text_in_document(
            filename, text_to_find, match_case, whole_word
        )
    
    @mcp.tool()
    async def convert_to_pdf(filename: str, output_filename: str = None):
        """Convert a Word document to PDF format."""
        return await extended_document_tools.convert_to_pdf(filename, output_filename)
    
    # ========================================================================
    # Clause editing tools (ordinal-based editing with artifact loader)
    # ========================================================================
    
    @mcp.tool()
    async def replace_clause_text_by_ordinal(filename: str, clause_number: str, new_text: str, 
                                       analysis_dir: str = None):
        """Replace the text of a clause identified by its ordinal number (e.g., '3.2.1')."""
        return clause_editing_tools.replace_clause_text_by_ordinal(
            filename, clause_number, new_text, analysis_dir
        )
    
    @mcp.tool()
    async def insert_paragraph_after_clause(filename: str, clause_number: str, text: str,
                                     style: str = "Normal", inherit_numbering: bool = False,
                                     analysis_dir: str = None):
        """Insert a new paragraph after a clause identified by ordinal (e.g., '8.2')."""
        return clause_editing_tools.insert_paragraph_after_clause(
            filename, clause_number, text, style, inherit_numbering, analysis_dir
        )
    
    @mcp.tool()
    async def delete_clause_by_ordinal(filename: str, clause_number: str, analysis_dir: str = None):
        """Delete a clause and its continuations identified by ordinal (e.g., '12.5')."""
        return clause_editing_tools.delete_clause_by_ordinal(
            filename, clause_number, analysis_dir
        )
    
    @mcp.tool()
    async def get_clause_text_by_ordinal(filename: str, clause_number: str, 
                                   include_continuations: bool = True, analysis_dir: str = None):
        """Get the text of a clause by its ordinal number (e.g., '5.1')."""
        return clause_editing_tools.get_clause_text_by_ordinal(
            filename, clause_number, include_continuations, analysis_dir
        )
    
    @mcp.tool()
    async def list_all_clause_numbers(filename: str, analysis_dir: str = None):
        """List all clause ordinals in the document for discovery."""
        return clause_editing_tools.list_all_clause_numbers(filename, analysis_dir)

    # ========================================================================
    # Para ID tools (retrieval and replacement by paraId)
    # ========================================================================

    @mcp.tool()
    async def get_text_by_para_id(filename: str, para_id: str):
        """Get the text content of a paragraph identified by its paraId."""
        return await content_tools.get_text_by_para_id(filename, para_id)

    @mcp.tool()
    async def replace_text_by_para_id(filename: str, para_id: str, new_text: str):
        """Replace the entire text content of a paragraph identified by its paraId."""
        return await content_tools.replace_text_by_para_id(filename, para_id, new_text)


def run_server():
    """Run the effilocal Document MCP Server with configurable transport."""
    # Get transport configuration
    config = get_transport_config()
    
    # Register all tools
    register_tools()
    
    # Print startup information
    transport_type = config['transport']
    print(f"Starting effilocal Document MCP Server with {transport_type} transport...")
    
    try:
        if transport_type == 'stdio':
            # Run with stdio transport (default, backward compatible)
            print("Server running on stdio transport")
            mcp.run(transport='stdio')
            
        elif transport_type == 'streamable-http':
            # Run with streamable HTTP transport
            print(f"Server running on streamable-http transport at http://{config['host']}:{config['port']}{config['path']}")
            mcp.run(
                transport='streamable-http',
                host=config['host'],
                port=config['port'],
                path=config['path']
            )
            
        elif transport_type == 'sse':
            # Run with SSE transport
            print(f"Server running on SSE transport at http://{config['host']}:{config['port']}{config['sse_path']}")
            mcp.run(
                transport='sse',
                host=config['host'],
                port=config['port'],
                path=config['sse_path']
            )
            
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    return mcp


def main():
    """Main entry point for the server."""
    run_server()


if __name__ == "__main__":
    main()
