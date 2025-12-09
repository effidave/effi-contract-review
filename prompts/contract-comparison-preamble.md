# Contract Comparison Preamble

Use this file to establish context for comparing a client's terms against a trusted precedent.

---

## Instructions

Copy each section below into the chat in sequence, waiting for confirmation before proceeding to the next. Alternatively, use the "Combined Version" section for a single-prompt setup.

---

## Stage 1: Firm Context

```
I'm setting up context for a contract comparison task.

We are commercial lawyers advising technology companies on SaaS agreements.
Our clients are typically B2B SaaS vendors, UK-based or selling into UK/EU markets.
Jurisdiction: Primarily English law.

The task: Compare a client's existing SaaS terms against our trusted precedent to identify strengths and weaknesses.

Please confirm you understand this context.  Don't get started until I tell you.
```

---

## Stage 2: Comparison Framework

```
Our approach to this comparison:

Perspective: We're advising the client (who is the Supplier/SaaS vendor)
Objective: Identify where client's terms are weaker than our precedent and recommend improvements

Priority areas:
1. Liability exposure (caps, exclusions, carve-outs)
2. IP ownership and licensing scope  
3. Data protection compliance (UK GDPR, processor obligations)
4. Indemnity structure (scope, direction, caps)
5. Termination rights and exit provisions
6. Payment terms and fee increase mechanisms
7. Service specification and scope protection

For each issue, we want:
- What the precedent says
- What the client terms say
- Whether client is stronger, weaker or equivalent
- Recommended amendment if weaker

Also identify:
- Clauses in precedent that are MISSING from client terms entirely
- For each missing clause: what risk does this create for the client?
- Whether absence is a problem (some clauses are optional) or a critical gap

And identify:
- Clauses in client terms that are NOT in the precedent
- For each: is this a good addition, problematic, or neutral?
- Flag any unusual or non-standard provisions that may create risk

Confirm understood.
```

---

## Stage 3: Output Format

```
For the comparison output, use this structure:

## Executive Summary
- Overall assessment: Is client's document stronger/weaker/equivalent to precedent?
- Top 3-5 priority issues to address
- Key structural gaps (clauses missing entirely)

## Clause-by-Clause Comparison

For each material difference:

| Clause | Precedent Position | Client Position | Assessment | Recommendation |
|--------|-------------------|-----------------|------------|----------------|
| [topic] | [summary] | [summary] | Weaker/Stronger/Equivalent | [specific suggestion] |

## Structural Gaps (Missing Clauses)

For clauses in precedent that are missing entirely from client terms:

| Missing From Client | Precedent Reference | Risk Level | Why It Matters |
|---------------------|---------------------|------------|----------------|
| [clause/topic] | Clause X | High/Medium/Low | [consequence of omission] |

## Client Additions (Not in Precedent)

For clauses in client terms that are not in the precedent:

| Client Clause | Topic | Assessment | Comment |
|---------------|-------|------------|----------|
| Clause X | [topic] | Good/Problematic/Neutral | [why this helps, harms or is fine] |

## Detailed Recommendations

For high-priority issues, provide:
- Specific amendment wording where helpful
- Risk if not addressed
- Negotiability assessment (standard market practice vs. aggressive ask)

Tone: Direct, practical, lawyer-to-lawyer.
Grammar: British English (no Oxford comma, use "organise" not "organize").

Confirm you understand the format.
```

---

## Stage 4: Calibration Check

```
Quick calibration before we proceed:

For a pro-supplier B2B SaaS agreement under English law:
1. What's a typical liability cap structure?
2. Is a one-way customer indemnity (customer indemnifies supplier) market standard?
3. How would you expect IP in improvements/customisations to be handled?
4. What's a reasonable data return period on termination?

Brief answers — I want to confirm your market knowledge aligns with current practice.
```

---

## Stage 5: Document Attachment and Orientation

```
Now I'm attaching two documents:

#file:[precedent-file.md]  
#file:[client-file.md]

Before full analysis, please confirm:

1. Document identification:
   - Precedent: [which file]
   - Client terms: [which file]

2. Document types: What kind of agreement is each?

3. Overall impression: 
   - Is client's document pro-supplier, pro-customer or balanced?
   - How does it compare structurally to precedent (similar clauses, missing sections)?

4. Initial concerns: Any obvious gaps or issues that stand out?

Please provide this orientation summary, then I'll request the full comparison.
```

### Stage 5 Alternative: Neutral Orientation (for high-stakes comparisons)

Use this version to avoid anchoring bias — it validates document loading without triggering premature judgment:

```
Now I'm attaching two documents:

#file:[precedent-file.md]  
#file:[client-file.md]

Before full analysis, please confirm:

1. Document identification:
   - Which file is the precedent?
   - Which file is the client terms?

2. Document structure:
   - How many main clauses in each?
   - Any schedules/annexes?

3. Ready to proceed?

Do NOT provide any assessment of balance, strengths or weaknesses yet. 
Just confirm you can identify both documents and are ready for the full comparison.
```

---

## Stage 6: Full Comparison Request

```
Thank you. Now please provide the full comparison analysis:

1. Executive Summary
2. Clause-by-Clause Comparison table
3. Detailed Recommendations for priority issues

Focus on actionable advice. Where client is weaker, provide specific amendment suggestions.
```

---

## Combined Version (Single Prompt)

If you want a condensed version for faster setup:

```
I need you to compare a client's SaaS terms against our precedent.

CONTEXT:
- We're commercial lawyers advising the client (a B2B SaaS vendor)
- Jurisdiction: English law
- Objective: Identify where client's terms are weaker than precedent

PRECEDENT: [first attached file] - Our trusted pro-supplier template
CLIENT TERMS: [second attached file] - Client's current document

PRIORITIES:
1. Liability caps and exclusions
2. IP ownership (especially improvements/customisations)
3. Data protection compliance
4. Indemnity structure
5. Termination and exit
6. Payment and fee increases
7. Service specification clarity

OUTPUT FORMAT:
1. Executive Summary (overall assessment, top 5 issues, structural gaps)
2. Comparison Table: | Clause | Precedent | Client | Assessment | Recommendation |
3. Structural Gaps Table: | Missing From Client | Precedent Ref | Risk Level | Why It Matters |
4. Client Additions Table: | Client Clause | Topic | Assessment (Good/Problematic/Neutral) | Comment |
5. Detailed Recommendations with specific amendment wording for high-priority issues

IMPORTANT: 
- Identify clauses that are in the precedent but MISSING from client terms (gaps can be dangerous)
- Identify clauses in client terms that are NOT in the precedent (may be good, problematic or neutral)

TONE: Direct, practical, lawyer-to-lawyer. British English.

Before full analysis, briefly confirm:
- Which document is which
- Overall balance of each
- Any obvious structural gaps

Then provide the full comparison.

[ATTACH BOTH DOCUMENTS]
```

---

## Usage Notes

| Stage | Purpose | Skip If... |
|-------|---------|------------|
| 1 | Establish firm identity | You've used this before with same model instance |
| 2 | Set comparison framework | Already covered in combined preamble |
| 3 | Define output structure | You're flexible on format |
| 4 | Validate market knowledge | You trust the model's calibration |
| 5 | Orient on specific documents | Documents are clearly labelled |
| 6 | Trigger full analysis | — |

For routine comparisons, the **combined version** with the brief orientation checkpoint is efficient. Use the **full staged version** when working with a new model, complex documents or high-stakes advice.

---

## Workflow Summary

```
SESSION 1 (Technical - optional):
├── Convert precedent.docx → precedent.md
├── Convert client-terms.docx → client-terms.md
└── Verify outputs look correct

SESSION 2 (Legal Analysis):
├── Load this preamble (staged or combined)
├── Attach precedent.md + client-terms.md
├── Brief orientation checkpoint
└── Receive full comparison with recommendations
```

---

## Version History

- 2025-12-04: Added bidirectional gap analysis (client additions not in precedent)
- 2025-12-04: Added explicit structural gaps/missing clause analysis
- 2025-12-04: Initial version for precedent-vs-client comparison workflow
