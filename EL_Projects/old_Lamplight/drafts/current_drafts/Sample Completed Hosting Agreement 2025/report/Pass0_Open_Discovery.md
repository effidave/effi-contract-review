# Pass 0: Open Discovery Analysis

**Document**: Lamplight Hosting Agreement (20 October 2025)  
**Parties**: Lamplight Database Systems Ltd (Supplier) / Roots to Sky (Customer — charity)  
**Analyst**: GitHub Copilot  
**Date**: 4 December 2025  
**Perspective**: Supplier-side (Lamplight)

---

## 1. Key Issues: How Does This Contract Handle the Important Legal Issues?

### Liability & Risk Allocation — Well Structured

**Strengths:**
- **Liability cap** (Clause 10.3): 125% of fees in preceding 12 months — sensible, market-standard structure
- **Indirect/consequential loss exclusion** (Clause 10.1): Broad exclusion covering loss of profits, contracts, goodwill, anticipated savings — each construed as separate exclusions (good drafting)
- **Carve-outs** (Clause 10.2): Death/personal injury unlimited; property damage capped at £20,000 per incident
- **Customer acknowledgment** (Clause 10.4): Customer confirms they could negotiate the cap — useful for UCTA reasonableness

**Concerns:**
- The 125% cap applies to "total fees paid... in the preceding twelve months" — but Initial Term is only 3 months, so early claims could have a very low cap (potentially ~£105 on £35/month hosting)
- No super-cap for data protection breaches (compare to market practice)

### Data Protection — Comprehensive but Heavy on Supplier

**Strengths:**
- Controller/processor roles correctly identified (Clause 8.1)
- Article 28 requirements largely addressed (Clauses 8.3–8.12)
- Sub-processor controls in place (Clause 8.12)
- 24-hour breach notification (Clause 8.8)
- Data Protocol in Appendix 4 — good practice

**Concerns:**
- **DSAR assistance at Customer's cost** (Clause 8.11.2) — good
- **DPIA/breach assistance at Customer's cost only if not Lamplight's fault** (Clause 8.8) — reasonable balance
- **No UK Addendum/IDTA reference** — the contract still references EU SCCs (Clause 8.9.1) but post-Brexit should reference UK IDTA or UK SCCs
- **EEA references throughout** — should be updated to "UK" given English law jurisdiction and UK GDPR applicability

### IP & Indemnities — Balanced

**Strengths:**
- Clear IP ownership retained by Lamplight (Clause 5.1)
- Customer data remains Customer's property (Clause 5.1)
- **IP indemnity from Lamplight** (Clause 11) — properly structured with conditions
- **Counter-indemnity from Customer** for Customer Data (Clause 12) — appropriate balance
- Both indemnities limited to "reasonable and direct costs" — good

**Concerns:**
- IP indemnity (Clause 11) is uncapped — should consider whether it falls within the 125% cap or is unlimited (Clause 11.3 says "entire liability" but doesn't specify cap)
- Clause 10.3 refers to claims "for indemnity" being subject to 125% cap — so IP indemnity is probably capped, but could be clearer

### Termination & Exit — Adequate but Missing Data Return Detail

**Strengths:**
- 30 days' notice to terminate at end of Initial Term or any time thereafter (Clause 13.1)
- Standard insolvency and material breach triggers (Clause 13.2)
- Lamplight can terminate if Customer discontinues use (Clause 13.3) — helpful for dormant accounts
- Survival of Clauses 7 and 8 (Clause 13.5)

**Concerns:**
- **No explicit data export/return provision** in main body — only in Appendix 4 Data Protocol (28-day deletion)
- Customer has no contractual right to request data export in usable format before deletion
- No transition assistance obligation

### Service Levels & Support — Weak

**Concerns:**
- **No uptime commitment or SLA** — Clause 9.1 expressly disclaims uninterrupted service
- **No service credits**
- Support described as "general administrative and limited front line support" (Clause 2.1.4) — vague
- **Appendix 2** describes training options but no response time commitments
- **Appendix 3** describes backup/DR infrastructure well (AWS Aurora, daily snapshots, 28-day retention) but no RTO/RPO commitments

### Change Management — Favours Supplier

**Strengths:**
- Clause 5.3/5.4: Lamplight can change Service Providers/Third Party Applications with 14 days' notice
- Clause 5.5: Upgrades and maintenance allowed, with reasonable endeavours to avoid 8am–8pm
- Customer exit right if unhappy with changes (Clause 5.4) — 30 days' notice

**This is appropriate** for a low-cost SaaS product — supplier needs flexibility.

---

## 2. Red Flags from Supplier's Perspective

### 🔴 **Critical: Warranty Time Limit is Supplier-Unfriendly**

Clause 9.3 requires Customer to notify non-conformance **within 3 months of commencement** — but this protects the supplier. However:

- The **exclusive remedy** clause (Clause 9.2) gives Lamplight options (fix, replace, refund) — but refund terminates the agreement
- Refund of "fees paid" is undefined — could mean all fees ever paid, not just relating to the defective element

**Recommendation**: Clarify refund is limited to fees for the affected period.

### 🔴 **Critical: No Price Increase Mechanism in Main Body**

The main terms don't give Lamplight the right to increase fees. However:

- **Appendix 1, item 11** contains a narrow price increase right for bandwidth/user overages only
- No general annual price review clause
- After Initial Term, stuck at £35/month indefinitely unless contract amended by mutual consent

**Recommendation**: Add annual price review mechanism (e.g., RPI/CPI or minimum percentage).

### 🟡 **Moderate: Customer is a Charity — UCTA Considerations**

Roots to Sky is a charity/CIC (registered number suggests CIC). While charities can be commercial parties:

- May be argued to "deal as consumer" under UCTA s.12 if not acting in course of business
- More likely to claim exclusion clauses are unreasonable

**Mitigation**: Clause 10.4's acknowledgment helps, but consider whether to add express warranty of commercial capacity.

### 🟡 **Moderate: Data Protection Liability Exposure**

- Clause 8.8: Lamplight must notify breaches within 24 hours and provide full cooperation
- Costs of assistance recoverable from Customer only if "not attributable to any failure of Lamplight"
- If Lamplight is partially at fault, unclear who bears costs
- No cap specifically referenced for data protection claims (relies on general 125% cap)

**Recommendation**: Consider super-cap for DP breaches (e.g., 3–5x annual fees) rather than relying on general cap.

### 🟡 **Moderate: Assignment is One-Way**

- Clause 14.2: Customer cannot assign without Lamplight's consent
- **No equivalent restriction on Lamplight** — Lamplight can presumably assign freely

**This is supplier-favourable** (no red flag from supplier perspective, but Customer might push back).

### 🟢 **Low: Force Majeure Doesn't Carve Out Payment**

Clause 14.1 correctly carves out payment obligations from force majeure — good.

---

## 3. Missing Elements

### ❌ **No Acceptable Use Policy**

- Customer can use "for its own internal purposes" (Clause 2.2.4) but no AUP restricting illegal/harmful use
- Customer indemnity (Clause 12) partially covers this but an express AUP would be clearer

### ❌ **No Insurance Requirements**

- No requirement for either party to hold professional indemnity, cyber liability or public liability insurance
- Given hosting of potentially sensitive data (charity client data), this is a gap

### ❌ **No Security Certifications Commitment**

- Appendix 3 references AWS certifications (ISO 27001, SOC2, Cyber Essentials Plus) but these are AWS's, not Lamplight's
- Lamplight makes no commitment to hold its own certifications
- Clause 8.7: "Lamplight can only implement industry standard security procedures" — vague

### ❌ **No Explicit Audit Rights**

- Clause 8.5.4 allows Customer to inspect Lamplight's facilities relating to data processing
- But subject to "reasonable security restrictions" — acceptable
- **However**: No reciprocal right for Lamplight to audit Customer's compliance with data protection (e.g., lawful basis for processing)

### ❌ **No Notices Clause**

- No clause specifying how notices should be given (address, method, deemed receipt)
- Clause 1.7 says "writing" includes faxes but not email — outdated
- References to "written notice" throughout but no central notices provision

### ❌ **No Anti-Bribery / Modern Slavery**

- Not essential for this contract size, but increasingly expected

---

## 4. Overall Impression

### Is This a Well-Drafted Contract?

**First reaction: Yes, this is a competent, supplier-friendly agreement suitable for a small/mid-market B2B SaaS offering.**

**Strengths:**
- Clear structure with modular appendices
- Liability cap and exclusions are well-drafted
- Data protection provisions are comprehensive (though need UK GDPR updates)
- Change control and IP provisions are sensible
- Termination rights are balanced
- Technical infrastructure appendix (Appendix 3) is impressive for a contract of this size

**Weaknesses:**
- No SLA or uptime commitment — might be fine for the price point but limits enforceability
- Data return/exit provisions could be stronger
- Price escalation mechanism missing
- Some provisions are slightly dated (EEA references, fax references, EU SCCs)
- No notices clause

**Commercial Context:**
This is a low-value contract (£35/month hosting). The terms are appropriately calibrated for the commercial reality — comprehensive data protection, limited liability, minimal service guarantees. A higher-touch enterprise agreement would need stronger SLAs and exit provisions, but for this market segment the balance is reasonable.

**Fitness for Purpose:**
From Lamplight's perspective, this agreement is **fit for purpose with minor improvements needed**:

1. Add annual price review clause
2. Update GDPR references for UK post-Brexit
3. Add notices clause
4. Consider super-cap for data protection
5. Clarify refund calculation in warranty remedy

---

## Summary Table

| Area | Assessment | Priority |
|------|------------|----------|
| Liability cap | Adequate (125% of 12-month fees) | — |
| Indirect loss exclusion | Strong | — |
| Data protection | Comprehensive but needs UK updates | Medium |
| IP/Indemnities | Well balanced | — |
| Termination | Adequate | — |
| Data exit | Weak (28-day delete, no export right) | Medium |
| Service levels | Missing | Low (price point) |
| Price increases | Missing | High |
| Boilerplate | Mostly adequate, missing notices | Low |

---

*Ready for Pass 1 structured taxonomy analysis when instructed.*
