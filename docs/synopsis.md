# **🧾 Project Synopsis — *Effi-Local Local Document Editor***

## WARNING - this md file is from an earlier iteration and might not be 100% accurate ##

## **1\. Overview**



**Effi-Local is a local Python application that edits Microsoft Word (`.docx`) documents in collaboration with an LLM via the OpenAI API.**  

 **It runs entirely on the user’s computer and talks to the internet only for model inference**



**The design emphasizes:**



* **Local-first processing (privacy & determinism)**



* **Structured JSON representations of Word documents**



* **LLM reasoning via well-defined JSON schemas**



* **Safe, reversible edits via structured tool contracts**



* **Persistent UUID-based identities embedded in the `.docx` using paragraph tags (`w:pPr/w:tag`)**



* **Durable range tagging with overlapping spans using paired start/end markers**



  ---



  ## **2\. Core architecture**



  ### **A. Document Representation**



**Each `.docx` file is parsed into structured JSON artifacts:**





* **`raw.docx`**



* **`blocks.jsonl` - one block (paragraph, heading, list item, table cell, image caption) per line, each with a carrier UUID, a content hash fingerprint, type, style, text, and optional anchors/metadata.**



* **`sections.json` — heading-derived tree referencing block UUIDs.**



* **`styles.json` — discovered styles and usage counts.**



* **`tag_ranges.jsonl` — newline-JSON of arbitrary spans across the document, each defined by a start\_marker\_id and end\_marker\_id (both UUIDs), a `label` (e.g., “liability”, “warranty”), optional attributes, and repair anchors. One special “block” tag range is auto-generated per block spanning exactly that block’s text; it lets us detect later splits/merges.**



* **`index.json` — counts and a `filemap` to all artifacts (`blocks`, `sections`, `styles`, optional `tag_ranges`).**



* **`manifest.json` — version, checksums, and carrier configuration:**



  * **`uuid_carrier`: where block UUIDs are written (`paragraph-tags` | `comments` | `bookmarks`)**



  * **`range_marker_carrier`: where range markers are written (same enum)**



  * **`range_marker_tag_prefix`: prefix used in marker tags (e.g., `"marker:"`)**



**JSON is the *canonical* source of truth for reasoning and edits; `.docx` is an export target and import source.**



### **B. Persistent UUIDs in Word**



* **Each block gets a UUID (`uuid4`) and is rendered with that UUID persisted in Word using paragraph properties: `<w:p><w:pPr><w:tag w:val="effi:block:<uuid>"/></w:pPr>...</w:p>`.**



* **Range tags use paired point markers (start/end) for arbitrary spans. Block UUIDs stored in paragraph tags don't interfere with `doc.paragraphs` iteration.**



* **On re-parse, identities are recovered from these carriers; if a carrier is missing, the system falls back to text/neighbor anchors and the stored content hash to gauge drift.**



**Block splits/merges:**



* **If a user splits a paragraph in Word, the original block keeps its UUID and a new block (new UUID) appears.**



* **The per-block “block” tag range reveals splits/merges: if its start/end markers land in different blocks after re-parse, we record a split; for merges, the reverse.**



  ### **C. Edit**




4. **Render new `.docx` (write block UUID paragraph tags; insert/update range markers).**



5. **Re-parse the rendered `.docx`; reconcile primarily by UUIDs, falling back to anchors if needed.**



6. **Commit new JSON and bump `manifest.v` if reconciliation passes; otherwise surface a drift report (and do not promote).**



**All changes are schema-validated; operations are dry-run by default and reversible.**



---



## **3\. Security and locality**



* **No inbound exposure: all local processes; only outbound HTTPS to LLM.**



* **Only outbound HTTPS to LLM via VSCode as the LLM client and MCP client.**



* **`manifest.json` checksums detect external modifications to `.docx`.**



* **`raw.docx` is read-only; new versions are generated from JSON.**



  ---





  ---



  ## **5\. Future extensions**



* **Local semantic search / embeddings.**



* **Multi-document context with a manifest registry.**



* **Fine-grained diff viewer (JSON-to-JSON and text-aware).**



* **Multi-agent editing (topic-scoped subplans).**



* **Exportable audit logs.**



  ---



**In summary:**  

**Effi-Local converts `.docx` into a durable, UUID-anchored JSON corpus. Block identities are embedded in Word paragraphs via `w:tag` elements; arbitrary, overlapping spans use paired start/end markers. The LLM reasons on JSON, proposes structured edit/tag plans, and the system re-applies them deterministically with reconciliation and versioning—ready for future MCP hosting but fully operable today via Responses API tool-calling.**



* 



