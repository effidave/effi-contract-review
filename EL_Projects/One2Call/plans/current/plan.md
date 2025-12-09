---
tasks:
- id: 2540deb3
  title: 0.0 PROJECT CONTEXT (Read First)
  description: '**PROJECT CONTEXT — READ FIRST**


    **Client:** One2Call Limited, Sheffield UK (Reg No: 06220567)

    **Business:** Managed Service Provider (MSP) — IT support, cyber security, cloud,
    connectivity, telecoms, hardware

    **Accreditations:** ISO 27001, ISO 9001, Cyber Essentials Plus


    **Objective:** Consolidate and modernise One2Call''s customer-facing contracts
    by:

    1. Enhancing the existing MSA (HJ7) with provisions from old service-specific
    terms

    2. Creating a modular Schedule/Annex structure that can be assembled per Order

    3. Replacing 9 legacy service-specific T&Cs with the new unified structure


    **Source Documents:**

    • MSA (HJ7): `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\drafts\current_drafts\One2call  -
    2025 Templates  - MSA Defined Services - HJ7.docx`

    • Maintenance Schedule (HJ1): `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\drafts\current_drafts\One2call  -
    2025 Templates  - Maintenance Schedule - HJ1.docx`

    • Old terms (markdown conversions): `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\[DocumentName]\[DocumentName].md`

    • Precedents: `C:\Users\DavidSant\effi-contract-review\EL_Projects\Precedents\Pro-Supplier\managed_it_services\`


    **Approved Document Architecture (Option B):**

    ```

    MSA (HJ7)

    ├── Cover / Order Form (commercial details, service selection, term/notice overrides)

    ├── Schedule 1: Terms and Conditions (core legal terms — enhance per Tasks 1.1-1.3,
    1.7-1.8)

    ├── Schedule 2: Data Protection (existing)

    ├── Schedule 3: Installation & Provisioning Services (NEW — common framework)

    │   ├── Annex 3A: Managed IT Services

    │   ├── Annex 3B: Cyber Security Services

    │   ├── Annex 3C: Cloud Management

    │   ├── Annex 3D: Connectivity (Ethernet — 36m/60d defaults)

    │   ├── Annex 3E: Telecoms (Horizon/VoIP — 24m/60d defaults)

    │   └── Annex 3F: Hardware Provision & Maintenance

    ├── Schedule 4: Security Schedule (optional — for cyber services)

    └── Schedule 5: Maintenance Schedule (from HJ1 — enhanced per Task 1.6)

    ```


    **Hierarchy of Documents:**

    1. Order Form (highest — overrides Annex defaults)

    2. Schedule 1 (Terms and Conditions)

    3. Schedule 3 + selected Annexes

    4. Other Schedules


    **Gap Analysis Status:**

    ✅ Ethernet terms → Task 1.5 (Schedule 3), Task 1.8 (MSA core), Annex 3D specifics

    ✅ Horizon terms → Task 3.1 (Annex 3E with prominent 999 warning + client comment)

    ✅ Phone Maintenance → Task 1.6 (Schedule 5 enhancements)

    ✅ Access Control Maintenance → Task 1.6 (Schedule 5 enhancements)

    ✅ CCTV Maintenance → Task 1.6 (Schedule 5 enhancements)


    **Gap Analysis Remaining (Task 1.9):**

    • Mobile terms — Different structure (25 clauses); may need separate treatment

    • Business Comms — To be analysed

    • Sale of Goods — To be analysed


    **Key Decisions Made:**

    • Default response times: 4h (>50% failure) / 8h (other) — in Schedule 5

    • Phone system exception: 9h response time via conditional clause in Schedule
    5 cl 7.3(b)

    • Service credits: Menu in Order Form (£50 / 5% / 10% / custom)

    • Equipment Maintenance: Indicated in Order Form; if selected, Schedule 5 applies

    • 999 emergency warning: Prominent in Annex 3E (not Order Form); client comment
    explaining regulatory significance

    • Equipment theft/destruction: Softer approach than old terms (30-day termination
    right); client comment explaining departure


    **MSA Provisions Already Adequate (no duplication needed):**

    • Price increases: MSA cl 11.7 (pass-through + once per 12m + >10% termination
    right)

    • Interest on late payment: MSA cl 14.14 (8% above BoE base rate)

    • Liability cap: MSA cl 19.4 (£100k per client instruction)


    **Drafting Style:** British English per grammar.md (-ise, -our, licence/license
    distinction, UK date format, no Oxford comma)


    **Jurisdiction:** English law, UK GDPR, EU GDPR'
  status: pending
  ordinal: 0
  creationDate: '2025-12-09T22:12:13.037368Z'
  completionDate: null
  editIds: []
- id: 6be41a3d
  title: 0.1 Record all Decisions for Client Info
  description: '**DECISIONS LOG — For Client Advice Note**


    This task captures key decisions made during the contract review and consolidation
    project. These should be communicated to the client in the final advice note.


    ---


    ## STRUCTURAL DECISIONS


    **DECISION S1: Document Architecture (Option B)**


    **Decision:** Adopt modular MSA structure with detachable Schedules and Annexes.


    **Structure:**

    ```

    MSA (HJ7)

    ├── Cover / Order Form (commercial details, service selection, term/notice overrides)

    ├── Schedule 1: Terms and Conditions (core legal terms)

    ├── Schedule 2: Data Protection (existing)

    ├── Schedule 3: Installation & Provisioning Services (NEW — common framework)

    │   ├── Annex 3A: Managed IT Services

    │   ├── Annex 3B: Cyber Security Services

    │   ├── Annex 3C: Cloud Management

    │   ├── Annex 3D: Connectivity (Ethernet — 36m/60d defaults)

    │   ├── Annex 3E: Telecoms (Horizon/VoIP — 24m/60d defaults)

    │   └── Annex 3F: Hardware Provision & Maintenance

    ├── Schedule 4: Security Schedule (optional — for cyber services)

    └── Schedule 5: Maintenance Schedule (from HJ1)

    ```


    **Hierarchy:** Order Form (highest) → Schedule 1 → Schedule 3 + Annexes → Other
    Schedules


    **Rationale:** Provides flexibility to assemble contract per engagement while
    maintaining consistent core terms. Avoids repetition across service-specific documents.


    ---


    **DECISION S2: Separate Mobile from Horizon**


    **Decision:** Create separate Annex for Mobile services (not combined with Horizon
    VoIP in Annex 3E).


    **Rationale:** Mobile terms have fundamentally different structure (25 clauses
    vs 11) and cover different subject matter:

    - Mobile: SIM cards, handsets, porting, roaming, network coverage, MultiNet

    - Horizon: VoIP, SBC, IP addresses, emergency services warning


    **Impact:** May need Annex 3E-VoIP and Annex 3E-Mobile, or renumber to 3E and
    3G.


    ---


    **DECISION S3: Schedule 3 Common Framework**


    **Decision:** Extract common installation/provisioning provisions from Ethernet
    and Horizon terms into Schedule 3 (common framework), with service-specific details
    in Annexes.


    **Common provisions identified:**

    1. Site surveys

    2. Site preparation & amendments

    3. Installation obligations

    4. Commissioning & testing

    5. Acceptance testing (5 Working Days)

    6. Service demarcation point (framework)

    7. Equipment ownership & return

    8. Customer-supplied equipment

    9. Reservation of rights

    10. Appointment scheduling


    **Rationale:** Avoids repetition; ensures consistency across installed services.


    ---


    ## MAINTENANCE SCHEDULE DECISIONS


    **DECISION M1: Default Response Times**


    **Decision:** Set defaults in Schedule 5:

    - Response Time (>50% failure): 4 hours

    - Response Time (other faults): 8 hours

    - Business Hours: 8am-6pm Mon-Fri


    **Exception:** Phone systems default to 9 hours (not 8) via conditional clause
    in Schedule 5 cl 7.3(b).


    **Rationale:** Provides clean universal default with service-specific carve-out.
    Derived from Access Control/CCTV (8h) and Phone (9h) old terms.


    ---


    **DECISION M2: Service Credits**


    **Decision:** Offer menu of service credit options in Order Form (not defaults
    in Schedule 5):

    - £50 per breach (fixed)

    - 5% of monthly fee per breach

    - 10% of monthly fee per breach

    - Custom amount


    **Rationale:** Service credits vary significantly by customer and service value.
    Better to select per Order than impose universal default.


    ---


    **DECISION M3: Equipment-Specific Exclusions**


    **Decision:** Use conditional clause in Schedule 5 (not separate Annexes) for
    equipment-specific exclusions.


    **Example clause:** "If the Maintained Equipment includes telephone systems, the
    Maintenance Services shall not cover 2-wire devices unless expressly stated in
    the Order."


    **Rationale:** Only one equipment-specific exclusion identified (2-wire devices
    for phones). Doesn''t justify separate Annexes.


    ---


    **DECISION M4: Alterations to Equipment**


    **Decision:** Keep HJ1''s strict approach requiring prior written approval for
    alterations.


    **Rationale:** HJ1 approach is stricter than old terms (which allowed Customer
    alterations). Stricter approach protects Supplier''s maintenance obligations.


    ---


    **DECISION M5: Equipment Destruction/Theft**


    **Decision:** Add softer termination right (30 days'' notice) rather than old
    terms'' approach (Customer remains liable).


    **New clause:** "If the Maintained Equipment is destroyed, stolen, or damaged
    beyond repair, either party may terminate this Schedule on 30 days'' written notice,
    and the Customer shall pay the Standard Maintenance Fees up to the date of termination."


    **Client comment required:** "This clause departs from your old maintenance terms,
    which stated that theft/destruction of equipment would not affect the Customer''s
    payment obligations. We have softened this to allow either party to terminate
    on 30 days'' notice, with fees payable up to termination."


    ---


    **DECISION M6: Early Termination**


    **Decision:** Add early termination clause to Schedule 5 — remaining fees due
    if Customer terminates before end of term.


    **New clause:** "If the Customer terminates this Schedule before the end of the
    Service Initial Period or any Service Renewal Period (other than in accordance
    with clause 10.1 or for Supplier breach), the Customer shall pay to the Supplier
    all Standard Maintenance Fees that would have been payable for the remainder of
    that period."


    ---


    **DECISION M7: Scope Changes**


    **Decision:** Add scope change clause to Schedule 5 — Supplier may adjust fees
    if maintained equipment changes materially.


    **New clause:** "If the scope of the Maintained Equipment changes materially from
    that specified in the Order (including any increase in the number of users, devices,
    or software licences), the Supplier may, on reasonable written notice, adjust
    the Standard Maintenance Fees to reflect the changed scope."


    ---


    ## MSA CORE DECISIONS


    **DECISION C1: Price Increases — No Change Needed**


    **Decision:** MSA cl 11.7 already covers price increases adequately.


    **Existing provision:**

    - Pass-through of supplier increases: any time, 30 days notice

    - General inflationary increases: once per 12 months

    - Customer termination right: if single increase >10%, Customer can terminate
    within 14 days


    **Rationale:** Better than old maintenance terms which had no termination right.


    ---


    **DECISION C2: Interest on Late Payment — No Change Needed**


    **Decision:** MSA cl 14.14 already covers interest (8% above BoE base rate).


    **Rationale:** Actually higher than old terms (which had 4% in some documents,
    5% in others).


    ---


    **DECISION C3: Liability Cap — No Change Needed**


    **Decision:** MSA cl 19.4 already has £100,000 liability cap per client instruction.


    **Rationale:** Client has already made commercial decision on cap level.


    ---


    ## ANNEX 3E (HORIZON/VoIP) DECISIONS


    **DECISION V1: Emergency Services Warning Placement**


    **Decision:** Place 999/112 warning prominently at START of Annex 3E (not in Order
    Form).


    **Rationale:** Regulatory compliance requirement (Ofcom). Prominent placement
    in Annex ensures customers are clearly informed when they select VoIP services.


    **Client comment required:** "This warning is a regulatory compliance requirement
    for VoIP services. Ofcom requires providers to inform customers about the limitations
    of VoIP emergency calling. Failure to provide adequate warning could expose One2Call
    to regulatory action and liability claims."


    ---


    **DECISION V2: Equipment Maintenance via Order Form**


    **Decision:** Equipment Maintenance indicated in Order Form. If selected, Schedule
    5 (Maintenance Schedule) applies to the Maintained Equipment specified.


    **Rationale:** Clean separation — Order Form selects services; Schedule 5 contains
    maintenance terms.


    ---


    ## RETIREMENT DECISIONS


    **DECISION R1: Retire Standalone Sale of Goods Terms**


    **Decision:** Retire the standalone "Terms & Conditions for the Sale of Goods"
    document.


    **Rationale:** The MSA (HJ7) already contains comprehensive goods provisions at
    clauses 4-8:

    • Cl 4: Goods Specification

    • Cl 5: Delivery (notes, location, late/short delivery, instalments)

    • Cl 6: Acceptance (48-hour deemed acceptance, 5-day defect notification)

    • Cl 7: Quality/Warranty (description conformity, repair/replace/refund, UCTA
    exclusions)

    • Cl 8: Title and Risk (risk on delivery, title on payment, retention provisions)


    **Impact:** For pure product sales with no ongoing services, One2Call should use
    the MSA with an Order that specifies Goods only.


    **Old Document Path:** `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\One2Call-Terms-and-Conditions-for-the-Sale-of-Goods\`


    ---


    **DECISION R2: Retire Business Communications General Terms**


    **Decision:** The Business Communications General Terms will be replaced by the
    enhanced MSA (HJ7).


    **Rationale:** Business Communications is the current "master" document. The MSA
    will assume this role with improved provisions and modular structure.


    **Old Document Path:** `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\One2Call-Business-Communications-General-Terms-and-Conditions.pdf\`


    ---


    *Additional decisions to be added as they are made during this project.*'
  status: pending
  ordinal: 1
  creationDate: '2025-12-09T23:18:31.326988Z'
  completionDate: null
  editIds: []
- id: 905bd222
  title: 1.1 Fix critical drafting issues
  description: '(a) Correct Schedule numbering — The Terms and Conditions are headed
    "Schedule 2" but should be "Schedule 1" per the cover document structure. Correct
    this inconsistency.


    (b) Add "Data Protection Legislation" definition — This term is used in clause
    18.1 but not defined. Add definition to clause 1 referencing UK GDPR and EU GDPR.


    Reference: Managed services agreement (1).docx'
  status: pending
  ordinal: 2
  creationDate: '2025-12-09T19:51:13.454897Z'
  completionDate: null
  editIds: []
- id: 09b4f841
  title: 1.2 Expand clause 21 (exit/transition)
  description: 'Add exit/transition provisions covering:


    (a) Customer data extraction right — Customer may request return or deletion of
    Customer Data within 30 days of termination.


    (b) Transition assistance — Supplier to provide reasonable transition assistance
    for up to 3 months at Supplier''s then-current rates.


    (c) Data deletion certification — Following data return, Supplier to confirm deletion
    of Customer Data (subject to legal retention requirements).


    (d) Equipment — Customer equipment to be returned; Supplier equipment to be collected
    or purchased at net book value.


    Reference: Managed services agreement (1).docx — clause 21 (Exit Plan and Transition
    Services)'
  status: pending
  ordinal: 3
  creationDate: '2025-12-09T19:51:19.582753Z'
  completionDate: null
  editIds: []
- id: 90c3d4e3
  title: 1.3 Clarify indemnity cap
  description: 'Add to clause 19.4: ''The liability of either party under clause 17
    (Indemnities) shall be subject to the cap set out in this clause 19.4.''


    Reference: Managed services agreement (1).docx — clause 19 (Limitation of Liability)'
  status: pending
  ordinal: 4
  creationDate: '2025-12-09T19:51:25.068098Z'
  completionDate: null
  editIds: []
- id: 1370e522
  title: 1.4 Draft Security Schedule (Schedule 4)
  description: 'Create optional Security Schedule (Schedule 4) to be incorporated
    by reference in Orders that include cyber security services. Key areas:


    (a) Security standards compliance — ISO 27001 certification, Cyber Essentials
    Plus accreditation, compliance obligations.


    (b) Incident definitions — Define Incident, Known Vulnerability, Latent Vulnerability,
    Virus, and Mitigate.


    (c) Incident handling procedures — Detection, escalation, response, resolution,
    post-incident review.


    (d) Vulnerability management — Scanning, patching, remediation timelines.


    (e) Business continuity/disaster recovery — DR plan, testing, RTO/RPO commitments.


    (f) Notification obligations — Timing and content of security incident notifications
    to Customer.


    Reference: Managed services agreement (1).docx — clause 8 (Security) and Schedule
    12 (Security)'
  status: pending
  ordinal: 5
  creationDate: '2025-12-09T19:51:31.593909Z'
  completionDate: null
  editIds: []
- id: 98ff7a67
  title: 1.8 Enhance MSA core with general provisions
  description: 'Add the following general provisions to the MSA core (Schedule 1 Terms
    and Conditions) that will apply to all services.


    **TARGET DOCUMENT:** MSA (HJ7) — Schedule 1 Terms and Conditions

    **PATH:** `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\drafts\current_drafts\One2call  -
    2025 Templates  - MSA Defined Services - HJ7.docx`


    **Clause 10 (Customer Obligations) — Add new sub-clauses:**

    (a) Named contacts — Customer to provide authorised contacts with appropriate
    authority level for each Order, and notify Supplier of any changes. [Ethernet
    cl 1.7/3.2, Horizon cl 1.7/3.2]

    (b) Third-party consents — Customer responsible for obtaining all necessary consents
    (landlord, wayleave, access) for installation or service delivery at Customer
    premises; Customer bears cost of obtaining consents. [Ethernet cl 3.1, Horizon
    cl 3.1]

    (c) Health & safety — Customer to ensure Supplier staff have safe working environment;
    notify Supplier of applicable H&S rules; Supplier to comply with reasonable site
    rules. [Ethernet cl 3.3, Horizon cl 3.3]


    **Clause 11 (Charges) — Add new sub-clauses:**

    (d) Deposits & guarantees — Supplier may require deposit or parent company guarantee
    as condition of service provision; Customer agrees to enter into any agreement
    reasonably required. [Ethernet cl 7.6, Horizon cl 7.6]

    (e) Aborted visit charges — If Supplier attends site and cannot complete work
    due to Customer default (no access, site not ready, appointment broken, failure
    to prepare site), Supplier may charge standard aborted visit fee; rescheduled
    appointments subject to new lead-times. [Ethernet cl 1.13, Horizon cl 1.13]


    **WHY THESE BELONG IN MSA CORE:**

    These provisions apply to ALL installed services (not just Ethernet/Horizon) and
    are currently missing from the MSA. They represent general obligations that should
    apply across the board rather than being repeated in each Annex.


    **SOURCE DOCUMENTS:**

    • Ethernet: `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\One2Call-Terms-and-Conditions-for-Ethernet-g\One2Call-Terms-and-Conditions-for-Ethernet-g.md`

    • Horizon: `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\One2Call-Terms-and-Conditions-for-Horizon-Services-g-v1.2\One2Call-Terms-and-Conditions-for-Horizon-Services-g-v1.2.md`


    **PRECEDENT REFERENCE:** Managed services agreement (1).docx — for drafting style'
  status: pending
  ordinal: 6
  creationDate: '2025-12-09T22:04:57.278344Z'
  completionDate: null
  editIds: []
- id: a2457b5d
  title: 1.9 Complete gap analysis for remaining old terms
  description: "Complete gap analysis for remaining old terms documents against MSA\
    \ and proposed Schedule 3/Annexes structure.\n\n**COMPLETED ANALYSES:**\n✅ Ethernet\
    \ terms → Task 1.5 (Schedule 3), Task 1.8 (MSA core), Annex 3D specifics\n✅ Horizon\
    \ terms → Task 3.1 (Annex 3E)\n✅ Phone Maintenance → Task 1.6 (Schedule 5 enhancements)\n\
    ✅ Access Control Maintenance → Task 1.6 (Schedule 5 enhancements)\n✅ CCTV Maintenance\
    \ → Task 1.6 (Schedule 5 enhancements)\n✅ Sale of Goods → **RETIRED** — MSA cl\
    \ 4-8 already covers goods; see Task 0.1 (Decisions Log)\n✅ Business Communications\
    \ → **MASTER TERMS** — to be replaced by enhanced MSA\n\n**REMAINING DOCUMENTS\
    \ TO ANALYSE:**\n• Mobile terms → for new Annex 3E-Mobile (separate from Horizon\
    \ VoIP)\n  Path: `C:\\Users\\DavidSant\\effi-contract-review\\EL_Projects\\One2Call\\\
    old_terms\\One2Call-Terms-and-Conditions-for-Mobile-Services-g-v1.1\\One2Call-Terms-and-Conditions-for-Mobile-Services-g-v1.1.md`\n\
    \  **FINDING:** Mobile terms are SUPPLEMENTARY to Business Communications (see\
    \ cl 32). They have a different structure (25 clauses) covering SIM cards, handsets,\
    \ porting, roaming, network coverage — very different from Horizon VoIP. Should\
    \ be a separate Annex.\n\n**KEY STRUCTURAL FINDING:**\nOld terms hierarchy:\n\
    • **Business Communications** = Master general terms (equivalent to MSA)\n• **Supplementary\
    \ Conditions** = Ethernet, Horizon, Mobile, Maintenance (service-specific)\n•\
    \ **Sale of Goods** = Standalone (now retired — MSA covers)\n\n**For Mobile terms,\
    \ identify:**\n(a) Provisions already covered by MSA core (Schedule 1)\n(b) Provisions\
    \ that should be in Schedule 3 common framework\n(c) Mobile-specific provisions\
    \ for new Annex 3E-Mobile\n(d) Any terms that need special treatment or may conflict\
    \ with MSA\n\nReference: Markdown conversions in `C:\\Users\\DavidSant\\effi-contract-review\\\
    EL_Projects\\One2Call\\old_terms\\`"
  status: pending
  ordinal: 7
  creationDate: '2025-12-09T22:05:15.837650Z'
  completionDate: null
  editIds: []
- id: 9e3278d7
  title: 1.5 Create Schedule 3 (Installation & Provisioning) with Annexes
  description: 'Create Schedule 3: Installation & Provisioning Services as a common
    framework with detachable service-specific Annexes.


    **TARGET DOCUMENT:** MSA (HJ7)

    **PATH:** `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\drafts\current_drafts\One2call  -
    2025 Templates  - MSA Defined Services - HJ7.docx`


    **WHY THIS STRUCTURE:**

    The old terms (Ethernet, Horizon) share common installation/provisioning provisions.
    Rather than repeating these in each Annex, Schedule 3 captures the common framework.
    Service-specific details go in detachable Annexes that are selected per Order.


    **SCHEDULE 3 — COMMON PROVISIONS** (applies to all installed/provisioned services):


    1. **Site surveys** — Supplier may survey before quoting; survey findings may
    affect price/feasibility; Customer to permit access; if replacement proposal required,
    Customer has 14 days to accept or original cancelled. [Ethernet cl 1.2-1.6, Horizon
    cl 1.2-1.6]


    2. **Site preparation & amendments** — Customer responsible for preparing site
    to Supplier specification; cost of amendments borne by Customer; includes power
    supply, alternative power if temporary fails. [Ethernet cl 1.8, Horizon cl 1.8]


    3. **Installation obligations** — Supplier to install using reasonable skill and
    care; time not of the essence; timeframes are estimates only. Customer to provide
    access, power, co-operation. [Ethernet cl 1.6, Horizon cl 1.6]


    4. **Commissioning & testing** — Supplier to test installation and demonstrate
    basic functionality. [Ethernet cl 1.11, Horizon cl 1.11]


    5. **Acceptance testing** — Customer has 5 Working Days from installation to report
    material defects; if none reported, acceptance deemed; Supplier to remedy material
    non-conformities; investigation of non-existent defects chargeable. [Ethernet
    cl 2.1-2.4, Horizon cl 2.1-2.4]


    6. **Service demarcation point** — Define boundary of Supplier/Customer responsibility
    (framework; specifics in Annexes). General principle: Supplier maintains to demarcation
    point; Customer responsible beyond. [Ethernet cl 1.16, Horizon cl 1.16]


    7. **Equipment ownership & return** — Equipment remains Supplier property until
    paid in full; if monthly fee, remains Supplier property; return on termination
    at Customer cost. [Ethernet cl 1.9, Horizon cl 1.9]


    8. **Customer-supplied equipment** — Supplier not responsible for compatibility
    or performance issues with customer-provided kit; if Supplier visits due to customer-equipment
    fault, visit chargeable. [Ethernet cl 1.17, Horizon cl 1.17]


    9. **Reservation of rights** — Supplier may decline to provide Service if site
    unsuitable, distance issues, or Customer refuses excess construction charges.
    [Ethernet cl 1.10, Horizon cl 1.10]


    10. **Appointment scheduling** — Customer must agree installation appointment
    within 14 days of notification or Supplier''s preferred date applies. [Ethernet
    cl 1.14, Horizon cl 1.14]


    **ANNEXES (detachable, selected per Order):**

    • Annex 3A: Managed IT Services — remote monitoring, helpdesk, patch management
    specifics [To be drafted — Task 2.2]

    • Annex 3B: Cyber Security Services — security monitoring, incident response,
    assessment terms [To be drafted — Task 2.2]

    • Annex 3C: Cloud Management — cloud platform terms, migration, backup specifics
    [To be drafted — Task 2.2]

    • Annex 3D: Connectivity — Ethernet, Fibre, EFM, FTTC specifics; line speeds;
    broadband backup; excess construction charges; carrier dependencies; **Default
    term: 36 months / Default notice: 60 days** [Source: Ethernet terms]

    • Annex 3E: Telecoms — Horizon VoIP; Mobile services; telephone numbers; porting;
    handset terms; **Default term: 24 months / Default notice: 60 days** [Task 3.1]

    • Annex 3F: Hardware Provision & Maintenance — hardware supply; maintenance terms;
    RMAs [To be drafted after Group 2 analysis]


    **HIERARCHY:** Order Form takes precedence over Annex defaults (e.g., term and
    notice period). Statement: "In the event of conflict between the Order Form and
    any Annex, the Order Form prevails."


    **SOURCE DOCUMENTS:**

    • Ethernet: `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\One2Call-Terms-and-Conditions-for-Ethernet-g\One2Call-Terms-and-Conditions-for-Ethernet-g.md`

    • Horizon: `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\One2Call-Terms-and-Conditions-for-Horizon-Services-g-v1.2\One2Call-Terms-and-Conditions-for-Horizon-Services-g-v1.2.md`'
  status: pending
  ordinal: 8
  creationDate: '2025-12-09T19:51:38.394289Z'
  completionDate: null
  editIds: []
- id: c5de8ee8
  title: 1.6 Incorporate Maintenance Schedule (HJ1) as Schedule 5 with enhancements
  description: "Incorporate the existing Maintenance Schedule (HJ1) as Schedule 5:\
    \ Maintenance Schedule, with the following enhancements based on gap analysis\
    \ of old maintenance terms (Phone, Access Control, CCTV).\n\n**SOURCE DOCUMENT:**\
    \ Maintenance Schedule (HJ1)\n**PATH:** `C:\\Users\\DavidSant\\effi-contract-review\\\
    EL_Projects\\One2Call\\drafts\\current_drafts\\One2call  - 2025 Templates  - Maintenance\
    \ Schedule - HJ1.docx`\n\n**TARGET DOCUMENT:** MSA (HJ7)\n**PATH:** `C:\\Users\\\
    DavidSant\\effi-contract-review\\EL_Projects\\One2Call\\drafts\\current_drafts\\\
    One2call  - 2025 Templates  - MSA Defined Services - HJ7.docx`\n\n**DEFAULT SERVICE\
    \ LEVELS (add to Schedule 2 within HJ1):**\n• Response Time (>50% failure): 4\
    \ hours\n• Response Time (other faults): 8 hours\n• Business Hours: 8am-6pm Mon-Fri\
    \ (excl. bank holidays)\n• Statement: \"These defaults apply unless the Order\
    \ specifies different service levels.\"\n\n**ENHANCEMENTS TO HJ1:**\n\n**(a) Equipment-specific\
    \ exclusions (conditional clause):**\nAdd to clause 7 (Excluded Support):\n\"\
    7.3 If the Maintained Equipment includes telephone systems:\n  (a) the Maintenance\
    \ Services shall not cover 2-wire devices unless expressly stated in the Order;\
    \ and\n  (b) the default Response Time for faults other than those affecting more\
    \ than 50% of the Maintained Equipment shall be 9 hours (not 8 hours) unless otherwise\
    \ specified in the Order.\n7.4 Any other equipment-specific exclusions shall be\
    \ as set out in the relevant Order.\"\n\n**(b) Scope changes (new clause):**\n\
    Add to clause 8 (Charges):\n\"8.6 If the scope of the Maintained Equipment changes\
    \ materially from that specified in the Order (including any increase in the number\
    \ of users, devices, or software licences), the Supplier may, on reasonable written\
    \ notice, adjust the Standard Maintenance Fees to reflect the changed scope.\"\
    \n\n**(c) Early termination (new clause):**\nAdd to clause 10 (Term and termination):\n\
    \"10.2 If the Customer terminates this Schedule before the end of the Service\
    \ Initial Period or any Service Renewal Period (other than in accordance with\
    \ clause 10.1 or for Supplier breach), the Customer shall pay to the Supplier\
    \ all Standard Maintenance Fees that would have been payable for the remainder\
    \ of that period.\"\n\n**(d) Equipment destruction/theft (new clause with client\
    \ comment):**\nAdd to clause 10:\n\"10.3 If the Maintained Equipment is destroyed,\
    \ stolen, or damaged beyond repair, either party may terminate this Schedule on\
    \ 30 days' written notice, and the Customer shall pay the Standard Maintenance\
    \ Fees up to the date of termination.\"\n\n**[COMMENT FOR CLIENT]:** \"This clause\
    \ departs from your old maintenance terms, which stated that theft/destruction\
    \ of equipment would not affect the Customer's payment obligations. We have softened\
    \ this to allow either party to terminate on 30 days' notice, with fees payable\
    \ up to termination. This is a more balanced approach that avoids the Customer\
    \ being locked into paying for maintenance of equipment that no longer exists.\"\
    \n\n**NO CHANGES NEEDED FOR:**\n- Price increases: MSA cl 11.7 already covers\
    \ (pass-through + once per 12m + >10% termination right)\n- Interest on late payment:\
    \ MSA cl 14.14 already has 8% above BoE base rate\n- Liability cap: MSA cl 19.4\
    \ already has £100k cap per client instruction\n\n**OLD MAINTENANCE TERMS ANALYSED:**\n\
    • Phone: `C:\\Users\\DavidSant\\effi-contract-review\\EL_Projects\\One2Call\\\
    old_terms\\One2Call-Terms-and-Conditions-for-Phone-System-Maintenance-services-v1.1\\\
    `\n• Access Control: `C:\\Users\\DavidSant\\effi-contract-review\\EL_Projects\\\
    One2Call\\old_terms\\One2Call-Terms-Conditions-for-Access-Control-Maintenance-Services-v1.0\\\
    `\n• CCTV: `C:\\Users\\DavidSant\\effi-contract-review\\EL_Projects\\One2Call\\\
    old_terms\\One2Call-Terms-Conditions-for-CCTV-Maintenance-Services-v1.1\\`"
  status: pending
  ordinal: 9
  creationDate: '2025-12-09T19:51:44.543695Z'
  completionDate: null
  editIds: []
- id: 74ad3e5e
  title: 1.7 Add regulatory compliance clauses
  description: 'Add to clause 24 (General) with explanatory drafting notes:


    (a) Anti-bribery — Compliance with Bribery Act 2010; no bribes or facilitation
    payments; right to terminate for breach. [Note: May be required by larger clients
    and public sector customers.]


    (b) Anti-slavery — Compliance with Modern Slavery Act 2015; due diligence on supply
    chain; annual statement. [Note: May be required by larger clients and public sector
    customers.]


    (c) Dispute escalation — Before commencing litigation, disputes to be escalated
    to senior management for good faith resolution discussions for 14 days. [Note:
    May reduce legal costs and preserve commercial relationships.]


    Reference:

    • Managed services agreement (1).docx — clause 29 (Anti-bribery), clause 30 (Anti-slavery),
    clause 35 (Dispute resolution)'
  status: pending
  ordinal: 10
  creationDate: '2025-12-09T19:51:51.851235Z'
  completionDate: null
  editIds: []
- id: 575ad48e
  title: 2.1 Create Systems Integration SOW template
  description: 'Create SOW template for project-based work (migrations, infrastructure
    deployments, consultancy) based on Systems Integration Agreement precedent. Key
    areas:


    (a) Project scope and deliverables

    (b) Milestones and timeline

    (c) Acceptance testing procedures

    (d) Change control procedure

    (e) Payment milestones

    (f) Project-specific IP provisions (if bespoke work)

    (g) Go-live and handover


    Reference:

    • Systems integration agreement (pro-supplier) (1).docx — Primary reference for
    SOW structure'
  status: pending
  ordinal: 11
  creationDate: '2025-12-09T19:51:58.298663Z'
  completionDate: null
  editIds: []
- id: 6ad41cae
  title: 2.2 Complete Service Schedule detail
  description: 'Populate full detail for each Schedule 3 sub-schedule (3A-3F) including:

    • Detailed service descriptions aligned to One2Call website offerings

    • Specific SLA metrics (response times, fix times, uptime percentages)

    • Service credit calculations

    • Pricing structure frameworks

    • Standard exclusions and customer obligations


    References:

    • Managed services agreement (1).docx — Schedule 4 (Service Description), Schedule
    5 (Governance), Schedule 6 (Service Levels)

    • Software maintenance_ service level agreement.docx — SLA structure and service
    credits'
  status: pending
  ordinal: 12
  creationDate: '2025-12-09T19:52:05.354434Z'
  completionDate: null
  editIds: []
- id: 4ec1b7e1
  title: 2.3 Create Order Form template with service level options
  description: "Design Order Form template that serves as the \"front page\" of each\
    \ service engagement.\n\n**TARGET:** Create new Order Form template document\n\
    **OUTPUT PATH:** `C:\\Users\\DavidSant\\effi-contract-review\\EL_Projects\\One2Call\\\
    drafts\\current_drafts\\` (new file)\n\n**ORDER FORM CONTENTS:**\n\n1. **Parties\
    \ & Locations**\n   • Supplier: One2Call Limited\n   • Customer: [Name, address,\
    \ company number]\n   • Service location(s): [Site addresses]\n\n2. **Schedule\
    \ & Annex Selection** (checkbox approach)\n   ☐ Schedule 1: Terms and Conditions\
    \ (always applies)\n   ☐ Schedule 2: Data Protection (always applies)\n   ☐ Schedule\
    \ 3: Installation & Provisioning Services\n      ☐ Annex 3A: Managed IT Services\n\
    \      ☐ Annex 3B: Cyber Security Services\n      ☐ Annex 3C: Cloud Management\n\
    \      ☐ Annex 3D: Connectivity\n      ☐ Annex 3E: Telecoms (Horizon/VoIP)\n \
    \     ☐ Annex 3F: Hardware Provision & Maintenance\n   ☐ Schedule 4: Security\
    \ Schedule\n   ☐ Schedule 5: Maintenance Schedule\n      ☐ Equipment Maintenance\
    \ included: Yes / No\n\n3. **Commercial Terms**\n   • Charges: [Monthly fee /\
    \ One-off fee / Usage rates]\n   • Payment terms: [Override if different from\
    \ Schedule 1]\n   • Service term: [Override Annex default if different]\n   •\
    \ Notice period: [Override Annex default if different]\n\n4. **Default Term Reference\
    \ Table** (for information)\n   | Service | Default Term | Default Notice |\n\
    \   |---------|--------------|----------------|\n   | Connectivity (3D) | 36 months\
    \ | 60 days |\n   | Telecoms (3E) | 24 months | 60 days |\n   | Maintenance (Sch\
    \ 5) | 12 months | 60 days |\n   | Other | 12 months | 30 days |\n\n5. **Maintenance\
    \ Services (if Schedule 5 selected)**\n   • Maintained Equipment: [Description\
    \ / Equipment List reference]\n   • Location(s): [Site addresses]\n   \n   **Default\
    \ Service Levels** (from Schedule 5 — apply automatically):\n   • Response Time\
    \ (>50% failure): 4 hours\n   • Response Time (other faults): 8 hours (9 hours\
    \ for telephone systems)\n   • Business Hours: 8am-6pm Mon-Fri\n   \n   **Override\
    \ Service Levels** (complete only if different from defaults):\n   • Response\
    \ Time (>50% failure): ___\n   • Response Time (other faults): ___\n   • Business\
    \ Hours: ___\n   \n   **Service Credits:**\n   [ ] £50 per breach\n   [ ] 5% of\
    \ monthly fee per breach\n   [ ] 10% of monthly fee per breach\n   [ ] Custom:\
    \ ___\n   \n   **Equipment-specific exclusions:** [e.g., additional items beyond\
    \ 2-wire devices]\n\n6. **Hierarchy Statement**\n   \"In the event of conflict\
    \ between the terms of this Order and any Schedule or Annex, the terms of this\
    \ Order shall prevail.\"\n\n7. **Signatures / Electronic Acceptance**\n   • Customer\
    \ signature block\n   • Date\n   • Reference to electronic acceptance if applicable\n\
    \n**NOTE:** Default service levels are now in Schedule 5 (Task 1.6). Phone system\
    \ 9h response time is handled via conditional clause in Schedule 5 clause 7.3(b).\
    \ Order Form only needs override fields if customer wants something different.\n\
    \n**PRECEDENT REFERENCE:** MSA (HJ7) cover page for existing format"
  status: pending
  ordinal: 13
  creationDate: '2025-12-09T19:52:11.332451Z'
  completionDate: null
  editIds: []
- id: c750b02c
  title: '3.1 Draft Annex 3E: Telecoms (Horizon/VoIP)'
  description: "Draft Annex 3E for Horizon/VoIP services. Mobile services to be assessed\
    \ separately (see Task 1.9 — Mobile has different structure).\n\n**TARGET DOCUMENT:**\
    \ Create new Annex 3E within Schedule 3 framework in MSA (HJ7)\n**SOURCE DOCUMENT:**\
    \ `C:\\Users\\DavidSant\\effi-contract-review\\EL_Projects\\One2Call\\old_terms\\\
    One2Call-Terms-and-Conditions-for-Horizon-Services-g-v1.2\\One2Call-Terms-and-Conditions-for-Horizon-Services-g-v1.2.md`\n\
    \n**REGULATORY / SAFETY — PROMINENT PLACEMENT:**\n(a) Emergency services (999/112)\
    \ warning — **MAKE THIS PROMINENT AT START OF ANNEX**\nVoIP 999/112 calls do not\
    \ operate the same as PSTN fixed lines; connection may not be possible during\
    \ service outages (loss of internet connectivity); emergency services may not\
    \ be able to identify caller location/number; Customer should use alternative\
    \ line in outage. [Horizon cl 1.21]\n\n**[COMMENT FOR CLIENT]:** \"This warning\
    \ is a regulatory compliance requirement for VoIP services. Ofcom requires providers\
    \ to inform customers about the limitations of VoIP emergency calling. We have\
    \ made this prominent in Annex 3E to ensure customers are clearly informed. Failure\
    \ to provide adequate warning could expose One2Call to regulatory action and liability\
    \ claims if a customer is unable to reach emergency services during an outage.\"\
    \n\n**SERVICE FEATURES:**\n(b) User-based features — Auto attendant, hunt groups,\
    \ call park, call pickup, call queues etc; unallocated features may be recovered\
    \ by Supplier. [Horizon cl 1.25]\n(c) Music on hold — Customer responsible for\
    \ obtaining licences for uploaded music; indemnifies Supplier for failure. [Horizon\
    \ cl 3.6]\n(d) Internet portal account — Supplier provides online control portal;\
    \ reasonable endeavours to maintain 24/7 access; no liability for access restrictions.\
    \ [Horizon cl 1.19]\n(e) IP address — No IP address ownership; internet authorities\
    \ control; Supplier may change if unavailable. [Horizon cl 1.18]\n(f) Bandwidth\
    \ upgrades — Additional charges for upgrades; Supplier to advise at time of request.\
    \ [Horizon cl 1.20]\n\n**INSTALLATION:**\n(g) Third-party installer — If Customer\
    \ uses third-party installer, Customer indemnifies Supplier for direct/indirect\
    \ losses; affects Demarcation Point. [Horizon cl 1.23]\n(h) Daily sign-off — Customer\
    \ to sign off work daily during installation (not Acceptance). [Horizon cl 1.24]\n\
    \n**CUSTOMER-SUPPLIED ELEMENTS:**\n(i) Customer-supplied access — If Customer\
    \ provides own broadband/Ethernet/leased line, Customer responsible for meeting\
    \ requirements (per non-One2Call access requirements document); affects Demarcation\
    \ Point; Supplier may charge for visits caused by Customer-supplied access faults.\
    \ [Horizon cl 1.22]\n(j) Customer-supplied router — Same responsibility transfer;\
    \ affects Demarcation Point. [Horizon cl 1.17]\n\n**DEMARCATION POINTS (tiered):**\n\
    (k) Define Service Demarcation Point tiers:\n    • Main Horizon service: SBC connection\
    \ within network\n    • One2Call-supplied access + router: Customer-side port\
    \ on router\n    • Access + Installation + Equipment Maintenance: Handset\n  \
    \  • Customer-supplied access/router: Adjusted (Customer responsibility)\n[Horizon\
    \ cl 11 Definitions]\n\n**EQUIPMENT MAINTENANCE:**\n(l) If Equipment Maintenance\
    \ is included in the Order, Schedule 5 (Maintenance Schedule) shall apply to the\
    \ Maintained Equipment specified in the Order.\n\n**DEFAULT TERM & NOTICE:**\n\
    (m) Default Initial Term: **24 months** (if not specified in Order) — NOTE: Different\
    \ from Connectivity (36 months)\n(n) Auto-renewal: 12 months rolling\n(o) Default\
    \ termination notice: **60 days**\n(p) Include statement: \"These defaults may\
    \ be overridden by express terms in the Order Form\"\n\n**MANUFACTURER WARRANTY:**\n\
    (q) 30-day defect warranty for equipment [Horizon cl 6.2]\n(r) Supplier will honour\
    \ manufacturer warranty on handsets [Horizon cl 11 Definitions]\n\n**RELATIONSHIP\
    \ TO OTHER DOCUMENTS:**\n• Schedule 3 common provisions (site surveys, acceptance,\
    \ equipment ownership) apply — see Task 1.5\n• Schedule 5 (Maintenance Schedule)\
    \ applies if Equipment Maintenance selected in Order — see Task 1.6\n• Order Form\
    \ specifies whether Equipment Maintenance included — see Task 2.3"
  status: pending
  ordinal: 14
  creationDate: '2025-12-09T22:09:36.695809Z'
  completionDate: null
  editIds: []
documents:
- id: b34623a3
  filename: C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\drafts\current_drafts\One2call  -
    2025 Templates  - MSA Defined Services - HJ7.docx
  displayName: One2Call MSA (HJ7)
  addedDate: '2025-12-09T19:51:03.354901Z'
- id: febbdea1
  filename: C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\drafts\current_drafts\One2call  -
    2025 Templates  - Maintenance Schedule - HJ1.docx
  displayName: Maintenance Schedule (HJ1)
  addedDate: '2025-12-09T19:51:07.246104Z'
---

# Work Plan

## 1. 0.0 PROJECT CONTEXT (Read First)
**Status:** pending

**PROJECT CONTEXT — READ FIRST**

**Client:** One2Call Limited, Sheffield UK (Reg No: 06220567)
**Business:** Managed Service Provider (MSP) — IT support, cyber security, cloud, connectivity, telecoms, hardware
**Accreditations:** ISO 27001, ISO 9001, Cyber Essentials Plus

**Objective:** Consolidate and modernise One2Call's customer-facing contracts by:
1. Enhancing the existing MSA (HJ7) with provisions from old service-specific terms
2. Creating a modular Schedule/Annex structure that can be assembled per Order
3. Replacing 9 legacy service-specific T&Cs with the new unified structure

**Source Documents:**
• MSA (HJ7): `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\drafts\current_drafts\One2call  - 2025 Templates  - MSA Defined Services - HJ7.docx`
• Maintenance Schedule (HJ1): `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\drafts\current_drafts\One2call  - 2025 Templates  - Maintenance Schedule - HJ1.docx`
• Old terms (markdown conversions): `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\[DocumentName]\[DocumentName].md`
• Precedents: `C:\Users\DavidSant\effi-contract-review\EL_Projects\Precedents\Pro-Supplier\managed_it_services\`

**Approved Document Architecture (Option B):**
```
MSA (HJ7)
├── Cover / Order Form (commercial details, service selection, term/notice overrides)
├── Schedule 1: Terms and Conditions (core legal terms — enhance per Tasks 1.1-1.3, 1.7-1.8)
├── Schedule 2: Data Protection (existing)
├── Schedule 3: Installation & Provisioning Services (NEW — common framework)
│   ├── Annex 3A: Managed IT Services
│   ├── Annex 3B: Cyber Security Services
│   ├── Annex 3C: Cloud Management
│   ├── Annex 3D: Connectivity (Ethernet — 36m/60d defaults)
│   ├── Annex 3E: Telecoms (Horizon/VoIP — 24m/60d defaults)
│   └── Annex 3F: Hardware Provision & Maintenance
├── Schedule 4: Security Schedule (optional — for cyber services)
└── Schedule 5: Maintenance Schedule (from HJ1 — enhanced per Task 1.6)
```

**Hierarchy of Documents:**
1. Order Form (highest — overrides Annex defaults)
2. Schedule 1 (Terms and Conditions)
3. Schedule 3 + selected Annexes
4. Other Schedules

**Gap Analysis Status:**
✅ Ethernet terms → Task 1.5 (Schedule 3), Task 1.8 (MSA core), Annex 3D specifics
✅ Horizon terms → Task 3.1 (Annex 3E with prominent 999 warning + client comment)
✅ Phone Maintenance → Task 1.6 (Schedule 5 enhancements)
✅ Access Control Maintenance → Task 1.6 (Schedule 5 enhancements)
✅ CCTV Maintenance → Task 1.6 (Schedule 5 enhancements)

**Gap Analysis Remaining (Task 1.9):**
• Mobile terms — Different structure (25 clauses); may need separate treatment
• Business Comms — To be analysed
• Sale of Goods — To be analysed

**Key Decisions Made:**
• Default response times: 4h (>50% failure) / 8h (other) — in Schedule 5
• Phone system exception: 9h response time via conditional clause in Schedule 5 cl 7.3(b)
• Service credits: Menu in Order Form (£50 / 5% / 10% / custom)
• Equipment Maintenance: Indicated in Order Form; if selected, Schedule 5 applies
• 999 emergency warning: Prominent in Annex 3E (not Order Form); client comment explaining regulatory significance
• Equipment theft/destruction: Softer approach than old terms (30-day termination right); client comment explaining departure

**MSA Provisions Already Adequate (no duplication needed):**
• Price increases: MSA cl 11.7 (pass-through + once per 12m + >10% termination right)
• Interest on late payment: MSA cl 14.14 (8% above BoE base rate)
• Liability cap: MSA cl 19.4 (£100k per client instruction)

**Drafting Style:** British English per grammar.md (-ise, -our, licence/license distinction, UK date format, no Oxford comma)

**Jurisdiction:** English law, UK GDPR, EU GDPR

## 2. 0.1 Record all Decisions for Client Info
**Status:** pending

**DECISIONS LOG — For Client Advice Note**

This task captures key decisions made during the contract review and consolidation project. These should be communicated to the client in the final advice note.

---

## STRUCTURAL DECISIONS

**DECISION S1: Document Architecture (Option B)**

**Decision:** Adopt modular MSA structure with detachable Schedules and Annexes.

**Structure:**
```
MSA (HJ7)
├── Cover / Order Form (commercial details, service selection, term/notice overrides)
├── Schedule 1: Terms and Conditions (core legal terms)
├── Schedule 2: Data Protection (existing)
├── Schedule 3: Installation & Provisioning Services (NEW — common framework)
│   ├── Annex 3A: Managed IT Services
│   ├── Annex 3B: Cyber Security Services
│   ├── Annex 3C: Cloud Management
│   ├── Annex 3D: Connectivity (Ethernet — 36m/60d defaults)
│   ├── Annex 3E: Telecoms (Horizon/VoIP — 24m/60d defaults)
│   └── Annex 3F: Hardware Provision & Maintenance
├── Schedule 4: Security Schedule (optional — for cyber services)
└── Schedule 5: Maintenance Schedule (from HJ1)
```

**Hierarchy:** Order Form (highest) → Schedule 1 → Schedule 3 + Annexes → Other Schedules

**Rationale:** Provides flexibility to assemble contract per engagement while maintaining consistent core terms. Avoids repetition across service-specific documents.

---

**DECISION S2: Separate Mobile from Horizon**

**Decision:** Create separate Annex for Mobile services (not combined with Horizon VoIP in Annex 3E).

**Rationale:** Mobile terms have fundamentally different structure (25 clauses vs 11) and cover different subject matter:
- Mobile: SIM cards, handsets, porting, roaming, network coverage, MultiNet
- Horizon: VoIP, SBC, IP addresses, emergency services warning

**Impact:** May need Annex 3E-VoIP and Annex 3E-Mobile, or renumber to 3E and 3G.

---

**DECISION S3: Schedule 3 Common Framework**

**Decision:** Extract common installation/provisioning provisions from Ethernet and Horizon terms into Schedule 3 (common framework), with service-specific details in Annexes.

**Common provisions identified:**
1. Site surveys
2. Site preparation & amendments
3. Installation obligations
4. Commissioning & testing
5. Acceptance testing (5 Working Days)
6. Service demarcation point (framework)
7. Equipment ownership & return
8. Customer-supplied equipment
9. Reservation of rights
10. Appointment scheduling

**Rationale:** Avoids repetition; ensures consistency across installed services.

---

## MAINTENANCE SCHEDULE DECISIONS

**DECISION M1: Default Response Times**

**Decision:** Set defaults in Schedule 5:
- Response Time (>50% failure): 4 hours
- Response Time (other faults): 8 hours
- Business Hours: 8am-6pm Mon-Fri

**Exception:** Phone systems default to 9 hours (not 8) via conditional clause in Schedule 5 cl 7.3(b).

**Rationale:** Provides clean universal default with service-specific carve-out. Derived from Access Control/CCTV (8h) and Phone (9h) old terms.

---

**DECISION M2: Service Credits**

**Decision:** Offer menu of service credit options in Order Form (not defaults in Schedule 5):
- £50 per breach (fixed)
- 5% of monthly fee per breach
- 10% of monthly fee per breach
- Custom amount

**Rationale:** Service credits vary significantly by customer and service value. Better to select per Order than impose universal default.

---

**DECISION M3: Equipment-Specific Exclusions**

**Decision:** Use conditional clause in Schedule 5 (not separate Annexes) for equipment-specific exclusions.

**Example clause:** "If the Maintained Equipment includes telephone systems, the Maintenance Services shall not cover 2-wire devices unless expressly stated in the Order."

**Rationale:** Only one equipment-specific exclusion identified (2-wire devices for phones). Doesn't justify separate Annexes.

---

**DECISION M4: Alterations to Equipment**

**Decision:** Keep HJ1's strict approach requiring prior written approval for alterations.

**Rationale:** HJ1 approach is stricter than old terms (which allowed Customer alterations). Stricter approach protects Supplier's maintenance obligations.

---

**DECISION M5: Equipment Destruction/Theft**

**Decision:** Add softer termination right (30 days' notice) rather than old terms' approach (Customer remains liable).

**New clause:** "If the Maintained Equipment is destroyed, stolen, or damaged beyond repair, either party may terminate this Schedule on 30 days' written notice, and the Customer shall pay the Standard Maintenance Fees up to the date of termination."

**Client comment required:** "This clause departs from your old maintenance terms, which stated that theft/destruction of equipment would not affect the Customer's payment obligations. We have softened this to allow either party to terminate on 30 days' notice, with fees payable up to termination."

---

**DECISION M6: Early Termination**

**Decision:** Add early termination clause to Schedule 5 — remaining fees due if Customer terminates before end of term.

**New clause:** "If the Customer terminates this Schedule before the end of the Service Initial Period or any Service Renewal Period (other than in accordance with clause 10.1 or for Supplier breach), the Customer shall pay to the Supplier all Standard Maintenance Fees that would have been payable for the remainder of that period."

---

**DECISION M7: Scope Changes**

**Decision:** Add scope change clause to Schedule 5 — Supplier may adjust fees if maintained equipment changes materially.

**New clause:** "If the scope of the Maintained Equipment changes materially from that specified in the Order (including any increase in the number of users, devices, or software licences), the Supplier may, on reasonable written notice, adjust the Standard Maintenance Fees to reflect the changed scope."

---

## MSA CORE DECISIONS

**DECISION C1: Price Increases — No Change Needed**

**Decision:** MSA cl 11.7 already covers price increases adequately.

**Existing provision:**
- Pass-through of supplier increases: any time, 30 days notice
- General inflationary increases: once per 12 months
- Customer termination right: if single increase >10%, Customer can terminate within 14 days

**Rationale:** Better than old maintenance terms which had no termination right.

---

**DECISION C2: Interest on Late Payment — No Change Needed**

**Decision:** MSA cl 14.14 already covers interest (8% above BoE base rate).

**Rationale:** Actually higher than old terms (which had 4% in some documents, 5% in others).

---

**DECISION C3: Liability Cap — No Change Needed**

**Decision:** MSA cl 19.4 already has £100,000 liability cap per client instruction.

**Rationale:** Client has already made commercial decision on cap level.

---

## ANNEX 3E (HORIZON/VoIP) DECISIONS

**DECISION V1: Emergency Services Warning Placement**

**Decision:** Place 999/112 warning prominently at START of Annex 3E (not in Order Form).

**Rationale:** Regulatory compliance requirement (Ofcom). Prominent placement in Annex ensures customers are clearly informed when they select VoIP services.

**Client comment required:** "This warning is a regulatory compliance requirement for VoIP services. Ofcom requires providers to inform customers about the limitations of VoIP emergency calling. Failure to provide adequate warning could expose One2Call to regulatory action and liability claims."

---

**DECISION V2: Equipment Maintenance via Order Form**

**Decision:** Equipment Maintenance indicated in Order Form. If selected, Schedule 5 (Maintenance Schedule) applies to the Maintained Equipment specified.

**Rationale:** Clean separation — Order Form selects services; Schedule 5 contains maintenance terms.

---

## RETIREMENT DECISIONS

**DECISION R1: Retire Standalone Sale of Goods Terms**

**Decision:** Retire the standalone "Terms & Conditions for the Sale of Goods" document.

**Rationale:** The MSA (HJ7) already contains comprehensive goods provisions at clauses 4-8:
• Cl 4: Goods Specification
• Cl 5: Delivery (notes, location, late/short delivery, instalments)
• Cl 6: Acceptance (48-hour deemed acceptance, 5-day defect notification)
• Cl 7: Quality/Warranty (description conformity, repair/replace/refund, UCTA exclusions)
• Cl 8: Title and Risk (risk on delivery, title on payment, retention provisions)

**Impact:** For pure product sales with no ongoing services, One2Call should use the MSA with an Order that specifies Goods only.

**Old Document Path:** `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\One2Call-Terms-and-Conditions-for-the-Sale-of-Goods\`

---

**DECISION R2: Retire Business Communications General Terms**

**Decision:** The Business Communications General Terms will be replaced by the enhanced MSA (HJ7).

**Rationale:** Business Communications is the current "master" document. The MSA will assume this role with improved provisions and modular structure.

**Old Document Path:** `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\One2Call-Business-Communications-General-Terms-and-Conditions.pdf\`

---

*Additional decisions to be added as they are made during this project.*

## 3. 1.1 Fix critical drafting issues
**Status:** pending

(a) Correct Schedule numbering — The Terms and Conditions are headed "Schedule 2" but should be "Schedule 1" per the cover document structure. Correct this inconsistency.

(b) Add "Data Protection Legislation" definition — This term is used in clause 18.1 but not defined. Add definition to clause 1 referencing UK GDPR and EU GDPR.

Reference: Managed services agreement (1).docx

## 4. 1.2 Expand clause 21 (exit/transition)
**Status:** pending

Add exit/transition provisions covering:

(a) Customer data extraction right — Customer may request return or deletion of Customer Data within 30 days of termination.

(b) Transition assistance — Supplier to provide reasonable transition assistance for up to 3 months at Supplier's then-current rates.

(c) Data deletion certification — Following data return, Supplier to confirm deletion of Customer Data (subject to legal retention requirements).

(d) Equipment — Customer equipment to be returned; Supplier equipment to be collected or purchased at net book value.

Reference: Managed services agreement (1).docx — clause 21 (Exit Plan and Transition Services)

## 5. 1.3 Clarify indemnity cap
**Status:** pending

Add to clause 19.4: 'The liability of either party under clause 17 (Indemnities) shall be subject to the cap set out in this clause 19.4.'

Reference: Managed services agreement (1).docx — clause 19 (Limitation of Liability)

## 6. 1.4 Draft Security Schedule (Schedule 4)
**Status:** pending

Create optional Security Schedule (Schedule 4) to be incorporated by reference in Orders that include cyber security services. Key areas:

(a) Security standards compliance — ISO 27001 certification, Cyber Essentials Plus accreditation, compliance obligations.

(b) Incident definitions — Define Incident, Known Vulnerability, Latent Vulnerability, Virus, and Mitigate.

(c) Incident handling procedures — Detection, escalation, response, resolution, post-incident review.

(d) Vulnerability management — Scanning, patching, remediation timelines.

(e) Business continuity/disaster recovery — DR plan, testing, RTO/RPO commitments.

(f) Notification obligations — Timing and content of security incident notifications to Customer.

Reference: Managed services agreement (1).docx — clause 8 (Security) and Schedule 12 (Security)

## 7. 1.8 Enhance MSA core with general provisions
**Status:** pending

Add the following general provisions to the MSA core (Schedule 1 Terms and Conditions) that will apply to all services.

**TARGET DOCUMENT:** MSA (HJ7) — Schedule 1 Terms and Conditions
**PATH:** `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\drafts\current_drafts\One2call  - 2025 Templates  - MSA Defined Services - HJ7.docx`

**Clause 10 (Customer Obligations) — Add new sub-clauses:**
(a) Named contacts — Customer to provide authorised contacts with appropriate authority level for each Order, and notify Supplier of any changes. [Ethernet cl 1.7/3.2, Horizon cl 1.7/3.2]
(b) Third-party consents — Customer responsible for obtaining all necessary consents (landlord, wayleave, access) for installation or service delivery at Customer premises; Customer bears cost of obtaining consents. [Ethernet cl 3.1, Horizon cl 3.1]
(c) Health & safety — Customer to ensure Supplier staff have safe working environment; notify Supplier of applicable H&S rules; Supplier to comply with reasonable site rules. [Ethernet cl 3.3, Horizon cl 3.3]

**Clause 11 (Charges) — Add new sub-clauses:**
(d) Deposits & guarantees — Supplier may require deposit or parent company guarantee as condition of service provision; Customer agrees to enter into any agreement reasonably required. [Ethernet cl 7.6, Horizon cl 7.6]
(e) Aborted visit charges — If Supplier attends site and cannot complete work due to Customer default (no access, site not ready, appointment broken, failure to prepare site), Supplier may charge standard aborted visit fee; rescheduled appointments subject to new lead-times. [Ethernet cl 1.13, Horizon cl 1.13]

**WHY THESE BELONG IN MSA CORE:**
These provisions apply to ALL installed services (not just Ethernet/Horizon) and are currently missing from the MSA. They represent general obligations that should apply across the board rather than being repeated in each Annex.

**SOURCE DOCUMENTS:**
• Ethernet: `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\One2Call-Terms-and-Conditions-for-Ethernet-g\One2Call-Terms-and-Conditions-for-Ethernet-g.md`
• Horizon: `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\One2Call-Terms-and-Conditions-for-Horizon-Services-g-v1.2\One2Call-Terms-and-Conditions-for-Horizon-Services-g-v1.2.md`

**PRECEDENT REFERENCE:** Managed services agreement (1).docx — for drafting style

## 8. 1.9 Complete gap analysis for remaining old terms
**Status:** pending

Complete gap analysis for remaining old terms documents against MSA and proposed Schedule 3/Annexes structure.

**COMPLETED ANALYSES:**
✅ Ethernet terms → Task 1.5 (Schedule 3), Task 1.8 (MSA core), Annex 3D specifics
✅ Horizon terms → Task 3.1 (Annex 3E)
✅ Phone Maintenance → Task 1.6 (Schedule 5 enhancements)
✅ Access Control Maintenance → Task 1.6 (Schedule 5 enhancements)
✅ CCTV Maintenance → Task 1.6 (Schedule 5 enhancements)
✅ Sale of Goods → **RETIRED** — MSA cl 4-8 already covers goods; see Task 0.1 (Decisions Log)
✅ Business Communications → **MASTER TERMS** — to be replaced by enhanced MSA

**REMAINING DOCUMENTS TO ANALYSE:**
• Mobile terms → for new Annex 3E-Mobile (separate from Horizon VoIP)
  Path: `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\One2Call-Terms-and-Conditions-for-Mobile-Services-g-v1.1\One2Call-Terms-and-Conditions-for-Mobile-Services-g-v1.1.md`
  **FINDING:** Mobile terms are SUPPLEMENTARY to Business Communications (see cl 32). They have a different structure (25 clauses) covering SIM cards, handsets, porting, roaming, network coverage — very different from Horizon VoIP. Should be a separate Annex.

**KEY STRUCTURAL FINDING:**
Old terms hierarchy:
• **Business Communications** = Master general terms (equivalent to MSA)
• **Supplementary Conditions** = Ethernet, Horizon, Mobile, Maintenance (service-specific)
• **Sale of Goods** = Standalone (now retired — MSA covers)

**For Mobile terms, identify:**
(a) Provisions already covered by MSA core (Schedule 1)
(b) Provisions that should be in Schedule 3 common framework
(c) Mobile-specific provisions for new Annex 3E-Mobile
(d) Any terms that need special treatment or may conflict with MSA

Reference: Markdown conversions in `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\`

## 9. 1.5 Create Schedule 3 (Installation & Provisioning) with Annexes
**Status:** pending

Create Schedule 3: Installation & Provisioning Services as a common framework with detachable service-specific Annexes.

**TARGET DOCUMENT:** MSA (HJ7)
**PATH:** `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\drafts\current_drafts\One2call  - 2025 Templates  - MSA Defined Services - HJ7.docx`

**WHY THIS STRUCTURE:**
The old terms (Ethernet, Horizon) share common installation/provisioning provisions. Rather than repeating these in each Annex, Schedule 3 captures the common framework. Service-specific details go in detachable Annexes that are selected per Order.

**SCHEDULE 3 — COMMON PROVISIONS** (applies to all installed/provisioned services):

1. **Site surveys** — Supplier may survey before quoting; survey findings may affect price/feasibility; Customer to permit access; if replacement proposal required, Customer has 14 days to accept or original cancelled. [Ethernet cl 1.2-1.6, Horizon cl 1.2-1.6]

2. **Site preparation & amendments** — Customer responsible for preparing site to Supplier specification; cost of amendments borne by Customer; includes power supply, alternative power if temporary fails. [Ethernet cl 1.8, Horizon cl 1.8]

3. **Installation obligations** — Supplier to install using reasonable skill and care; time not of the essence; timeframes are estimates only. Customer to provide access, power, co-operation. [Ethernet cl 1.6, Horizon cl 1.6]

4. **Commissioning & testing** — Supplier to test installation and demonstrate basic functionality. [Ethernet cl 1.11, Horizon cl 1.11]

5. **Acceptance testing** — Customer has 5 Working Days from installation to report material defects; if none reported, acceptance deemed; Supplier to remedy material non-conformities; investigation of non-existent defects chargeable. [Ethernet cl 2.1-2.4, Horizon cl 2.1-2.4]

6. **Service demarcation point** — Define boundary of Supplier/Customer responsibility (framework; specifics in Annexes). General principle: Supplier maintains to demarcation point; Customer responsible beyond. [Ethernet cl 1.16, Horizon cl 1.16]

7. **Equipment ownership & return** — Equipment remains Supplier property until paid in full; if monthly fee, remains Supplier property; return on termination at Customer cost. [Ethernet cl 1.9, Horizon cl 1.9]

8. **Customer-supplied equipment** — Supplier not responsible for compatibility or performance issues with customer-provided kit; if Supplier visits due to customer-equipment fault, visit chargeable. [Ethernet cl 1.17, Horizon cl 1.17]

9. **Reservation of rights** — Supplier may decline to provide Service if site unsuitable, distance issues, or Customer refuses excess construction charges. [Ethernet cl 1.10, Horizon cl 1.10]

10. **Appointment scheduling** — Customer must agree installation appointment within 14 days of notification or Supplier's preferred date applies. [Ethernet cl 1.14, Horizon cl 1.14]

**ANNEXES (detachable, selected per Order):**
• Annex 3A: Managed IT Services — remote monitoring, helpdesk, patch management specifics [To be drafted — Task 2.2]
• Annex 3B: Cyber Security Services — security monitoring, incident response, assessment terms [To be drafted — Task 2.2]
• Annex 3C: Cloud Management — cloud platform terms, migration, backup specifics [To be drafted — Task 2.2]
• Annex 3D: Connectivity — Ethernet, Fibre, EFM, FTTC specifics; line speeds; broadband backup; excess construction charges; carrier dependencies; **Default term: 36 months / Default notice: 60 days** [Source: Ethernet terms]
• Annex 3E: Telecoms — Horizon VoIP; Mobile services; telephone numbers; porting; handset terms; **Default term: 24 months / Default notice: 60 days** [Task 3.1]
• Annex 3F: Hardware Provision & Maintenance — hardware supply; maintenance terms; RMAs [To be drafted after Group 2 analysis]

**HIERARCHY:** Order Form takes precedence over Annex defaults (e.g., term and notice period). Statement: "In the event of conflict between the Order Form and any Annex, the Order Form prevails."

**SOURCE DOCUMENTS:**
• Ethernet: `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\One2Call-Terms-and-Conditions-for-Ethernet-g\One2Call-Terms-and-Conditions-for-Ethernet-g.md`
• Horizon: `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\One2Call-Terms-and-Conditions-for-Horizon-Services-g-v1.2\One2Call-Terms-and-Conditions-for-Horizon-Services-g-v1.2.md`

## 10. 1.6 Incorporate Maintenance Schedule (HJ1) as Schedule 5 with enhancements
**Status:** pending

Incorporate the existing Maintenance Schedule (HJ1) as Schedule 5: Maintenance Schedule, with the following enhancements based on gap analysis of old maintenance terms (Phone, Access Control, CCTV).

**SOURCE DOCUMENT:** Maintenance Schedule (HJ1)
**PATH:** `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\drafts\current_drafts\One2call  - 2025 Templates  - Maintenance Schedule - HJ1.docx`

**TARGET DOCUMENT:** MSA (HJ7)
**PATH:** `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\drafts\current_drafts\One2call  - 2025 Templates  - MSA Defined Services - HJ7.docx`

**DEFAULT SERVICE LEVELS (add to Schedule 2 within HJ1):**
• Response Time (>50% failure): 4 hours
• Response Time (other faults): 8 hours
• Business Hours: 8am-6pm Mon-Fri (excl. bank holidays)
• Statement: "These defaults apply unless the Order specifies different service levels."

**ENHANCEMENTS TO HJ1:**

**(a) Equipment-specific exclusions (conditional clause):**
Add to clause 7 (Excluded Support):
"7.3 If the Maintained Equipment includes telephone systems:
  (a) the Maintenance Services shall not cover 2-wire devices unless expressly stated in the Order; and
  (b) the default Response Time for faults other than those affecting more than 50% of the Maintained Equipment shall be 9 hours (not 8 hours) unless otherwise specified in the Order.
7.4 Any other equipment-specific exclusions shall be as set out in the relevant Order."

**(b) Scope changes (new clause):**
Add to clause 8 (Charges):
"8.6 If the scope of the Maintained Equipment changes materially from that specified in the Order (including any increase in the number of users, devices, or software licences), the Supplier may, on reasonable written notice, adjust the Standard Maintenance Fees to reflect the changed scope."

**(c) Early termination (new clause):**
Add to clause 10 (Term and termination):
"10.2 If the Customer terminates this Schedule before the end of the Service Initial Period or any Service Renewal Period (other than in accordance with clause 10.1 or for Supplier breach), the Customer shall pay to the Supplier all Standard Maintenance Fees that would have been payable for the remainder of that period."

**(d) Equipment destruction/theft (new clause with client comment):**
Add to clause 10:
"10.3 If the Maintained Equipment is destroyed, stolen, or damaged beyond repair, either party may terminate this Schedule on 30 days' written notice, and the Customer shall pay the Standard Maintenance Fees up to the date of termination."

**[COMMENT FOR CLIENT]:** "This clause departs from your old maintenance terms, which stated that theft/destruction of equipment would not affect the Customer's payment obligations. We have softened this to allow either party to terminate on 30 days' notice, with fees payable up to termination. This is a more balanced approach that avoids the Customer being locked into paying for maintenance of equipment that no longer exists."

**NO CHANGES NEEDED FOR:**
- Price increases: MSA cl 11.7 already covers (pass-through + once per 12m + >10% termination right)
- Interest on late payment: MSA cl 14.14 already has 8% above BoE base rate
- Liability cap: MSA cl 19.4 already has £100k cap per client instruction

**OLD MAINTENANCE TERMS ANALYSED:**
• Phone: `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\One2Call-Terms-and-Conditions-for-Phone-System-Maintenance-services-v1.1\`
• Access Control: `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\One2Call-Terms-Conditions-for-Access-Control-Maintenance-Services-v1.0\`
• CCTV: `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\One2Call-Terms-Conditions-for-CCTV-Maintenance-Services-v1.1\`

## 11. 1.7 Add regulatory compliance clauses
**Status:** pending

Add to clause 24 (General) with explanatory drafting notes:

(a) Anti-bribery — Compliance with Bribery Act 2010; no bribes or facilitation payments; right to terminate for breach. [Note: May be required by larger clients and public sector customers.]

(b) Anti-slavery — Compliance with Modern Slavery Act 2015; due diligence on supply chain; annual statement. [Note: May be required by larger clients and public sector customers.]

(c) Dispute escalation — Before commencing litigation, disputes to be escalated to senior management for good faith resolution discussions for 14 days. [Note: May reduce legal costs and preserve commercial relationships.]

Reference:
• Managed services agreement (1).docx — clause 29 (Anti-bribery), clause 30 (Anti-slavery), clause 35 (Dispute resolution)

## 12. 2.1 Create Systems Integration SOW template
**Status:** pending

Create SOW template for project-based work (migrations, infrastructure deployments, consultancy) based on Systems Integration Agreement precedent. Key areas:

(a) Project scope and deliverables
(b) Milestones and timeline
(c) Acceptance testing procedures
(d) Change control procedure
(e) Payment milestones
(f) Project-specific IP provisions (if bespoke work)
(g) Go-live and handover

Reference:
• Systems integration agreement (pro-supplier) (1).docx — Primary reference for SOW structure

## 13. 2.2 Complete Service Schedule detail
**Status:** pending

Populate full detail for each Schedule 3 sub-schedule (3A-3F) including:
• Detailed service descriptions aligned to One2Call website offerings
• Specific SLA metrics (response times, fix times, uptime percentages)
• Service credit calculations
• Pricing structure frameworks
• Standard exclusions and customer obligations

References:
• Managed services agreement (1).docx — Schedule 4 (Service Description), Schedule 5 (Governance), Schedule 6 (Service Levels)
• Software maintenance_ service level agreement.docx — SLA structure and service credits

## 14. 2.3 Create Order Form template with service level options
**Status:** pending

Design Order Form template that serves as the "front page" of each service engagement.

**TARGET:** Create new Order Form template document
**OUTPUT PATH:** `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\drafts\current_drafts\` (new file)

**ORDER FORM CONTENTS:**

1. **Parties & Locations**
   • Supplier: One2Call Limited
   • Customer: [Name, address, company number]
   • Service location(s): [Site addresses]

2. **Schedule & Annex Selection** (checkbox approach)
   ☐ Schedule 1: Terms and Conditions (always applies)
   ☐ Schedule 2: Data Protection (always applies)
   ☐ Schedule 3: Installation & Provisioning Services
      ☐ Annex 3A: Managed IT Services
      ☐ Annex 3B: Cyber Security Services
      ☐ Annex 3C: Cloud Management
      ☐ Annex 3D: Connectivity
      ☐ Annex 3E: Telecoms (Horizon/VoIP)
      ☐ Annex 3F: Hardware Provision & Maintenance
   ☐ Schedule 4: Security Schedule
   ☐ Schedule 5: Maintenance Schedule
      ☐ Equipment Maintenance included: Yes / No

3. **Commercial Terms**
   • Charges: [Monthly fee / One-off fee / Usage rates]
   • Payment terms: [Override if different from Schedule 1]
   • Service term: [Override Annex default if different]
   • Notice period: [Override Annex default if different]

4. **Default Term Reference Table** (for information)
   | Service | Default Term | Default Notice |
   |---------|--------------|----------------|
   | Connectivity (3D) | 36 months | 60 days |
   | Telecoms (3E) | 24 months | 60 days |
   | Maintenance (Sch 5) | 12 months | 60 days |
   | Other | 12 months | 30 days |

5. **Maintenance Services (if Schedule 5 selected)**
   • Maintained Equipment: [Description / Equipment List reference]
   • Location(s): [Site addresses]
   
   **Default Service Levels** (from Schedule 5 — apply automatically):
   • Response Time (>50% failure): 4 hours
   • Response Time (other faults): 8 hours (9 hours for telephone systems)
   • Business Hours: 8am-6pm Mon-Fri
   
   **Override Service Levels** (complete only if different from defaults):
   • Response Time (>50% failure): ___
   • Response Time (other faults): ___
   • Business Hours: ___
   
   **Service Credits:**
   [ ] £50 per breach
   [ ] 5% of monthly fee per breach
   [ ] 10% of monthly fee per breach
   [ ] Custom: ___
   
   **Equipment-specific exclusions:** [e.g., additional items beyond 2-wire devices]

6. **Hierarchy Statement**
   "In the event of conflict between the terms of this Order and any Schedule or Annex, the terms of this Order shall prevail."

7. **Signatures / Electronic Acceptance**
   • Customer signature block
   • Date
   • Reference to electronic acceptance if applicable

**NOTE:** Default service levels are now in Schedule 5 (Task 1.6). Phone system 9h response time is handled via conditional clause in Schedule 5 clause 7.3(b). Order Form only needs override fields if customer wants something different.

**PRECEDENT REFERENCE:** MSA (HJ7) cover page for existing format

## 15. 3.1 Draft Annex 3E: Telecoms (Horizon/VoIP)
**Status:** pending

Draft Annex 3E for Horizon/VoIP services. Mobile services to be assessed separately (see Task 1.9 — Mobile has different structure).

**TARGET DOCUMENT:** Create new Annex 3E within Schedule 3 framework in MSA (HJ7)
**SOURCE DOCUMENT:** `C:\Users\DavidSant\effi-contract-review\EL_Projects\One2Call\old_terms\One2Call-Terms-and-Conditions-for-Horizon-Services-g-v1.2\One2Call-Terms-and-Conditions-for-Horizon-Services-g-v1.2.md`

**REGULATORY / SAFETY — PROMINENT PLACEMENT:**
(a) Emergency services (999/112) warning — **MAKE THIS PROMINENT AT START OF ANNEX**
VoIP 999/112 calls do not operate the same as PSTN fixed lines; connection may not be possible during service outages (loss of internet connectivity); emergency services may not be able to identify caller location/number; Customer should use alternative line in outage. [Horizon cl 1.21]

**[COMMENT FOR CLIENT]:** "This warning is a regulatory compliance requirement for VoIP services. Ofcom requires providers to inform customers about the limitations of VoIP emergency calling. We have made this prominent in Annex 3E to ensure customers are clearly informed. Failure to provide adequate warning could expose One2Call to regulatory action and liability claims if a customer is unable to reach emergency services during an outage."

**SERVICE FEATURES:**
(b) User-based features — Auto attendant, hunt groups, call park, call pickup, call queues etc; unallocated features may be recovered by Supplier. [Horizon cl 1.25]
(c) Music on hold — Customer responsible for obtaining licences for uploaded music; indemnifies Supplier for failure. [Horizon cl 3.6]
(d) Internet portal account — Supplier provides online control portal; reasonable endeavours to maintain 24/7 access; no liability for access restrictions. [Horizon cl 1.19]
(e) IP address — No IP address ownership; internet authorities control; Supplier may change if unavailable. [Horizon cl 1.18]
(f) Bandwidth upgrades — Additional charges for upgrades; Supplier to advise at time of request. [Horizon cl 1.20]

**INSTALLATION:**
(g) Third-party installer — If Customer uses third-party installer, Customer indemnifies Supplier for direct/indirect losses; affects Demarcation Point. [Horizon cl 1.23]
(h) Daily sign-off — Customer to sign off work daily during installation (not Acceptance). [Horizon cl 1.24]

**CUSTOMER-SUPPLIED ELEMENTS:**
(i) Customer-supplied access — If Customer provides own broadband/Ethernet/leased line, Customer responsible for meeting requirements (per non-One2Call access requirements document); affects Demarcation Point; Supplier may charge for visits caused by Customer-supplied access faults. [Horizon cl 1.22]
(j) Customer-supplied router — Same responsibility transfer; affects Demarcation Point. [Horizon cl 1.17]

**DEMARCATION POINTS (tiered):**
(k) Define Service Demarcation Point tiers:
    • Main Horizon service: SBC connection within network
    • One2Call-supplied access + router: Customer-side port on router
    • Access + Installation + Equipment Maintenance: Handset
    • Customer-supplied access/router: Adjusted (Customer responsibility)
[Horizon cl 11 Definitions]

**EQUIPMENT MAINTENANCE:**
(l) If Equipment Maintenance is included in the Order, Schedule 5 (Maintenance Schedule) shall apply to the Maintained Equipment specified in the Order.

**DEFAULT TERM & NOTICE:**
(m) Default Initial Term: **24 months** (if not specified in Order) — NOTE: Different from Connectivity (36 months)
(n) Auto-renewal: 12 months rolling
(o) Default termination notice: **60 days**
(p) Include statement: "These defaults may be overridden by express terms in the Order Form"

**MANUFACTURER WARRANTY:**
(q) 30-day defect warranty for equipment [Horizon cl 6.2]
(r) Supplier will honour manufacturer warranty on handsets [Horizon cl 11 Definitions]

**RELATIONSHIP TO OTHER DOCUMENTS:**
• Schedule 3 common provisions (site surveys, acceptance, equipment ownership) apply — see Task 1.5
• Schedule 5 (Maintenance Schedule) applies if Equipment Maintenance selected in Order — see Task 1.6
• Order Form specifies whether Equipment Maintenance included — see Task 2.3
