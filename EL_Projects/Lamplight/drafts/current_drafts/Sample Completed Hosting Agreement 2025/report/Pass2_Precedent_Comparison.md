# Pass 2 – Precedent Comparison

**Client Document**: Lamplight Hosting Agreement (20 October 2025)  
**Precedent**: Online SaaS Terms and Conditions (Pro-Supplier)  
**Perspective**: Supplier (Lamplight Database Systems Ltd)  
**Date**: 4 December 2025

---

## Executive Summary

**Overall Assessment**: The Lamplight terms are **broadly equivalent** to the precedent on core risk allocation but are **weaker on commercial protection mechanisms** and **missing several supplier-protective provisions** that the precedent includes.

The Lamplight agreement is a bespoke, traditionally-drafted hosting contract that works well for its purpose—a low-value charity SaaS subscription. However, compared to the precedent (which is designed for scalable self-service SaaS), Lamplight's terms lack several modern drafting features that protect supplier revenue and manage customer expectations.

**Top Priority Issues to Address**:

1. **Price Escalation** (High) – Precedent includes annual price increase right; Lamplight silent
2. **Data Return on Termination** (High) – Precedent includes time-limited request mechanism with cost recovery; Lamplight silent (customer could demand return years later)
3. **Written Notice Definition** (Medium) – Precedent explicitly includes email; Lamplight explicitly excludes it
4. **GDPR References** (Medium) – Lamplight references EU GDPR; precedent correctly uses UK GDPR
5. **User Licence Audit Rights** (Medium) – Precedent includes audit rights for per-user licences; Lamplight lacks (though unlimited users mitigates this for current contract)

**Key Structural Gaps**:
- No formal notices clause (addresses, deemed receipt)
- No express prohibition on competitive use of services
- No heightened cybersecurity disclaimer
- No trial period provisions (if ever needed)
- No surviving confidentiality time limit

---

## Clause-by-Clause Comparison

| Issue | Precedent Position | Client Position | Assessment | Recommendation | Priority |
|-------|-------------------|-----------------|------------|----------------|----------|
| **Price Escalation** | Clause 9.4: Supplier entitled to increase Fees on each anniversary of Subscription Start Date upon 60 days' notice. Order Details deemed amended accordingly. | Silent. Appendix 1 sets fixed £35/month fee with no escalation mechanism. Only mentions increase for excess users/bandwidth. | Precedent stronger. Lamplight has no inflation protection; over a multi-year contract, real revenue declines. | Add annual price review clause: *"Lamplight may increase the Fees on each anniversary of the Commencement Date upon 60 days' prior written notice to the Customer."* Model on precedent cl. 9.4. | **High** |
| **Data Return on Termination** | Clause 14.3(c): Supplier may destroy Customer Data unless written request received within 10 days of termination. Delivery within 30 days, subject to payment of outstanding fees. Customer pays reasonable expenses. | Silent on data return. Appendix 4 para 3 addresses deletion (28 days post-termination) but gives customer no express right to request return. | Precedent stronger. Lamplight's silence means customer could demand data return at any time, with no cost recovery right. | Add data return mechanism: *"The Customer may request return of Customer Data in writing within 14 days of termination. Lamplight shall deliver such data within 30 days, subject to payment of all outstanding fees and reasonable extraction costs."* | **High** |
| **Written Communications** | Clause 1.9: "A reference to writing or written includes e-mail." Clause 24: Full notices clause with deemed receipt rules for hand, post and email. | Clause 1.7: "A reference to writing or written includes faxes but not e-mail." No notices clause. | Precedent more practical. Email exclusion is outdated and operationally awkward for a modern SaaS business. | Amend definition to include email: *"A reference to writing or written includes e-mail."* Add notices clause based on precedent cl. 24 with addresses in Appendix 1. | **Medium** |
| **GDPR Definition** | Clause 1.1: Defines UK GDPR (per DPA 2018) and EU GDPR separately. Applicable Data Protection Laws references UK legislation first. | Clause 1.1.5: References "the GDPR" meaning EU Regulation 2016/679. Clause 1.1.8 defines GDPR as EU regulation. Clause 8.5.3 refers to transfers outside EEA. | Precedent correct for post-Brexit UK. Lamplight's EU/EEA references are technically inaccurate for UK law. | Update definitions: Replace "GDPR" with "UK GDPR" referencing DPA 2018. Update cl. 8.5.3 and 8.9 to refer to transfers outside UK rather than EEA. | **Medium** |
| **Liability Cap** | Clause 13.4(c): Aggregate liability limited to total Fees paid in 12 months preceding claim. | Clause 10.3: Aggregate liability limited to 125% of total fees paid in preceding 12 months. | Lamplight marginally more generous (125% vs 100%). Both acceptable. | No change required. 125% cap is reasonable and may aid UCTA reasonableness. | None |
| **IP Indemnity Scope** | Clause 12.2-12.5: Indemnity for UK/European patent, copyright, trademark, database right, confidentiality. Express carve-outs (customer modification, misuse, post-notice use, customer data, customer breach). Sole and exclusive remedy stated. | Clause 11.1-11.3: Indemnity for IP infringement. Reasonable carve-outs. States "entire liability" but less detailed than precedent. No express sole remedy language for customer. | Broadly equivalent. Lamplight's indemnity is adequate but less polished. | Consider adding express "sole and exclusive remedy" wording to cl. 11.3 for clarity: *"This Clause 11 states the Customer's sole and exclusive rights and remedies, and Lamplight's entire obligations and liability, for infringement of any third party Intellectual Property Rights."* | **Nice-to-have** |
| **Customer Indemnity** | Clause 12.1: Customer indemnifies supplier for claims arising from customer/authorised user use of services. Broad scope. | Clause 12.1: Customer indemnifies for IP/rights infringement from use of Customer Data. Narrower scope. | Precedent broader (covers all use-related claims). Lamplight's narrower scope is adequate but could be enhanced. | Consider broadening customer indemnity to cover misuse of services, not just Customer Data IP issues. Model on precedent cl. 12.1. | **Nice-to-have** |
| **Licence Restrictions** | Clause 2.4-2.5: Detailed acceptable use policy and restrictions (no reverse engineering, no competitive use, no sublicensing, no virus introduction). | Clause 2.2.4-2.2.5: Customer may only use for own data/internal purposes. Customer responsible for backup. No express reverse engineering or competitive use prohibition. | Precedent more protective. Lamplight lacks express restrictions that are standard in SaaS terms. | Add licence restrictions clause: *"The Customer shall not: (a) reverse engineer, decompile or disassemble the Application; (b) use the Service to build a competing product; (c) introduce any virus or malware into the Service."* | **Medium** |
| **User Audit Rights** | Clause 2.2(d)-(g): Customer must maintain user list, permit quarterly audits, disable unauthorised users, pay underpayment. | Silent. Appendix 1 specifies "Unlimited" users. | Precedent more protective for per-user models. Lamplight's unlimited user model means this is currently moot, but if user limits are ever introduced, audit rights would be needed. | No immediate change required. If user limits are introduced in future, add audit provisions modelled on precedent cl. 2.2(e)-(g). | None (for now) |
| **Support and SLAs** | Clause 3.2: Support per Support Policy, which supplier can amend (but not materially to customer's detriment). No defined SLAs in template. | Appendix 2: Support via online manual, videos, training courses, optional paid support packs. Appendix 3: Detailed DR/backup policy. No SLAs. | Equivalent for price point. Neither includes binding SLAs. Lamplight's detailed Appendix 3 is a strength. | No change required. Appendix 3 is supplier-favourable (sets expectations without binding commitments). | None |
| **Service Modifications** | Clause 3.3: Supplier may update Software and change Services, provided no material reduction in functionality. | Clause 5.3-5.5: Supplier may replace Third Party Applications/Service Provider with notice. Customer termination right if dissatisfied. Upgrades permitted with reasonable notice. | Equivalent. Both permit supplier flexibility with customer protections. Lamplight's termination right for dissatisfied customers is slightly more customer-friendly. | Consider whether 30-day termination right for service provider changes (cl. 5.4) is too generous. Could reduce to 14 days or remove. | **Nice-to-have** |
| **Payment Default** | Clause 9.2: Supplier may disable access; interest at 4% over base rate. | Clause 3.2: Supplier may suspend services; statutory interest per Late Payment Act. | Equivalent. Lamplight's Late Payment Act reference may yield higher interest (currently 8% + base). | No change required. Late Payment Act reference is appropriate. | None |
| **Entire Agreement** | Clause 20.1-20.4: Full entire agreement with no-reliance and no-remedy clauses. Fraud carve-out. | Clause 14.6: Entire agreement, supersedes prior communications, no-reliance statement. | Broadly equivalent. Lamplight's version is slightly less detailed. | No change required. | None |
| **Assignment** | Clause 21.1-21.2: Customer needs consent; supplier can assign freely. | Clause 14.2: Customer needs consent. Silent on supplier rights. | Precedent more explicit. Lamplight should confirm supplier's assignment right. | Add: *"Lamplight may assign, transfer or subcontract any of its rights or obligations under this Agreement without the Customer's consent."* | **Medium** |
| **Confidentiality Survival** | Clause 11.8: Survives for 5 years post-termination. | Clause 7.1: Survives termination but no time limit stated. | Precedent more certain. Lamplight's perpetual confidentiality is arguably stronger but less predictable. | Could add time limit for certainty: *"The foregoing obligations as to confidentiality shall remain in full force and effect for five years from termination."* Alternatively, leave as perpetual if preferred. | **Nice-to-have** |
| **Termination Notice** | Clause 14.1(b): Either party may terminate at end of Initial Term or Renewal Period with notice equal to Notice Period (30 days default). | Clause 13.1: Either party may terminate at end of Initial Term on 30 days' notice; after Initial Term, 30 days' notice at any time. | Lamplight slightly more customer-friendly (allows termination at any time after initial term, not just at period end). | Consider whether mid-period termination right is intended. Could align with precedent (termination only at period end). | **Nice-to-have** |
| **Force Majeure** | Clause 15: Supplier-only relief. Standard events including pandemic. Customer must be notified. | Clause 14.1: Neither party liable for delay. Standard drafting. | Precedent more supplier-protective (relief only for supplier). Lamplight's mutual relief is more balanced. | Could adopt supplier-only force majeure for stronger position. Current drafting acceptable. | **Nice-to-have** |
| **Governing Law** | Clause 25-26: English law, exclusive jurisdiction of English courts. | Clause 15.1, 15.2.3: English law, High Court exclusive jurisdiction. Also includes expert determination for technical disputes. | Equivalent. Lamplight's expert determination clause is an additional feature (could be useful or could be removed). | No change required. Expert determination is optional—could be retained or removed. | None |

---

## Structural Gaps (Missing Clauses)

| Missing From Client | Precedent Reference | Risk Level | Why It Matters |
|---------------------|---------------------|------------|----------------|
| **Notices Clause** | Clause 24 | Medium | No formal mechanism for deemed receipt of notices. Creates uncertainty about when termination notices, breach notices etc. take effect. |
| **Express Email Inclusion** | Clause 1.9 | Medium | Excluding email from "writing" is impractical for modern business. Termination by email may be ineffective. |
| **Competitive Use Prohibition** | Clause 2.5(b) | Low | No express bar on customer using services to build competing product. Low risk for charity customer, but gap in template. |
| **Heightened Cybersecurity Disclaimer** | Clause 7.3(a)(iv), Definition | Low | No express disclaimer that services don't comply with sector-specific cybersecurity regulations. Lamplight's target market (charities) unlikely to be affected, but gap in template. |
| **Trial Period Provisions** | Clause 3.4, Definition | Low | No mechanism for trial periods. Not relevant to current contract but gap if Lamplight offers trials. |
| **Supplier Assignment Right** | Clause 21.2 | Medium | No express right for Lamplight to assign. Could impede business sale. |
| **Third Party Provider Disclaimer** | Clause 6 | Low | Precedent has standalone clause disclaiming liability for third-party content. Lamplight addresses third parties via Service Provider structure but less comprehensively. |
| **Variation Clause** | Clause 16 | Low | Lamplight covers in cl. 14.6 (changes must be in writing and signed) but no standalone clause. |

---

## Client Additions (Not in Precedent)

| Client Clause | Topic | Assessment | Comment |
|---------------|-------|------------|---------|
| **Clause 4** | Acceptance Tests | **Good** | Deems services accepted if customer uses in live environment without testing. Supplier-protective. |
| **Clause 5.3-5.4** | Service Provider Changes | **Good** | Clear mechanism for changing third-party providers with customer termination right. More structured than precedent's general approach. |
| **Clause 6** | Change Control | **Neutral** | Formal change request procedure. Useful for bespoke implementations but may be overkill for standard SaaS. |
| **Appendix 3** | Backup and DR | **Good** | Detailed technical appendix setting expectations clearly. Not a legal commitment but manages expectations. |
| **Clause 15.2.2** | Expert Determination | **Neutral** | Technical disputes referred to expert. Potentially useful but adds process. Could be removed for simplicity. |
| **Clause 8.6** | Security Acknowledgements | **Good** | Detailed customer acknowledgements limiting Lamplight's security obligations to industry-standard measures. Supplier-protective. |
| **Clause 8.7** | Security Depends on Payment | **Good** | Customer acknowledges security depends on level of security "adopted and paid for by the Customer". Good risk allocation. |
| **Clause 9.3** | Warranty Time Limit | **Good** | 3-month warranty claim window. Supplier-protective time limit. |
| **Clause 10.4** | Negotiation Acknowledgement | **Good** | Customer acknowledges it could have negotiated higher liability limits. Supports UCTA reasonableness. |

---

## Summary of Recommendations

### High Priority

1. **Add price escalation clause** (model on precedent cl. 9.4)
2. **Add data return mechanism** with time limit and cost recovery (model on precedent cl. 14.3(c))

### Medium Priority

3. **Amend "writing" definition** to include email (precedent cl. 1.9)
4. **Add notices clause** with addresses and deemed receipt (precedent cl. 24)
5. **Update GDPR references** to UK GDPR, replace EEA with UK
6. **Add licence restrictions** (reverse engineering, competitive use prohibition)
7. **Add express supplier assignment right** (precedent cl. 21.2)

### Nice-to-Have

8. Clarify IP indemnity as "sole and exclusive remedy"
9. Broaden customer indemnity scope
10. Consider reducing customer termination right for service provider changes
11. Add confidentiality survival period (5 years)
12. Align termination to period-end only (if mid-period termination not intended)
13. Consider supplier-only force majeure

---

*Prepared for internal review. Not client-ready without further formatting.*
