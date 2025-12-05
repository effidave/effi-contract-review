# Contract Issue Analysis Preamble (Two-Pass)

Use this file for analysing a client's terms by legal issue, then comparing against a precedent.

This approach:
1. **Pass 0 (Optional)**: Open discovery — what are the key issues? (no framework, reduces anchoring bias)
2. **Pass 1**: Analyses client terms against 20-issue taxonomy using domain knowledge (no precedent)
3. **Pass 2**: Compares to precedent on priority issues identified, with specific recommendations

---

## Instructions

Run all stages in the **same chat session** to maintain context and consistency.

---

## Stage 1: Firm Context

```
I'm setting up context for a contract review task.

We are commercial lawyers advising technology companies on SaaS agreements.
Our clients are typically B2B SaaS vendors, UK-based or selling into UK/EU markets.
Jurisdiction: Primarily English law.

The task: Advise a client whether their existing SaaS terms are fit for purpose.

Please confirm you understand this context.
```

---

## Stage 2: Calibration Check

```
Quick calibration before we proceed:

For a pro-supplier B2B SaaS agreement under English law:

1. What's a typical liability cap structure?
2. Is excluding indirect/consequential loss enforceable under UCTA?
3. What processor obligations are required under UK GDPR Article 28?
4. What's market standard for data return on termination?
5. When would you expect to see a mutual indemnity vs one-way?

Brief answers — I want to confirm your market knowledge aligns with current practice.
```

---

## Stage 3: Pass 0 — Open Discovery (Optional)

```

#file:[client-terms.md]

Using your legal judgment, please identify:

1. **Key issues**: How does this contract handle the most important legal issues for a B2B SaaS agreement?
2. **Red flags**: What concerns you most from a supplier's perspective?
3. **Missing elements**: Is there anything significant missing?
4. **Overall impression**: Is this a well-drafted contract? First reaction?

Be specific — cite clause numbers where relevant.

Write the output to a new md file in C:\Users\DavidSant\effi-contract-review\EL_Projects\Lamplight\drafts\current_drafts\Sample Completed Hosting Agreement 2025

```
---


## Stage 4: Issue Taxonomy

```
As this is a B2B SaaS supplier agreement, I am going to ask you to advise on these legal issues from the supplier's perspective:

CORE COMMERCIAL:
1. Service specification and scope - Is the service clearly defined? Protection against scope creep?
2. Pricing and payment - Fee structure, payment terms, right to increase prices?
3. Term and renewal - Initial term, auto-renewal, notice periods, lock-in risk?

RISK ALLOCATION:
4. Liability exposure - Cap structure, exclusions, carve-outs, aggregate vs per-claim?
5. Indemnities - Scope, direction (mutual vs one-way), caps, procedure?
6. Warranties - What's warranted, what's disclaimed, remedies for breach?
7. Insurance - Any requirements, adequacy for risk profile?

INTELLECTUAL PROPERTY:
8. IP ownership - Who owns what? Improvements, customisations, derivative works?
9. Licence scope - Grant, restrictions, sublicensing, territorial scope?
10. Customer data - Ownership, permitted use, return/deletion on termination?

DATA AND SECURITY:
11. Data protection - GDPR compliance, processor obligations, sub-processors, transfers?
12. Security obligations - Technical measures, certifications, breach notification?
13. Confidentiality - Scope, duration, permitted disclosures, mutual vs one-way?

OPERATIONAL:
14. Service levels - Uptime commitments, remedies, service credits?
15. Support and maintenance - Scope, response times, exclusions?
16. Change management - Can supplier change the service? Notice, materiality threshold?

EXIT AND DISPUTES:
17. Termination rights - Grounds, notice periods, immediate termination triggers?
18. Exit provisions - Data return, transition assistance, survival of obligations?
19. Dispute resolution - Governing law, jurisdiction, escalation, ADR?

STRUCTURAL:
20. Boilerplate adequacy - Assignment, variation, waiver, entire agreement, third party rights?

For each issue, I will need you to assess:
- Is this issue addressed in the contract?
- How well is it addressed (strong/adequate/weak/missing)?
- Which clause(s) are relevant?
- Any specific concerns or gaps?

Confirm you understand this issue framework.
```

---

## Stage 5: Output Format for Pass 1

```

For the  output, use this structure:



For the issue analysis, once I have provided the contract, you will need to use this output format:

## Executive Summary
- Overall thoughts: 
-- general assessment of whether the agreement is fit for purpose, referring to strengths as well as weaknesses (at a high level)
-- an overview of material risks/issues which need to be addressed (e.g. risks which are high impact and possible, or medium impact with a realistic possibility of occuring)
-- a list of practical and commercial solutions/mitigations to address any high priority or medium priority material risks/issues [e.g. whether to strengthen the supplier's right to exit the agreement, whether to require payment in advance, whether to allocate the risk via warranties and indemnities]
-- a view on the most cost-effective way of carrying out the legal work to achieve those benefits [e.g. whether to start from a different template agreement, or whether to edit clauses on a case-by-case basis, whether to edit clauses via an overriding addendum/schedule]

## Issue-by-Issue Analysis

For each of the issues:

| Issue | Underlying rationale for addressing this in a B2B SaaS contract | Relevant clauses | Summary of actual contract position | Assessment of whether contract position adequately addresses the issue from the supplier's perspective | Recommendation |
|--------|-------------------|-----------------|------------|----------------|
| [Issue Name] | [summary of rationale] | [list of relevant clauses] | [summary of actual position, including clause references] | assessment of adequacy | [specific suggestion] |

## Issues Not Addressed
List any issues from the taxonomy that are completely missing from the contract.

## Cross-Cutting Concerns
Note any issues that arise from the interaction of multiple clauses.

Tone: Direct, practical, lawyer-to-lawyer.
Grammar: British English (no Oxford comma, spellings should be British English, e.g. "organise").

Confirm you understand this format.
```

---

## Stage 6: Pass 1 — Taxonomy Analysis (Client Terms Only)

```
[If you skipped Pass 0, attach the file here: #file:[client-terms.md]]

Here is the contract.  

Please now go ahead and use your legal domain knowledge to arry out the Pass 1 Issue Analysis and provide the output to a new md file in C:\Users\DavidSant\effi-contract-review\EL_Projects\Lamplight\drafts\current_drafts\Sample Completed Hosting Agreement 2025

The output will be reviewed by a senior partner at the firm, who values accuracy, thoroughness and practical and commercial solutions.

It is important to you to meet the partner's expectations.

Output using the format we established.

This is Pass 1 only. I will provide a precedent for comparison in Pass 2.
```

---

## Stage 7: Pass 1 Review (Optional)

```
Before we proceed to Pass 2, I want to check a few things:

1. [Any corrections or clarifications about the document]
2. [Any context about the client's specific situation]
3. [Any issues you want to prioritise or de-prioritise]

Please adjust your analysis if needed, then confirm you're ready for Pass 2.
```

---

## Stage 8: Pass 2 — Precedent Comparison

```
Now I'm attaching our trusted precedent for comparison.

#file:[precedent.md]

Please provide the Pass 2 Precedent Comparison:

For the comparison output, use this structure:

## Executive Summary
- Overall assessment: Is client's document stronger/weaker/equivalent to precedent?
- Top priority issues to address
- Key structural gaps (clauses missing entirely)

## Clause-by-Clause Comparison

For each material difference:

| Issue | Precedent Position | Client Position | Assessment | Recommendation | Priority |
|--------|-------------------|-----------------|------------|----------------|----------|
| [Issue Name] | [summary of how the issue is dealt with in the precedent (including clause references)] | [summary of differences in how the issue is dealt with in the client's agreement (including clause references)] | Which is more appropriate and why? | [specific practical and achievable suggestion, which could be that no change is needed, or a non-contractual solution (provide details), or a contract-drafting solution (provide details of drafting proposals, affected clauses and any precedent clauses which you propose to base this on)] | [high / medium / nice-to-have]

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


Tone: Direct, practical, lawyer-to-lawyer.
Grammar: British English (no Oxford comma, use "organise" not "organize").

Confirm you understand the format.

```
---


## Stage 9: Consolidated Report (Optional)

```

```

---

## Combined Version (Fewer Prompts)

For efficiency, you can combine stages. Choose 2-pass or 3-pass:
Please combine all passes into a single client-ready report:

## Structure

1. Executive Summary
   - Overall assessment
   - Top recommendations (prioritised)

2. Issue-by-Issue Analysis
   - For each issue: current state, precedent comparison, recommendation, relevant clause references
   - Grouped by category (Commercial, Risk, IP, Data, Operational, Exit, Structural, Other)

3. Recommended Amendments
   - Priority order
   - Specific drafting suggestions
   - Risk if not addressed


Tone: Suitable for sharing with the client (professional but accessible).
Grammar: British English (no Oxford comma, use "organise" not "organize").

### Option A: 3-Pass (with Open Discovery)

```
PROMPT 0 (Open Discovery — Optional):

I need you to review a client's SaaS terms. 

CONTEXT:
- We're commercial lawyers advising the client (a B2B SaaS vendor)
- Jurisdiction: English law
- Perspective: Supplier-side

Using your legal judgment, identify:
1. The most important legal issues in this contract
2. Anything unusual, creative, or unexpected
3. Red flags from a supplier's perspective
4. What's missing that you'd expect to see
5. Overall impression: well-drafted or not?

Cite clause numbers. Do NOT apply a structured framework yet.

#file:[client-terms.md]
```

### Option B: 2-Pass (Skip Discovery)

```
PROMPT 1 (Setup + Pass 1):

I need you to analyse a client's SaaS terms for fitness for purpose.

CONTEXT:
- We're commercial lawyers advising the client (a B2B SaaS vendor)
- Jurisdiction: English law
- This is Pass 1: Analyse by legal issue using domain knowledge only

ISSUE TAXONOMY (assess each):
1. Service specification  2. Pricing/payment  3. Term/renewal
4. Liability exposure  5. Indemnities  6. Warranties  7. Insurance
8. IP ownership  9. Licence scope  10. Customer data
11. Data protection  12. Security  13. Confidentiality
14. Service levels  15. Support  16. Change management
17. Termination  18. Exit provisions  19. Dispute resolution
20. Boilerplate

FOR EACH ISSUE:
- Addressed? (Yes/Partial/No)
- Quality? (Strong/Adequate/Weak/Missing)
- Relevant clauses?
- Concerns and recommendations?

OUTPUT:
- Executive Summary (overall fitness, priority issues)
- Issue-by-Issue table
- Cross-cutting concerns

Do NOT compare to any precedent yet. Use your legal domain knowledge only.

#file:[client-terms.md]
```

```
PROMPT 2 (Pass 1 after Discovery — if you ran Prompt 0):

Now apply the structured 20-issue taxonomy to the same contract.

ISSUE TAXONOMY (assess each):
1. Service specification  2. Pricing/payment  3. Term/renewal
4. Liability exposure  5. Indemnities  6. Warranties  7. Insurance
8. IP ownership  9. Licence scope  10. Customer data
11. Data protection  12. Security  13. Confidentiality
14. Service levels  15. Support  16. Change management
17. Termination  18. Exit provisions  19. Dispute resolution
20. Boilerplate

FOR EACH ISSUE:
- Addressed? (Yes/Partial/No)
- Quality? (Strong/Adequate/Weak/Missing)
- Relevant clauses?
- Concerns and recommendations?

Also note:
- Any issues from your open discovery that don't fit these 20 categories
- Cross-cutting concerns

The contract is already in context from Prompt 0.
```

```
PROMPT 3 (Pass 2 — Precedent Comparison):

Now compare to our precedent on each issue you identified.

#file:[precedent.md]

For each priority issue:
- How does precedent handle it?
- Is client weaker/stronger/equivalent?
- Specific drafting recommendation?

Also flag:
- Gaps: Precedent has it, client doesn't
- Additions: Client has it, precedent doesn't (good/problematic/neutral?)

Output as issue-by-issue comparison with specific amendment recommendations.
```

---

## Usage Notes

| Stage | Purpose | Skip If... |
|-------|---------|------------|
| 1 | Establish firm context | Already established in prior session |
| 2 | Set issue taxonomy | You want a different framework |
| 3 | Define Pass 1 output | You're flexible on format |
| 4 | **Pass 0: Open discovery** | Routine review, or confident taxonomy fits |
| 5 | Calibration check | You trust the model's knowledge |
| 6 | Pass 1 taxonomy analysis | — |
| 7 | Review/adjust Pass 1 | Pass 1 looks correct |
| 8 | Pass 2 precedent comparison | — |
| 9 | Consolidated report | You don't need client-ready output |

---

## Key Differences from Clause-Based Analysis

| Aspect | Clause-Based | Issue-Based (This Preamble) |
|--------|--------------|----------------------------|
| Primary structure | By clause number | By legal issue |
| Domain knowledge | Secondary to precedent | Primary input for Pass 1 |
| Cross-clause issues | May be missed | Explicitly addressed |
| Client usefulness | Technical reference | Actionable by issue |
| Precedent role | Main benchmark | Validation and drafting source |

---

## Version History

- 2025-12-04: Initial version for two-pass issue-based analysis
- 2025-12-04: Added optional Pass 0 (open discovery) to reduce taxonomy anchoring bias
