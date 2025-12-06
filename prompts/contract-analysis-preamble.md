# Contract Analysis Context Preamble

Use this file to establish context at the start of a new contract analysis session.

---

## Instructions

Copy each section below into the chat in sequence, waiting for confirmation before proceeding to the next. Alternatively, paste the entire "Combined Preamble" section for a single-prompt setup.

---

## Section 1: Firm Profile

```
I'm setting up context for contract analysis work. Let me tell you about our practice.

We are commercial lawyers advising technology companies on:
- SaaS and software licensing agreements
- Technology procurement and outsourcing
- Data protection and privacy compliance

Our typical clients:
- B2B SaaS vendors and technology companies
- UK-based or selling into UK/EU markets
- Deal sizes: £30k-£500k ARR typical, occasionally larger enterprise deals

Jurisdiction: Primarily English law, occasionally EU/international matters.

Please confirm you understand this context.
```

---

## Section 2: Risk Profile and Style

```
Our approach to contract drafting and negotiation:

Risk tolerance: Moderate
- We want enforceable, defensible terms
- Not seeking maximum aggression or unusual positions
- Prefer clarity over clever drafting

Negotiation philosophy:
- Commercial resolution is the norm; litigation is rare
- We advise on risk but respect client's commercial judgment
- We flag issues, recommend positions, but client decides

Drafting style:
- Plain English where possible
- Avoid archaic legalese
- Clear structure with numbered clauses

Please confirm you understand this context.
```

---

## Section 3: Priority Concerns

```
When reviewing contracts, our priority concerns are typically:

For Supplier-side deals:
1. Liability exposure (caps, exclusions, carve-outs)
2. IP ownership and licensing scope
3. Data protection compliance (UK GDPR, processor obligations)
4. Payment terms and remedies
5. Termination rights and consequences
6. Ability to increase pricing for ongoing services (e.g. subscriptions) and rate cards for ad-hoc work
7. Clarity over specification of services, protection against scope creep

For Customer-side deals:
1. Service levels and remedies
2. Data security and breach notification
3. Exit provisions and data portability
4. Supplier's financial stability / continuity
5. Liability protection for the customer
6. Supplier insurance requirements (especially if supplier is smaller or higher-risk)
7. Audit rights (to check Supplier's compliance e.g. with information security requirements, especially for regulated customers or large enterprises)

Confirm these align with your understanding of commercial priorities.
```

---

## Section 4: Output Format

```
When analysing contracts, use this YAML format for each clause:

clause_number: [number]
clause_title: "[title]"
clause_effect: "[1-2 sentences: what the clause does legally]"
clause_effect_of_deletion: "[What happens if this clause is removed]"
clause_balance: "[pro-supplier / pro-customer / balanced / neutral]"
supplier_negotiation_option: "[Practical suggestion to improve supplier's position]"
customer_negotiation_option: "[Practical suggestion to improve customer's position]"
legal_issue_tags: "[a tag for each legal issue this clause is relevant to]


Tone, grammar, spelling:
- Direct, lawyer-to-lawyer
- Practical, not academic
- Assume reader is a qualified lawyer
- Focus on "so what" and "what do we do about it"
- use British English grammar and spelling (e.g. do not use Oxford comma, use "organise" and not "organize")

Here's an example of the style we want:

---
clause_number: 6
clause_title: "Third party providers"

clause_effect: "Supplier disclaims all liability for third-party services, websites and content that may be accessed through the Services. Customer uses such third-party services at its own risk."
clause_effect_of_deletion: "If deleted, Customer could argue that third-party services form part of the Supplier's Services and therefore Supplier is liable for service availability, IP issues and compliance failures of those third-party services."
clause_balance: "pro-supplier"
supplier_negotiation_option: "Add an indemnity requiring Customer to hold Supplier harmless, defend and indemnify against any losses relating to third-party services used by Customer."
customer_negotiation_option: "Make Supplier liable for third-party services which are integral to the Supplier's Services or where Customer cannot opt out of using them; require Supplier to vet third-party providers."
legal_issue_tags: "#liability #specification #third-parties #risk #remedies"

---

Confirm you understand this format.
```

---

## Section 5: Calibration Check

```
Quick calibration check. For a typical English law B2B SaaS agreement:

1. What's a standard liability cap structure?
2. What's market norm for customer indemnity scope?
3. When would you see mutual vs. one-way confidentiality?
4. How is indirect/consequential loss typically handled?

Brief answers please - I want to confirm your market knowledge matches current practice.
```

---

## Section 6: Task Prompt Template

```
Now I'm sharing a contract for analysis.

Document type: [SaaS Terms / Software License / DPA / MSA]
Perspective: [Pro-supplier template / Pro-customer template / Counterparty paper]
We're advising: [the Supplier / the Customer]
Governing law: [English law / other]
Negotiation leverage: [strong / moderate / limited]
Special context: [e.g., "regulated customer", "first enterprise deal", "renewal negotiation"]

Please read the full document and provide clause-by-clause analysis using the format we established.

[ATTACH DOCUMENT]
```

---

## Combined Preamble (Single Prompt Version)

If you prefer to establish all context in one prompt, use this:

```
I need you to analyse a contract. First, some context about our practice:

FIRM PROFILE:
- Commercial lawyers advising technology companies
- Focus: SaaS/software licensing, tech procurement, data protection
- Typical clients: B2B SaaS vendors, 50-500 employees, UK-based
- Deal sizes: £30k-£500k ARR
- Jurisdiction: Primarily English law

APPROACH:
- Risk tolerance: Moderate - enforceable terms, not aggressive
- Style: Plain English, clear structure, practical advice
- Philosophy: Commercial resolution preferred, we advise on risk, client decides

PRIORITIES (Supplier-side):
1. Liability caps and exclusions
2. IP ownership and licensing
3. Data protection compliance
4. Payment terms
5. Termination rights

OUTPUT FORMAT:
For each clause, provide YAML with:
- clause_effect: What it does legally (1-2 sentences)
- clause_effect_of_deletion: Impact if removed
- clause_balance: pro-supplier / pro-customer / balanced / neutral
- supplier_negotiation_option: How to improve supplier position
- customer_negotiation_option: How to improve customer position
- legal_issue_tags: List of tags for the relevant legal issues


TONE: Direct, practical, lawyer-to-lawyer. Focus on "so what" and "what do we do."

EXAMPLE (Clause 6 - Third party providers):
---
clause_effect: "Supplier disclaims all liability for third-party services, websites, and content accessed through the Services."
clause_effect_of_deletion: "If deleted, Customer could argue third-party services form part of Supplier's Services, making Supplier liable for availability and compliance."
clause_balance: "pro-supplier"
supplier_negotiation_option: "Add customer indemnity for third-party service losses."
customer_negotiation_option: "Make Supplier liable for integral third-party services Customer cannot opt out of."
legal_issue_tags: "#liability #specification #third-parties #risk #remedies"
---

NOW THE TASK:
Document type: [type]
We're advising: [party]
Leverage: [level]

[ATTACH DOCUMENT]
```

---

## Usage Notes

1. **Multi-step approach**: Use Sections 1-5 when you want to validate the LLM's understanding before analysis
2. **Single prompt approach**: Use Combined Preamble when you're confident and want speed
3. **File reference**: In VS Code Copilot Chat, reference this file with `#file:prompts/contract-analysis-preamble.md`
4. **Customisation**: Edit Section 3 priorities based on the specific deal type

---

## Version History

- 2025-12-04: Initial version based on SaaS agreement analysis session
