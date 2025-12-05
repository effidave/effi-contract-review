# Pass 1: Issue-Based Analysis

**Document**: Lamplight Hosting Agreement  
**Date**: 20 October 2025  
**Parties**: Lamplight Database Systems Ltd (Supplier) / Roots to Sky (Customer — CIC/Charity)  
**Analyst**: GitHub Copilot  
**Analysis Date**: 4 December 2025  
**Perspective**: Supplier-side  
**Jurisdiction**: English law

---

## Executive Summary

### Overall Assessment

**This agreement is broadly fit for purpose for a low-value B2B SaaS offering**, with strong liability protections and comprehensive data protection provisions. However, several gaps require attention before continued use as a standard template.

**Key Strengths:**
- Well-structured liability cap (125% of 12-month fees) with comprehensive indirect loss exclusions
- Balanced IP indemnity structure (mutual, limited to "reasonable and direct costs")
- Thorough data protection clause addressing most Article 28 requirements
- Good change management flexibility — supplier can update services with reasonable notice
- Sensible acceptance testing provision shifts risk of untested deployments to customer

**Key Weaknesses:**
- No annual price review mechanism — locked at £35/month indefinitely
- No SLA or uptime commitment (though arguably appropriate for price point)
- Data protection references outdated (EEA/EU SCCs rather than UK IDTA)
- Missing notices clause
- No explicit data export right for customer on termination

### Material Risks Requiring Attention

| Risk | Impact | Likelihood | Priority |
|------|--------|------------|----------|
| **No price escalation right** — inflation erodes margin over time | Medium | High | **High** |
| **GDPR provisions reference EEA** — technically incorrect post-Brexit, could create confusion | Low | Medium | **Medium** |
| **No data export provision** — customer may dispute 28-day deletion | Medium | Low | **Medium** |
| **IP indemnity uncapped** — Clause 11.3 says "entire liability" but relationship to Clause 10.3 cap unclear | High | Low | **Medium** |
| **Customer is a charity** — may argue consumer status under UCTA | Medium | Low | **Low** |

### Practical Solutions

1. **Price escalation**: Add annual review clause permitting increases linked to RPI/CPI or a fixed percentage (e.g. 5% per annum) with 30 days' notice
2. **UK GDPR update**: Replace EEA references with UK; reference UK IDTA rather than EU SCCs
3. **Data export**: Add express provision for customer to export data in machine-readable format during 28-day post-termination window
4. **IP indemnity cap**: Clarify that IP indemnity is subject to Clause 10.3 cap, or specify a super-cap (e.g. 3x annual fees)
5. **Notices clause**: Add standard notices provision specifying addresses, methods and deemed receipt

### Cost-Effective Implementation

These are targeted amendments to an otherwise sound template. **Recommend clause-by-clause edits** rather than starting from a different template. Estimated 2–3 hours of drafting time. Changes can be implemented via:
- Direct amendment to the template for future use
- Short addendum/side letter for existing signed contracts if needed

---

## Issue-by-Issue Analysis

### CORE COMMERCIAL

| Issue | Rationale | Relevant Clauses | Contract Position | Assessment | Recommendation |
|-------|-----------|------------------|-------------------|------------|----------------|
| **1. Service specification and scope** | Clear definition prevents scope creep and disputes about what is included | Clause 2, Appendix 1 (modules), Appendix 2 (functionality) | Services defined by reference to Appendix 2 which lists functional capabilities. Modules selected in Appendix 1. Clause 2.2.4 restricts use to "own internal purposes". Clause 6 provides change control requiring customer to submit Change Requests. | **Adequate.** Service scope is reasonably defined through appendices. Change control protects against scope creep — supplier can decline or charge for changes (Clause 6.2). Customer cannot unilaterally expand scope. | Consider adding express statement that any work outside Appendix 2 is chargeable at prevailing rates. |
| **2. Pricing and payment** | Predictable revenue; protection against non-payment; ability to adjust pricing over time | Clause 3, Appendix 1 (item 11) | Fees in Appendix 1: £35/month by Direct Debit. 30-day payment terms (Clause 3.1). Late payment interest at statutory rate (Clause 3.2). Suspension right for non-payment (Clause 3.2). Appendix 1 contains narrow price increase right for bandwidth/user overages only. **No general annual price review.** | **Weak.** Payment mechanics are adequate but **no right to increase standard fees** over time. At £35/month, inflation will erode margins. Direct Debit mitigates collection risk. | **Priority fix**: Add annual price review clause (e.g. "Lamplight may increase Fees annually by giving 30 days' written notice, such increase not to exceed the greater of RPI or 5%"). |
| **3. Term and renewal** | Predictable contract duration; ability to exit problem customers; avoid perpetual lock-in | Clause 13.1, Appendix 1 (items 1–2) | Initial Term: 3 months. Auto-renewal for successive 3-month periods. Either party can terminate on 30 days' notice at end of Initial Term or any time thereafter. | **Strong.** Short initial term with rolling renewal is supplier-friendly — easy to exit problem customers. 30-day notice period is adequate for a low-value contract. No customer lock-in concerns. | No change needed. |

### RISK ALLOCATION

| Issue | Rationale | Relevant Clauses | Contract Position | Assessment | Recommendation |
|-------|-----------|------------------|-------------------|------------|----------------|
| **4. Liability exposure** | Cap financial exposure; exclude unpredictable losses; protect against catastrophic claims | Clause 10 | **Indirect loss exclusion** (Clause 10.1): Comprehensive — covers loss of profits, contracts, goodwill, anticipated savings. Each construed as separate exclusion. **Carve-outs** (Clause 10.2): Death/personal injury unlimited; property damage capped at £20,000 per incident. **General cap** (Clause 10.3): 125% of fees paid in preceding 12 months, applies to contract, tort and indemnity claims. **Customer acknowledgment** (Clause 10.4): Customer confirms could have negotiated — helps UCTA reasonableness. | **Strong.** Market-standard structure. 125% of 12-month fees is appropriate for low-value SaaS. Aggregate cap (not per-claim). Clause 10.5 excludes liability for customer's failure to backup — sensible given hosting model. | Consider whether data protection breaches should have a super-cap (e.g. 3–5x annual fees) rather than relying on general 125% cap. Currently no super-cap. |
| **5. Indemnities** | Allocate specific third-party claim risks; ensure procedural control | Clauses 11, 12 | **IP indemnity from supplier** (Clause 11): Covers claims that Lamplight's own Application infringes third-party IP. Limited to "reasonable and direct costs". Conditions: no prejudice to defence, prompt notification, supplier has conduct. Remedies: procure right, modify, or refund and terminate. Clause 11.3 says this is "entire liability" for IP claims. **Customer indemnity** (Clause 12): Covers claims arising from Customer Data infringing third-party rights. Mirror conditions. | **Adequate.** Balanced mutual structure. Both limited to "reasonable and direct" costs. IP indemnity appropriately excludes Third Party Applications (Clause 11.1 specifies "specifically created by Lamplight"). **Concern**: Clause 11.3 says "entire liability" but doesn't clearly state whether it's subject to Clause 10.3 cap. Clause 10.3 includes "indemnity" claims in cap — but potential ambiguity. | Clarify in Clause 11 that IP indemnity is subject to Clause 10.3 cap. Alternatively, specify uncapped but with super-cap for IP claims. |
| **6. Warranties** | Balance customer expectations; limit exposure for service failures; define exclusive remedies | Clause 9 | **Express warranty** (Clause 9.1): Services performed with "due care and skill". Expressly disclaims uninterrupted or error-free operation. **Exclusive remedy** (Clause 9.2): Fix, replace, or refund (supplier's option). Refund terminates agreement. **Time limit** (Clause 9.3): Notice of non-conformance within 3 months of service commencement. **Third-party disclaimer** (Clause 9.4): No warranties for hosting, Third Party Applications, internet. Customer accepts reduced recourse due to low/no licence fees. **Implied terms exclusion** (Clause 9.5): Excludes all implied warranties to fullest extent permitted. | **Strong.** Well-drafted exclusive remedy clause. 3-month notice period is supplier-friendly. Clear disclaimer for third-party components. Customer acknowledgment of trade-off (low fees = limited recourse) helps UCTA. | Clarify in Clause 9.2.3 that refund is of fees "relating to the non-conforming element" or "paid in the preceding 12 months" rather than potentially all fees ever paid. |
| **7. Insurance** | Ensure adequate cover exists; allocate risk of uninsured losses | None | **Not addressed.** No requirement for either party to maintain insurance (PI, cyber, public liability). | **Missing.** Not critical for this contract size, but leaves supplier exposed if customer is uninsured and has no assets. Also means supplier is not required to evidence cover — which may be intentional. | For higher-value deployments, consider adding mutual insurance requirements. For this price point, probably acceptable to leave out. |

### INTELLECTUAL PROPERTY

| Issue | Rationale | Relevant Clauses | Contract Position | Assessment | Recommendation |
|-------|-----------|------------------|-------------------|------------|----------------|
| **8. IP ownership** | Retain ownership of platform; clarify treatment of improvements | Clause 5.1 | Lamplight retains all IP in Application and Third Party Applications. Customer retains IP in Customer Data. Customer grants Lamplight licence to use Customer Data "only to the extent necessary" to perform obligations. | **Strong.** Clear ownership retained by supplier. No assignment of improvements to customer. Licence to Customer Data appropriately limited. | No change needed. |
| **9. Licence scope** | Define usage rights; prevent misuse; retain control | Clauses 2.1.2, 2.2.4, 5.1 | Lamplight grants (or procures) licence to use Application and Third Party Applications "as part of the Service only and to the extent envisaged by this Agreement" (Clause 2.1.2). Customer may only use for "its own internal purposes" (Clause 2.2.4). Permitted Users: Unlimited (Appendix 1). | **Adequate.** Internal use restriction is good. "Unlimited" users is unusual — normally would cap users to control load. However, Appendix 1 item 11 allows price increase for >100 users per project or excessive bandwidth. | Consider whether "Unlimited" users should be reconsidered for template. Current wording relies on bandwidth/user overage clause for protection. |
| **10. Customer data** | Confirm customer ownership; clarify permitted use; address return/deletion | Clauses 5.1, 8, Appendix 4 (Data Protocol) | Customer owns Customer Data (Clause 5.1). Lamplight's use limited to service provision. On termination: access suspended immediately; data deleted within 28 days; backups deleted after 28 days (Appendix 4, section 3). **No express export right** — customer must retrieve data before termination or within 28-day window but no obligation on Lamplight to provide export. | **Weak.** Ownership clear. However, **no express provision for data export in usable format**. Appendix 2 mentions "upload and download data" as functionality, but no contractual obligation to assist with export on termination. | Add clause requiring Lamplight to make Customer Data available for export in machine-readable format (e.g. CSV) for 28 days post-termination, after which data will be deleted. |

### DATA AND SECURITY

| Issue | Rationale | Relevant Clauses | Contract Position | Assessment | Recommendation |
|-------|-----------|------------------|-------------------|------------|----------------|
| **11. Data protection** | Comply with UK GDPR; meet Article 28 processor requirements; manage sub-processors | Clause 8, Appendix 4 | **Roles** (Clause 8.1): Customer = controller; Lamplight = processor. **Instructions** (Clauses 8.3–8.4): Process only per Data Protocol; notify if additional processing needed. **Security** (Clause 8.5.1): Appropriate technical and organisational measures; privacy by design. **Sub-processors** (Clauses 8.12–8.13): Require customer approval (except pre-approved Service Providers in Appendix 1). Flow-down obligations required. **Breach notification** (Clause 8.8): Within 24 hours. **DSAR assistance** (Clause 8.11.2): At customer's cost. **International transfers** (Clauses 8.5.3, 8.9): Customer consent required; references EU SCCs. **Audit** (Clause 8.5.4): Customer can inspect, subject to reasonable security restrictions. | **Adequate** but **needs updating**. Covers most Article 28 requirements. However: (1) References "EEA" throughout rather than "UK"; (2) References EU SCCs (Clause 8.9.1) rather than UK IDTA post-Brexit; (3) No explicit reference to UK GDPR vs EU GDPR in definitions. | Update Clause 1.1.5 and 1.1.8 to reference UK GDPR and UK data protection framework. Replace EEA references with UK where appropriate. Reference UK IDTA for international transfers. |
| **12. Security obligations** | Define technical measures; allocate responsibility; address breach response | Clauses 8.5–8.8, Appendix 3 | **Measures**: "Appropriate technical and organisational measures" (Clause 8.5.1). Regular review required (Clause 8.5.2). **Qualifications** (Clauses 8.6–8.7): Extensive qualifications — Lamplight only provides "ordinary business" measures (Clause 8.6.1); customer responsible for data integrity and user training; "industry standard" only, no penetration testing. **Breach notification**: 24 hours (Clause 8.8). **Infrastructure** (Appendix 3): AWS hosting with Aurora databases, S3 storage, multi-AZ replication, daily snapshots retained 28 days. AWS certifications (ISO 27001, SOC2, Cyber Essentials Plus). | **Adequate.** Security obligations are appropriately qualified for a SME SaaS provider. Appendix 3 provides good technical detail. **Note**: Certifications are AWS's, not Lamplight's own. No commitment to Lamplight holding certifications. | Consider whether Lamplight should commit to Cyber Essentials certification (achievable for SME). Add reference to Lamplight's own security practices, not just AWS's. |
| **13. Confidentiality** | Protect both parties' confidential information; define permitted disclosures | Clause 7 | Mutual confidentiality. Customer Data expressly included. Disclosure limited to employees/agents/sub-contractors bound by similar undertaking and with need to know. **Survives termination** (Clause 7.1). Written consent required for third-party disclosure (not to be unreasonably withheld). | **Adequate.** Mutual obligation with survival. No time limit on confidentiality — indefinite, which is appropriate for Customer Data. | No change needed. Could add carve-outs for legally compelled disclosure, but not essential. |

### OPERATIONAL

| Issue | Rationale | Relevant Clauses | Contract Position | Assessment | Recommendation |
|-------|-----------|------------------|-------------------|------------|----------------|
| **14. Service levels** | Define availability; provide remedies for downtime; manage customer expectations | Clause 9.1, Appendix 3 | **No SLA.** Clause 9.1 expressly disclaims "uninterrupted or error free" operation. **No uptime commitment.** **No service credits.** Appendix 3 describes infrastructure (multi-AZ, failover) but makes no availability commitment. | **Missing (intentionally).** For a £35/month service this is commercially appropriate — SLAs create administrative overhead and liability exposure disproportionate to revenue. | No change needed for this price point. For enterprise deals, add SLA schedule with uptime target (e.g. 99.5%) and service credit mechanism. |
| **15. Support and maintenance** | Define support scope; set expectations; exclude out-of-scope requests | Clauses 2.1.4, 5.5, Appendix 2 | **Support**: "General administrative and limited front line support" (Clause 2.1.4). Appendix 2 describes training options and purchasable 2-hour support packs. **Maintenance**: Lamplight may upgrade/enhance services (Clause 5.5). Reasonable endeavours to avoid 8am–8pm disruption on working days. Emergency maintenance permitted any time with advance warning where possible. | **Adequate.** Support deliberately limited — appropriate for price point. Additional support available for purchase. Maintenance window flexibility is supplier-friendly. | Consider specifying support hours (e.g. 9am–5pm UK business days) and response time target (e.g. 2 business days) even if not an SLA. Currently undefined. |
| **16. Change management** | Allow supplier flexibility to evolve service; protect customer from material adverse changes | Clauses 5.3–5.5, 6 | **Supplier changes**: Lamplight can replace/vary Third Party Applications or Service Provider with 14 days' notice where possible (Clause 5.3). Customer can terminate on 30 days' notice if dissatisfied (Clause 5.4). Upgrades/enhancements permitted (Clause 5.5). **Customer changes**: Via Change Control (Clause 6) — customer submits request, Lamplight quotes, mutual agreement required. | **Strong.** Supplier has appropriate flexibility. Customer exit right for material changes is fair balance. Change control protects against scope creep. | No change needed. |

### EXIT AND DISPUTES

| Issue | Rationale | Relevant Clauses | Contract Position | Assessment | Recommendation |
|-------|-----------|------------------|-------------------|------------|----------------|
| **17. Termination rights** | Ability to exit; grounds for immediate termination; consequences | Clause 13 | **Convenience** (Clause 13.1): Either party, 30 days' notice, at end of Initial Term or any time after. **Material breach** (Clause 13.2.1): 30 days to cure, then immediate termination. **Insolvency** (Clauses 13.2.2–13.2.4): Immediate termination. **Customer discontinues use** (Clause 13.3): Lamplight can terminate immediately. **Service Provider breach** (Clause 13.4): Either party, 30 days' notice. | **Strong.** Supplier has good termination rights including for discontinued use (catches dormant accounts). Mutual insolvency trigger. Material breach allows 30-day cure — reasonable. | No change needed. |
| **18. Exit provisions** | Data return; transition; survival | Clause 13.5, Appendix 4 (section 3) | **Survival**: Clauses 7 (confidentiality) and 8 (data protection) survive. **Data**: Access suspended immediately on termination; deleted within 28 days (Appendix 4). **No transition assistance obligation.** **No express data export right.** | **Weak.** Survival clause is adequate. Data deletion timeline is clear. However, **no obligation to provide data in usable format** and **no transition assistance**. | Add: (1) Express data export right (machine-readable format, 28-day window); (2) Consider optional paid transition assistance. See Issue 10. |
| **19. Dispute resolution** | Efficient resolution; appropriate forum; avoid excessive litigation costs | Clause 15 | **Governing law**: English (Clause 15.1). **Escalation** (Clause 15.2.1): Senior management, 14 days. **Expert determination** (Clause 15.2.2): For technical disputes, BCS-nominated expert. **Litigation** (Clause 15.2.3): High Court of Justice, exclusive jurisdiction. | **Strong.** Good tiered approach. Expert determination for technical disputes is sensible and cost-effective. English courts appropriate. | No change needed. |

### STRUCTURAL

| Issue | Rationale | Relevant Clauses | Contract Position | Assessment | Recommendation |
|-------|-----------|------------------|-------------------|------------|----------------|
| **20. Boilerplate adequacy** | Standard protections; avoid unintended consequences | Clause 14 | **Force majeure** (Clause 14.1): Mutual, payment obligations carved out — good. **Assignment** (Clause 14.2): Customer cannot assign without Lamplight's consent. **No restriction on Lamplight** — can assign freely. **Severability** (Clause 14.3): Standard. **Waiver** (Clause 14.4): Written waivers only. **Third parties** (Clause 14.5): Contracts (Rights of Third Parties) Act 1999 excluded. **Entire agreement** (Clause 14.6): Comprehensive, includes non-reliance acknowledgment and written variation requirement. **Notices**: **Not addressed.** Clause 1.7 says "writing" includes faxes but not email — outdated. | **Adequate** with gaps. Core boilerplate is sound. Assignment asymmetry is supplier-friendly. **However**: (1) No notices clause (addresses, deemed receipt); (2) "Writing" definition excludes email — outdated. | Add notices clause specifying: addresses for each party; permitted methods (including email); deemed receipt rules. Update Clause 1.7 to include email. |

---

## Issues Not Addressed

| Issue | Risk Level | Comment |
|-------|------------|---------|
| **Insurance requirements** | Low | No mutual insurance requirements. Acceptable for this contract size. |
| **Service levels / SLA** | Low | Intentionally excluded for £35/month product. Would need adding for enterprise deals. |
| **Acceptable use policy** | Low | Clause 2.2.4 restricts use to internal purposes. Customer indemnity (Clause 12) provides some protection. Express AUP would be clearer. |
| **Anti-bribery / Modern Slavery** | Low | Increasingly expected but not essential for this contract size. |

---

## Cross-Cutting Concerns

### 1. Liability Cap and Indemnity Interaction

**Issue**: Clause 10.3 states that the 125% cap applies to claims "based on any claim for indemnity or contribution". Clause 11.3 states that the IP indemnity provisions represent "the entire liability of Lamplight with respect to infringement". These provisions could be read together or in tension.

**Risk**: Uncertainty about whether IP indemnity claims are subject to the 125% cap.

**Recommendation**: Add clarifying language to Clause 11: "This Clause 11 is subject to the limitations in Clause 10."

### 2. Data Protection and Liability Cap Interaction

**Issue**: No super-cap for data protection breaches. A significant breach could generate regulatory fines and third-party claims well in excess of £525/year (125% of 12 months × £35).

**Risk**: Disproportionate exposure for data protection incidents.

**Recommendation**: Consider adding super-cap (e.g. 3–5x annual fees) for data protection claims. Alternatively, ensure Lamplight carries adequate cyber liability insurance.

### 3. Customer Acknowledgments and UCTA

**Issue**: Customer is a charity/CIC. The contract contains several customer acknowledgments designed to support UCTA reasonableness (Clauses 9.4, 10.4). However, charities can sometimes argue they are not acting "in the course of business".

**Risk**: Low — CICs are commercial entities and this is clearly a business-to-business transaction. Acknowledgments help.

**Recommendation**: Consider adding express warranty from customer that it is entering the agreement in the course of its business and not as a consumer.

### 4. EEA/EU References vs UK Post-Brexit

**Issue**: Multiple references to EEA (Clauses 8.5.3, 8.9, 8.10) and EU SCCs (Clause 8.9.1) rather than UK GDPR framework.

**Risk**: Technical non-compliance with UK data protection terminology. May cause confusion about applicable framework.

**Recommendation**: Comprehensive update to reference UK GDPR, UK territory, and UK IDTA for international transfers.

---

## Priority Actions Summary

| Priority | Action | Effort |
|----------|--------|--------|
| **High** | Add annual price review clause | 30 mins |
| **Medium** | Update GDPR references for UK (EEA → UK, EU SCCs → UK IDTA) | 1 hour |
| **Medium** | Add explicit data export right on termination | 30 mins |
| **Medium** | Clarify IP indemnity is subject to liability cap | 15 mins |
| **Low** | Add notices clause | 30 mins |
| **Low** | Update "writing" definition to include email | 10 mins |
| **Low** | Add express warranty of commercial capacity | 15 mins |

**Total estimated effort**: 3–4 hours

---

*Ready for Pass 2 (Precedent Comparison) when instructed.*
