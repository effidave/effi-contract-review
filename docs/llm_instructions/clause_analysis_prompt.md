# Clause Analysis Prompt Template

This prompt template was derived from a successful clause analysis session using Claude Opus 4.5 on a SaaS agreement. Use this to replicate consistent, high-quality clause analysis.

## Key Success Factors

1. **Provide a worked example** - Include at least one fully completed clause analysis as a reference
2. **State the purpose clearly** - "Help a busy contracts lawyer compile a checklist to compare agreements"
3. **Full contract context** - Provide the entire contract so the LLM can see cross-references and defined terms
4. **Structured output format** - YAML with specific fields ensures consistent, parseable output
5. **Clear markers** - Use `[BEGIN EXPLANATION]...[END EXPLANATION]` blocks to identify where analysis should go
6. **Document type context** - Clarify whether this is a precedent, counterparty paper, or negotiation draft
7. **Jurisdiction context** - State the governing law (e.g., English law)

---

## Recommended Multi-Stage Conversation

For best results, use this 4-stage conversation flow rather than a single prompt:

### Stage 1: Context Setting

```
I'm building a contract analysis tool for commercial lawyers. I need you to help me analyze a SaaS agreement.

Context:
- This is a pro-supplier SaaS precedent template (not counterparty paper)
- Governed by English law
- The analysis will be used by lawyers to compare client agreements against this precedent
- Output should be practical and focused on negotiation implications

IMPORTANT: This will be a multi-step process. Please wait for my instructions at each stage before proceeding.

Do you understand the context? Please confirm and wait for the next step.
```

### Stage 2: Share the Full Contract

```
Here is the full contract. Please read it carefully, paying particular attention to:
- Clause 1 (Definitions) - these defined terms are used throughout
- Cross-references between clauses (e.g., indemnities subject to liability caps)
- The overall balance of the agreement

DO NOT start analyzing individual clauses yet. Just read and confirm you've reviewed it.

[PASTE FULL CONTRACT TEXT]

Once you've reviewed it, please confirm ONLY:
1. What type of agreement is this?
2. What's the overall balance (pro-supplier/pro-customer/balanced)?
3. Any notable features or unusual provisions?

Then STOP and wait for the output format instructions.
```

### Stage 3: Provide Example and Format

```
Great. Now I'll give you the output format. DO NOT start generating yet - just confirm you understand the format.

I need you to analyze each clause using this YAML format.

Here's an example of the analysis style I want (Clause 6):

[BEGIN EXPLANATION: 6 - Third party providers]
---
clause_number: 6
clause_title: "Third party providers"

clause_effect: "Supplier disclaims liability for third-party services and content."
clause_effect_of_deletion: "If deleted, Customer could argue that the third party services form part of the Supplier's Services and therefore Supplier is liable for service availability, IP issues, compliance issues of those third party services"
clause_balance: "pro-supplier"
supplier_negotiation_option: "Improve the Supplier's position by adding an indemnity so Customer holds the Supplier harmless, defends and indemnifies the Supplier against any losses in relation to the third party services"
customer_negotiation_option: "Improve the Customer's position by making the Supplier liable for any third party services which are an integral part of the Supplier's Services or where the Customer is not able to opt out of using the third party services"

---
[END EXPLANATION]

Field requirements:
- clause_effect: 1-2 sentences on legal effect
- clause_effect_of_deletion: What happens if removed (consider both parties)
- clause_balance: pro-supplier / pro-customer / balanced / neutral
- supplier_negotiation_option: Practical negotiation suggestion
- customer_negotiation_option: Practical negotiation suggestion

Note cross-references between clauses when they materially affect the analysis.

Please confirm you understand the format by briefly describing what each field requires. Then STOP and wait for my instruction to start.
```

### Stage 4: Request Analysis

```
Perfect. Now please analyze all clauses in the contract, providing YAML blocks for each.

Process them in order (Clause 1, 2, 3... then any Schedules/Annexes).

For each clause, fill in:
[BEGIN EXPLANATION: [number] - [title]]
---
[YAML analysis]
---
[END EXPLANATION]

Start with Clauses 1-10.
```

Then continue with:
```
Continue with Clauses 11-20.
```

And:
```
Complete with remaining clauses and any Annexes/Schedules.
```

---

## Alternative: Single Prompt Approach

If you prefer a single prompt (less optimal but faster), combine the context and instructions:

### System Prompt

```
You are a senior commercial contracts lawyer with expertise in SaaS agreements and technology contracts.

Context:
- You are analyzing a pro-supplier SaaS precedent template governed by English law
- The analysis will help other lawyers compare client agreements against this precedent
- Focus on practical negotiation implications, not academic legal theory

Your task is to analyze contract clauses and produce structured YAML analysis.

Guidelines:
- Be concise but precise (1-2 sentences per field)
- Focus on practical implications for contract negotiation
- Consider both parties' perspectives objectively
- Use plain English suitable for a busy lawyer
- Reference specific clause numbers when discussing cross-references
- Note how clauses interact (e.g., indemnities subject to liability caps)
- Identify the commercial reality behind legal provisions
```

### User Prompt

```
Analyze each clause in this SaaS agreement and fill in the explanation blocks.

This is a pro-supplier English law SaaS precedent. The analysis will be used by lawyers to compare other SaaS agreements against this template.

For each [BEGIN EXPLANATION: X - Title]...[END EXPLANATION] block, provide analysis in this YAML format:

---
clause_number: [number]
clause_title: "[title]"

clause_effect: "[What this clause does - its legal effect]"
clause_effect_of_deletion: "[What happens if this clause is deleted from the agreement]"
clause_balance: "[pro-supplier/pro-customer/balanced/neutral]"
supplier_negotiation_option: "[How Supplier could negotiate to improve their position]"
customer_negotiation_option: "[How Customer could negotiate to improve their position]"

---

Important:
- Read Clause 1 (Definitions) carefully - defined terms affect interpretation throughout
- Note cross-references between clauses (e.g., Clause 12 indemnity is subject to Clause 13 cap)
- Consider how deleting a clause would shift risk between parties

EXAMPLE - Clause 6 (Third party providers):

[BEGIN EXPLANATION: 6 - Third party providers]
---
clause_number: 6
clause_title: "Third party providers"

clause_effect: "Supplier disclaims liability for third-party services and content."
clause_effect_of_deletion: "If deleted, Customer could argue that the third party services form part of the Supplier's Services and therefore Supplier is liable for service availability, IP issues, compliance issues of those third party services"
clause_balance: "pro-supplier"
supplier_negotiation_option: "Improve the Supplier's position by adding an indemnity so Customer holds the Supplier harmless, defends and indemnifies the Supplier against any losses in relation to the third party services"
customer_negotiation_option: "Improve the Customer's position by making the Supplier liable for any third party services which are an integral part of the Supplier's Services or where the Customer is not able to opt out of using the third party services"

---
[END EXPLANATION]

Now analyze all clauses in the following contract:

[FULL CONTRACT TEXT HERE]
```

---

## Field Descriptions

| Field | Description | Example |
|-------|-------------|---------|
| `clause_effect` | What the clause does legally - its operational effect | "Grants Customer a limited, non-exclusive licence to use Services during subscription term" |
| `clause_effect_of_deletion` | Consequences if the clause were removed | "If deleted, Customer would have no legal right to use Services, or could claim unlimited implied licence" |
| `clause_balance` | Which party the clause favours | `pro-supplier`, `pro-customer`, `balanced`, or `neutral` |
| `supplier_negotiation_option` | How Supplier could strengthen their position | "Add audit rights with cost recovery for underpayment" |
| `customer_negotiation_option` | How Customer could improve their position | "Negotiate right to use Services for affiliates/group companies" |

---

## Balance Classification Guide

- **pro-supplier**: Clause primarily protects or benefits the Supplier (e.g., liability caps, IP ownership, unilateral termination rights)
- **pro-customer**: Clause primarily protects or benefits the Customer (e.g., SLAs, data portability, refund rights)
- **balanced**: Clause has mutual obligations or protections that benefit both parties equally
- **neutral**: Boilerplate clause that doesn't materially favour either party (e.g., governing law, notices, severance)

---

## Usage Notes

### For Best Results:
1. Provide the **complete contract** - partial context leads to missed cross-references
2. Include **defined terms** (usually in Clause 1) - these are essential for accurate analysis
3. Run on the **structured markdown format** with clear clause numbering and explanation markers
4. Use a **capable model** (Claude Opus, GPT-4o, or equivalent) for legal reasoning

### Post-Processing:
- The YAML output can be parsed programmatically
- Consider validating `clause_balance` values against allowed options
- Review for consistency in negotiation option phrasing

---

## Integration with fill_clause_explanations.py

The `scripts/fill_clause_explanations.py` script uses a similar prompt structure. To use this template:

1. Generate the LLM-optimized markdown with explanation markers using `docx_to_llm_markdown.py`
2. Either:
   - Use `--generate-prompts` to create individual prompt files
   - Set `OPENAI_API_KEY` and run directly with OpenAI API
   - Paste the full document into a chat session with this prompt

---

## Adapting for Different Contract Types

### For Customer-Side Review (analyzing counterparty paper)

Change Stage 1 context to:
```
This is a supplier's standard terms that our client (the Customer) has received.
Analyze from the Customer's perspective - identify risks and suggest pushback positions.
```

### For Balanced/Bespoke Agreements

Change Stage 1 context to:
```
This is a negotiated agreement. Analyze objectively without assuming either party's perspective.
Focus on how terms deviate from market standard and identify potential issues for both sides.
```

### For Non-SaaS Contracts

Adapt the example clause and field descriptions to match the contract type (e.g., for a supply agreement, use delivery/warranty clauses as examples).

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Analysis too brief | Ask: "Please expand on the negotiation options with specific drafting suggestions" |
| Missing cross-references | Ask: "Review your analysis and note any interactions between clauses you may have missed" |
| Inconsistent balance ratings | Ask: "Please review the balance ratings for consistency - some clauses rated 'neutral' appear to favour one party" |
| Output not in YAML format | Provide the example again and emphasize "Respond with ONLY the YAML block" |

---

## Version History

- **2025-12-04**: Initial version derived from successful Claude Opus 4.5 session
- **2025-12-04**: Added multi-stage conversation flow, context setting, and adaptation guidance
