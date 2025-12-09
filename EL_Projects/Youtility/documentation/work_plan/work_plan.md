# Work Plan: Youtility-Pockit POC Agreement v0.1

**Document:** Youtility-Pockit POC Agreement v0.1.docx  
**Date:** 9 December 2025  
**Client:** Youtility Limited (Supplier)  
**Counterparty:** Pockit Limited (Customer)  

---

## 1. Executive Summary

This is a Proof of Concept (POC) Services Contract for behavioural data analytics services. Youtility (Supplier) will receive behavioural data from Pockit's end users (~10k users), perform analytics using Youtility's proprietary model, and return enriched data with behavioural insights. The services are provided at no charge.

**Key Client Objectives (from instructions):**
- Youtility wants to be positioned as an independent controller (not a processor) for data protection purposes
- Youtility wants freedom to use the data to improve its own behavioural analytics engine
- Pockit retains responsibility for its regulatory obligations (financial regulation, consumer protection, consumer credit)

---

## 2. Recommended Edits

### 2.1 Front Matter / Contract Details

| Priority | Location | Issue | Recommended Edit |
|----------|----------|-------|------------------|
| **High** | Contract Details - DATE | Placeholder not completed | Insert actual date of signing |
| **High** | Contract Details - Customer Email | Placeholder [EMAIL ADDRESS] | Insert Pockit's contact email address |
| **High** | Contract Details - Supplier Email | Placeholder [EMAIL ADDRESS] | Insert Youtility's contact email address |
| **Medium** | Signature blocks | Placeholder [NAME OF DIRECTOR] | Insert names of signing directors for both parties |

---

### 2.2 Definitions (Clause 1)

| Priority | Location | Issue | Recommended Edit |
|----------|----------|-------|------------------|
| **Medium** | Clause 1.1 - "Business Day" | Not bold formatted like other defined terms | Format "Business Day" in bold for consistency |
| **Low** | Clause 1.1 - "Conditions" | Not bold formatted like other defined terms | Format "Conditions" in bold for consistency |
| **Low** | Clause 1.1 - "control" | Not bold formatted like other defined terms | Format "control" in bold for consistency |
| **Low** | Clause 1.1 - "Effective Date" | Not bold formatted like other defined terms | Format "Effective Date" in bold for consistency |

---

### 2.3 Data Protection (Clause 5 & Schedule 2)

| Priority | Location | Issue | Recommended Edit |
|----------|----------|-------|------------------|
| **High** | Clause 5 | Cross-reference shows "0" instead of Schedule 2 | Fix cross-reference: "Each party shall comply with its data protection obligations set out in **Schedule 2**." |
| **Medium** | Schedule 2, Para 1.3 - Agreed Purposes | Purpose (b) "configuration and augmentation of the Supplier's behavioural analytics model" could be strengthened | Consider expanding: "the configuration, improvement and augmentation of the Supplier's behavioural analytics model, including the training and development of the Supplier's algorithms and analytical capabilities" |
| **Low** | Schedule 2, Para 2.2 | Independent controller status is clear but could benefit from additional clarity | Consider adding: "For the avoidance of doubt, neither party is a joint controller with the other party, and each party shall independently determine the purposes and means of its own processing of the Shared Personal Data." |

---

### 2.4 Intellectual Property Rights (Clause 6)

| Priority | Location | Issue | Recommended Edit |
|----------|----------|-------|------------------|
| **High** | Clause 6.3 | States Customer retains IP in "any adaptation or enrichment of the Customer Materials as a result of the Services" - this may conflict with Youtility's right to use data to improve its model | Consider clarifying: "The Customer and its licensors shall retain ownership of all Intellectual Property Rights in the Customer Materials. The Customer grants the Supplier a non-exclusive, royalty-free, perpetual licence to use, copy and modify the Customer Materials for the Agreed Purposes. **For the avoidance of doubt, the Supplier shall retain all Intellectual Property Rights in any aggregated, anonymised or derived insights, models, algorithms or analytical outputs developed by the Supplier using the Customer Materials, provided that such materials do not identify or relate to any identifiable individual.** The Supplier may grant sublicences of the Customer Materials to its subcontractors and other suppliers where necessary for the performance of the Services." |
| **Medium** | Clause 6.2 | Restriction on sublicensing references rights "granted in clause 6.1" but 6.1 doesn't grant rights to Customer | Review and clarify - clause 6.1 retains Supplier ownership, it doesn't grant Customer any rights. Consider deleting or rewording this clause. |
| **Medium** | Schedule 1, Para 2 (Deliverables) | States "The Supplier retains all Intellectual Property Rights in its behavioural analytics model, methodology, algorithms and any aggregated or anonymised insights derived from the Input Data" | Ensure this is consistent with Clause 6.3 - consider adding explicit cross-reference or harmonising language |

---

### 2.5 Limitation of Liability (Clause 8)

| Priority | Location | Issue | Recommended Edit |
|----------|----------|-------|------------------|
| **Medium** | Clause 8.4(b) | IP indemnity cap of £1,000,000 may be high for a no-charge POC | Consider whether a lower cap (e.g., £100,000 or £250,000) would be more proportionate, or tie the cap to insurance coverage |
| **Low** | Clause 8.4(c) | General liability cap of £1,000 is very low | This is appropriate for a free POC, but ensure the client is comfortable with this level |
| **Medium** | Clause 8.2 - 8.4 | Exclusions and limitations only apply to Supplier | Consider whether mutual liability caps/exclusions are appropriate - the data protection indemnity in Schedule 2, Para 2.5 is uncapped |

---

### 2.6 Customer Obligations (Clause 4)

| Priority | Location | Issue | Recommended Edit |
|----------|----------|-------|------------------|
| **High** | Clause 4 | No explicit acknowledgment that Pockit is responsible for its regulatory obligations | Add new subclause 4.1(c): "comply with all regulatory obligations applicable to the Customer's business, including (without limitation) any obligations arising under financial services, consumer protection or consumer credit legislation. For the avoidance of doubt, the Supplier is not responsible for the Customer's compliance with such regulatory obligations and the Services do not constitute regulated advice or services." |

---

### 2.7 Services Description (Schedule 1)

| Priority | Location | Issue | Recommended Edit |
|----------|----------|-------|------------------|
| **Low** | Schedule 1, Para 1 | Services description is comprehensive | No changes required |
| **Low** | Schedule 1 | No specified timeline for delivery | Consider adding expected delivery timeframe or milestone dates if known |
| **Low** | Schedule 1 | No data format specification | Consider adding provisions about data format, method of delivery, and technical requirements for the Input Data |

---

### 2.8 Confidentiality (Clause 10.2)

| Priority | Location | Issue | Recommended Edit |
|----------|----------|-------|------------------|
| **Medium** | Clause 10.2(c) | Permitted use includes "the Agreed Purposes and/or to exercise its rights and perform its obligations under the Contract" | This is good - it allows Youtility to use Customer Materials/Confidential Information for the Agreed Purposes (which includes improving Youtility's model) |
| **Low** | Clause 10.2(a) | 2-year post-termination confidentiality period | Consider whether this is appropriate - may want to extend given the sensitive nature of behavioural data |

---

### 2.9 Termination (Clause 9)

| Priority | Location | Issue | Recommended Edit |
|----------|----------|-------|------------------|
| **Medium** | Clause 9 | No termination for convenience right | Consider adding: "Either party may terminate this Contract at any time by giving not less than 7 days' written notice to the other party." - this provides flexibility for a POC arrangement |
| **Low** | Clause 9 | No data return/deletion provisions on termination | Consider adding provisions requiring return or secure deletion of Customer Materials on termination (subject to Supplier's rights to retain aggregated/anonymised data) |

---

### 2.10 General Provisions (Clause 10)

| Priority | Location | Issue | Recommended Edit |
|----------|----------|-------|------------------|
| **Low** | Clause 10.3(b) | Standard entire agreement acknowledgment | No changes required |
| **Low** | Clauses 10.9-10.10 | English law and jurisdiction | Appropriate - no changes required |

---

## 3. Issues for Client Discussion

1. **Data Protection - Controller Status:** The contract positions both parties as independent controllers (Schedule 2, Para 2.2), which aligns with Youtility's instructions. However, this should be discussed with the client to confirm they are comfortable with the full implications of controller status, including:
   - Independent responsibility for data subject rights requests
   - Independent responsibility for security measures
   - Potential regulatory exposure

2. **Agreed Purposes Scope:** The "Agreed Purposes" in Schedule 2, Para 1.3 include "configuration and augmentation of the Supplier's behavioural analytics model." Confirm this is sufficiently broad to cover Youtility's intended use of the data to improve its analytics engine.

3. **Retention of Derived Insights:** Clause 6.3 and Schedule 1 should be harmonised to make clear that Youtility can retain aggregated/anonymised insights. Discuss whether perpetual retention is required or whether a time limit is acceptable.

4. **IP Indemnity Cap:** The £1,000,000 cap on IP indemnities may be disproportionate for a no-charge POC. Discuss with client whether this should be reduced or matched to insurance coverage.

5. **Regulatory Responsibilities:** Confirm that Pockit understands and accepts that it alone is responsible for FCA compliance, consumer credit obligations, and any use it makes of the analytics outputs.

---

## 4. Marked-Up Document Preparation

Once edits are agreed, the following should be prepared:
- [ ] Complete all placeholder fields (date, emails, director names)
- [ ] Fix cross-reference error in Clause 5
- [ ] Add regulatory responsibility acknowledgment to Clause 4
- [ ] Clarify IP position in Clause 6.3 and Schedule 1
- [ ] Consider adding termination for convenience
- [ ] Review and confirm liability caps
- [ ] Format inconsistent defined terms

---

## 5. Next Steps

1. Review this Work Plan with supervising partner
2. Discuss key issues with Youtility client
3. Prepare marked-up draft with agreed amendments
4. Circulate to Pockit for review
5. Negotiate any pushback on amendments
6. Finalise and arrange for signature

---

*Prepared by: [Associate Name]*  
*Reviewed by: [Partner Name]*
