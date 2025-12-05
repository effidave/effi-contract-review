#!/usr/bin/env python3
"""
Fill in clause explanations in an LLM-optimized markdown file.

This script:
1. Reads a markdown file with [BEGIN EXPLANATION]...[END EXPLANATION] blocks
2. For each block, extracts the clause number and title
3. Extracts the clause text that follows the explanation block
4. Generates a YAML-formatted analysis using an LLM
5. Writes the filled-in markdown back to the file

The explanations are designed to help a contracts lawyer compile a checklist
to compare a separate SaaS agreement against the precedent.

Usage:
    python fill_clause_explanations.py <input.md> [output.md]
    python fill_clause_explanations.py <input.md> --interactive
    python fill_clause_explanations.py <input.md> --clause 6
    
Example:
    python fill_clause_explanations.py "analysis/saas-llm.md" "analysis/saas-analyzed.md"
    python fill_clause_explanations.py "analysis/saas-llm.md" --interactive --clause 6

Modes:
    --interactive   Process clauses one at a time, printing prompts for VS Code Copilot
    --generate-prompts  Generate individual prompt files for batch processing
    --clause N      Only process clause number N (can combine with --interactive)
"""

import re
import sys
import json
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Check for OpenAI API (optional)
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@dataclass
class ClauseBlock:
    """Represents a clause with its explanation block."""
    clause_number: str
    clause_title: str
    clause_text: str
    start_pos: int  # Position of [BEGIN EXPLANATION
    end_pos: int    # Position after [END EXPLANATION]
    original_content: str  # The original [BEGIN]...[END] block


EXPLANATION_TEMPLATE = """---
clause_number: {clause_number}
clause_title: "{clause_title}"

clause_effect: "{clause_effect}"
clause_effect_of_deletion: "{effect_of_deletion}"
clause_balance: "{balance}"
clause_supplier_negotiation_option: "{supplier_option}"
clause_customer_negotiation_option: "{customer_option}"

---"""


SYSTEM_PROMPT = """You are a senior commercial contracts lawyer with expertise in SaaS agreements.
Your task is to analyze contract clauses and provide structured analysis to help another lawyer 
compare a different SaaS agreement against this precedent.

Always respond with ONLY the YAML block, no additional text before or after.
Keep each field to 1-2 concise sentences.
Use plain English suitable for a busy lawyer."""


def find_explanation_blocks(content: str) -> list[ClauseBlock]:
    """Find all [BEGIN EXPLANATION]...[END EXPLANATION] blocks in the content."""
    blocks = []
    
    # Pattern to match [BEGIN EXPLANATION: X - Title]...[END EXPLANATION]
    pattern = r'\[BEGIN EXPLANATION:\s*([^\]]+)\]\s*(.*?)\s*\[END EXPLANATION\]'
    
    for match in re.finditer(pattern, content, re.DOTALL):
        full_match = match.group(0)
        header_info = match.group(1).strip()
        existing_content = match.group(2).strip()
        
        # Parse "6 - Third party providers" format
        if ' - ' in header_info:
            parts = header_info.split(' - ', 1)
            clause_number = parts[0].strip()
            clause_title = parts[1].strip()
        else:
            clause_number = header_info
            clause_title = ""
        
        # Extract clause text that follows this block
        clause_text = extract_clause_text(content, match.end())
        
        blocks.append(ClauseBlock(
            clause_number=clause_number,
            clause_title=clause_title,
            clause_text=clause_text,
            start_pos=match.start(),
            end_pos=match.end(),
            original_content=full_match
        ))
    
    return blocks


def extract_clause_text(content: str, start_pos: int) -> str:
    """Extract the clause text that follows an explanation block.
    
    Stops at the next ## heading or [BEGIN EXPLANATION block.
    """
    # Find the end of this clause section
    remaining = content[start_pos:]
    
    # Look for next main clause heading (## X.) or next [BEGIN EXPLANATION
    next_heading = re.search(r'\n## \d+\.', remaining)
    next_annex = re.search(r'\n## (Schedule|Annex|Appendix)', remaining, re.IGNORECASE)
    next_begin = re.search(r'\[BEGIN EXPLANATION:', remaining)
    
    end_positions = []
    if next_heading:
        end_positions.append(next_heading.start())
    if next_annex:
        end_positions.append(next_annex.start())
    if next_begin:
        end_positions.append(next_begin.start())
    
    if end_positions:
        end_pos = min(end_positions)
        clause_text = remaining[:end_pos].strip()
    else:
        clause_text = remaining.strip()
    
#    # Limit to reasonable length for API calls
#    if len(clause_text) > 8000:
#        clause_text = clause_text[:8000] + "..."
    
    return clause_text


def generate_user_prompt(clause: ClauseBlock) -> str:
    """Generate the user prompt for the LLM to analyze a clause."""
    return f"""Analyze this SaaS agreement clause:

CLAUSE NUMBER: {clause.clause_number}
CLAUSE TITLE: {clause.clause_title}

CLAUSE TEXT:
{clause.clause_text}

Respond with ONLY this YAML format:

---
clause_number: {clause.clause_number}
clause_title: "{clause.clause_title}"

clause_effect: "[What this clause does - its legal effect, e.g. Supplier disclaims liability for third-party services and content.]"
clause_effect_of_deletion: "[What happens if deleted from the agreement, e.g. If deleted, Customer could argue that the third party services form part of the Supplier's Services and therefore Supplier is liable for service availability, IP issues, compliance issues of those third party services]"
clause_balance: "[pro-supplier/pro-customer/balanced]"
clause_supplier_negotiation_option: "[How Supplier could improve their position, e.g. Improve the Supplier's position by adding an indemnity so Customer holds the Supplier harmless, defends and indemnifies the Supplier against any losses in relation to the third party services]"
clause_customer_negotiation_option: "[How Customer could improve their position, e.g. Improve the Customer's position by making the Supplier liable for any third party services which are an integral part of the Supplier's Services or where the Customer is not able to opt out of using the third party services]"

---"""


def generate_copilot_prompt(clause: ClauseBlock) -> str:
    """Generate a prompt formatted for VS Code Copilot Chat."""
    return f"""@workspace I need you to analyze this SaaS agreement clause for a contracts lawyer checklist.

**Clause {clause.clause_number}: {clause.clause_title}**

```
{clause.clause_text}
```

Please provide analysis in this YAML format:
- clause_effect: What this clause does - its legal effect, e.g. Supplier disclaims liability for third-party services and content.
- clause_effect_of_deletion: What happens if the clause is deleted from the agreement, e.g. If deleted, Customer could argue that the third party services form part of the Supplier's Services and therefore Supplier is liable for service availability, IP issues, compliance issues of those third party services
- clause_balance: pro-supplier/pro-customer/balanced
- clause_supplier_negotiation_option: How Supplier could improve their position, e.g. Improve the Supplier's position by adding an indemnity so Customer holds the Supplier harmless, defends and indemnifies the Supplier against any losses in relation to the third party services
- clause_customer_negotiation_option: How Customer could improve their position, e.g. Improve the Customer's position by making the Supplier liable for any third party services which are an integral part of the Supplier's Services or where the Customer is not able to opt out of using the third party services

Keep each field to 1-2 sentences. Respond with ONLY the YAML block."""


def call_openai_api(clause: ClauseBlock, model: str = "gpt-4o") -> Optional[str]:
    """Call OpenAI API to generate explanation."""
    if not HAS_OPENAI:
        return None
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    
    client = openai.OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": generate_user_prompt(clause)}
            ],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"  OpenAI API error: {e}")
        return None


def extract_yaml_from_response(response: str) -> str:
    """Extract the YAML block from an LLM response."""
    if not response:
        return ""
    
    # Look for content between --- markers
    yaml_match = re.search(r'---\s*\n(.*?)\n\s*---', response, re.DOTALL)
    if yaml_match:
        return f"---\n{yaml_match.group(1).strip()}\n\n---"
    
    # Try to find YAML content without markers
    if 'clause_number:' in response and 'clause_effect:' in response:
        lines = []
        in_yaml = False
        for line in response.split('\n'):
            stripped = line.strip()
            if 'clause_number:' in line:
                in_yaml = True
            if in_yaml:
                # Stop at blank line after clause_customer_negotiation_option
                if 'clause_customer_negotiation_option:' in line:
                    lines.append(line)
                    break
                lines.append(line)
        if lines:
            return "---\n" + '\n'.join(lines) + "\n\n---"
    
    return response


def generate_placeholder(clause: ClauseBlock) -> str:
    """Generate a placeholder template for manual completion."""
    return EXPLANATION_TEMPLATE.format(
        clause_number=clause.clause_number,
        clause_title=clause.clause_title,
        clause_effect="[TO BE FILLED: Describe the legal effect of this clause]",
        effect_of_deletion="[TO BE FILLED: What happens if this clause is deleted]",
        balance="[TO BE FILLED: pro-supplier/pro-customer/balanced/neutral]",
        supplier_option="[TO BE FILLED: How Supplier could improve their position]",
        customer_option="[TO BE FILLED: How Customer could improve their position]"
    )


def process_clause_interactive(clause: ClauseBlock) -> str:
    """Process a single clause interactively, prompting for input."""
    print("\n" + "="*80)
    print(f"CLAUSE {clause.clause_number}: {clause.clause_title}")
    print("="*80)
    print("\nCopy the following prompt into VS Code Copilot Chat:\n")
    print("-" * 40)
    print(generate_copilot_prompt(clause))
    print("-" * 40)
    print("\nThen paste the YAML response below (end with a blank line):\n")
    
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "" and lines:
                # Check if we have enough content
                content = '\n'.join(lines)
                if '---' in content or 'clause_effect' in content:
                    break
            lines.append(line)
        except EOFError:
            break
    
    response = '\n'.join(lines)
    return extract_yaml_from_response(response) or generate_placeholder(clause)


def process_clause_api(clause: ClauseBlock, verbose: bool = True) -> str:
    """Process a single clause using available API."""
    if verbose:
        print(f"  Calling API for clause {clause.clause_number}...")
    
    # Try OpenAI first
    response = call_openai_api(clause)
    if response:
        yaml_content = extract_yaml_from_response(response)
        if yaml_content and 'clause_effect:' in yaml_content:
            return yaml_content
    
    # Fall back to placeholder
    if verbose:
        print(f"  No API available, generating placeholder")
    return generate_placeholder(clause)


def fill_explanations(content: str, mode: str = "api", 
                      target_clause: Optional[str] = None,
                      verbose: bool = True) -> str:
    """Fill in all explanation blocks in the content.
    
    Args:
        content: The markdown content
        mode: "api", "interactive", or "placeholder"
        target_clause: If set, only process this clause number
        verbose: Print progress messages
    """
    blocks = find_explanation_blocks(content)
    
    if target_clause:
        blocks = [b for b in blocks if b.clause_number == target_clause]
    
    if verbose:
        print(f"Found {len(blocks)} explanation blocks to fill")
    
    # Process blocks in reverse order to maintain position accuracy
    blocks_reversed = sorted(blocks, key=lambda b: b.start_pos, reverse=True)
    
    for block in blocks_reversed:
        if verbose:
            print(f"Processing clause {block.clause_number}: {block.clause_title}")
        
        if mode == "interactive":
            explanation = process_clause_interactive(block)
        elif mode == "api":
            explanation = process_clause_api(block, verbose)
        else:
            explanation = generate_placeholder(block)
        
        # Build the new block
        new_block = f"[BEGIN EXPLANATION: {block.clause_number} - {block.clause_title}]\n{explanation}\n[END EXPLANATION]"
        
        # Replace in content
        content = content[:block.start_pos] + new_block + content[block.end_pos:]
    
    return content


def process_file(input_path: Path, output_path: Optional[Path] = None,
                 mode: str = "api", target_clause: Optional[str] = None) -> None:
    """Process a markdown file and fill in explanations."""
    print(f"Reading: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if there are blocks to fill
    blocks = find_explanation_blocks(content)
    if not blocks:
        print("No [BEGIN EXPLANATION]...[END EXPLANATION] blocks found.")
        return
    
    if target_clause:
        matching = [b for b in blocks if b.clause_number == target_clause]
        if not matching:
            print(f"No clause found with number: {target_clause}")
            print(f"Available clauses: {', '.join(b.clause_number for b in blocks)}")
            return
        print(f"Processing clause {target_clause} only")
    else:
        print(f"Found {len(blocks)} clauses to analyze")
    
    # Fill explanations
    filled_content = fill_explanations(content, mode=mode, target_clause=target_clause)
    
    # Write output
    if output_path is None:
        output_path = input_path
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(filled_content)
    
    print(f"Output written to: {output_path}")


def generate_batch_prompts(input_path: Path, output_dir: Optional[Path] = None) -> None:
    """Generate individual prompt files for each clause.
    
    This allows batch processing through an external LLM API or manual review.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = find_explanation_blocks(content)
    
    if output_dir is None:
        output_dir = input_path.parent / "clause_prompts"
    
    output_dir.mkdir(exist_ok=True)
    
    # Also generate a combined prompts file for easy copying
    combined_prompts = []
    
    for block in blocks:
        prompt = generate_copilot_prompt(block)
        prompt_file = output_dir / f"clause_{block.clause_number.replace('.', '_').replace(' ', '_')}.txt"
        
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        combined_prompts.append(f"### Clause {block.clause_number}: {block.clause_title}\n\n{prompt}\n")
        print(f"Generated prompt: {prompt_file}")
    
    # Write combined file
    combined_file = output_dir / "_all_prompts.md"
    with open(combined_file, 'w', encoding='utf-8') as f:
        f.write("# Clause Analysis Prompts\n\n")
        f.write("Copy each prompt section into VS Code Copilot Chat.\n\n")
        f.write("---\n\n")
        f.write("\n---\n\n".join(combined_prompts))
    
    print(f"\nGenerated {len(blocks)} prompt files in {output_dir}")
    print(f"Combined prompts file: {combined_file}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fill in clause explanations in an LLM-optimized markdown file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all clauses
  python fill_clause_explanations.py analysis/saas.md --list-clauses
  
  # Generate prompts for Copilot Chat
  python fill_clause_explanations.py analysis/saas.md --generate-prompts
  
  # Process a single clause interactively
  python fill_clause_explanations.py analysis/saas.md --interactive --clause 6
  
  # Process all with OpenAI API (requires OPENAI_API_KEY env var)
  python fill_clause_explanations.py analysis/saas.md output.md
"""
    )
    parser.add_argument("input", help="Input markdown file with explanation blocks")
    parser.add_argument("output", nargs="?", help="Output file (default: overwrite input)")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Interactive mode: prompts for each clause")
    parser.add_argument("--generate-prompts", "-g", action="store_true",
                        help="Generate individual prompt files for batch processing")
    parser.add_argument("--list-clauses", "-l", action="store_true",
                        help="List all clauses found without processing")
    parser.add_argument("--clause", "-c", type=str,
                        help="Only process this specific clause number")
    parser.add_argument("--placeholder", "-p", action="store_true",
                        help="Generate placeholder templates only (no API calls)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)
    
    if args.list_clauses:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        blocks = find_explanation_blocks(content)
        print(f"Found {len(blocks)} clauses:\n")
        for block in blocks:
            text_preview = block.clause_text[:100].replace('\n', ' ')
            print(f"  {block.clause_number}. {block.clause_title}")
            print(f"      Text: {text_preview}...")
            print()
        return
    
    if args.generate_prompts:
        generate_batch_prompts(input_path)
        return
    
    # Determine mode
    if args.interactive:
        mode = "interactive"
    elif args.placeholder:
        mode = "placeholder"
    else:
        mode = "api"
    
    output_path = Path(args.output) if args.output else None
    process_file(input_path, output_path, mode=mode, target_clause=args.clause)


if __name__ == "__main__":
    main()
