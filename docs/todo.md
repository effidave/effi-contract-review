### IDEAS
AGENTS.md to explain the skills
- UK qualified lawyer etc.
- here are the tools
- here is how precedents work [including drafting notes]
- if acting for customer
- if acting for supplier

template project dir with the structure needed

ability to create a new project through the app

Q&A chat to understand and create 
- a context file for the client
- a context file for the instruction

Q&A chat to identify an appropriate precedent
- for now user will manually put this into the right place
- in the future the app will access a precedent bank
- and provide an opportunity for user to upload new precedent
- and provide a context file for each precedent

auto-git the artifacts 'with a useful message'
update the artifacts on each change - but how to preserve the uuids?
create an md file based on the blocks on each change - and use this as the context alongside all other contexts

generate paraId for new blocks:
Random rnd = new();
int idNum = rnd.Next(1, int.MaxValue);
string newId = idNum.ToString("X8");
[but also check for collisions with existing paraIds]

make sure track changes is rendering deleted text


Have the LLM watch what I am advising, and have a go at guessing which legal issue I am dealing with, and add suggestions for how I might deal with it / points I may want to keep in mind / alternate options / autopilot etc.

Use company names to lookup what their products/services/sectors are - and their turnover?  And use that to guess at the concerns of each party (e.g. WF concerned about cashflow, liability and termination vs Elavon concerned about regulatory compliance)

LLM to use brief deal context yaml generate a chat script to help set up the context window for the LLM

Clause titles not resolving for comments in the same way as for tracked edits?

3.4	Subcontractors/Vendor Personnel.  - not being recognised as a clause title
5.0	FEES & PAYMENT.  - not being recognised as a clause title
8.0	 DATA SECURITY. - not being recognised as a clause title
9.0	REPRESENTATIONS, WARRANTIES AND COVENANTS.  - not being recognised as a clause title

For comments, display whole para text rather than referenced text

We have lost this:
# Tracked Changes

This section contains examples of contract edits made by this lawyer, extracted from Word's Track Changes.
Each edit shows a paragraph that was modified, with:

- **Before**: The original text from the counterparty's draft
- **After**: The revised text after the lawyer's edits
- **Changes**: A summary of specific deletions and insertions
- **Rationale**: The lawyer's comments explaining their reasoning (when available)

These examples illustrate this particular lawyer's negotiation style and preferences.
You may use these as a reference when assisting this user with similar contract reviews.

---

Do the comments under the edits, with "Rationale"


## Edits to clause 10: "DATA SECURITY"

### Original clause
> DATA SECURITY. [SUPPLIER] shall comply with Exhibit 3 to this Trial.  [SUPPLIER] shall not process personal data or personal information (as such terms are defined under Applicable Law).

### Changes
**Before:** ... shall comply with Exhibit 3 to this Trial.  [SUPPLIER] shall ...
**After:** ... shall comply with clauses 6 (Data Retention and Descruction), 8 (Cyber Security Incidents) and 9 (Application and Software Requirements) of Exhibit 3 to this Trial.  Other than those specific clauses, Exhibit 3 shall not apply.  [SUPPLIER] shall ...

### Rationale
> For [SUPPLIER]: I have chosen these clauses from Exhibit 3 which probably map onto your existing processes.

> For [CUSTOMER]: see clause 10 for a list of clauses which look relevant


If there are no edits

## Comments on clause 10: "DATA SECURITY"

### Clause text
> DATA SECURITY. [SUPPLIER] shall comply with Exhibit 3 to this Trial.  [SUPPLIER] shall not process personal data or personal information (as such terms are defined under Applicable Law).

### Comments
> For [SUPPLIER]: I think we should ask for more information about this clause.

> For [CUSTOMER]: what is the purpose of this?
