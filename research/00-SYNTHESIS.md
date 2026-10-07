# Research Synthesis: Government Document Management & Intelligent Knowledge Retrieval

**Prepared for:** AWS Student Community Day Kuching 2026 Hackathon  
**Problem Statement:** Government agencies manage thousands of documents — policies, SOPs, circulars, guidelines, reports, and meeting minutes. Finding the right information is often time-consuming, leading to slower decision-making and reduced productivity.

---

## Overview of Sources

| # | Title | Scope | Year |
|---|---|---|---|
| 01 | Overcoming Fragmented Knowledge Management in Government Agencies (Esper) | 🌐 International | 2024 |
| 02 | The Hidden Costs of Knowledge Fragmentation (IBM IBV) | 🌐 International | 2026 |
| 03 | Seven Failure Points When Engineering a RAG System (Deakin University) | 🌐 International (Technical) | 2024 |
| 04 | AI-Driven Intelligent Document Processing in Government (WJAETS) | 🌐 International | 2025 |
| 05 | DDMS Implementation Guidelines for Malaysia Public Sector | 🇲🇾 Malaysia | 2020 |
| 06 | e-Government Implementation Challenges in Malaysia & South Korea | 🇲🇾 Malaysia | 2017 |
| 07 | Records Management Practices in Sarawak State Public Services | 🌴 Sarawak | 2012 |
| 08 | Sarawak Adopts AI to Address Citizen Needs (The Edge, 2026) | 🌴 Sarawak | 2026 |

---

## The Zoomed-Out View: From Global to Sarawak

### 🌐 International Level — The Universal Problem

At the global level, research consistently shows that government agencies everywhere are losing billions of dollars and countless hours to fragmented, inaccessible institutional knowledge. The numbers are stark:

- Fewer than **15% of government documents** are easily discoverable through existing search infrastructure (Esper, 2024)
- **65% of employees** work off guidelines that are already outdated (IBM IBV, 2026)
- **47% of digital workers** cannot find the information they need to do their jobs (Gartner/IBM, 2023)
- Duplicated work from knowledge fragmentation costs a mid-sized agency over **$2.3 million per year** (Esper, 2024)
- Knowledge silos cost Fortune 500 companies an estimated **$31.5 billion annually** in lost productivity

The root causes are structural: legacy systems that don't talk to each other, departmental silos, expertise drain as senior staff retire, and a culture that never evolved knowledge management as a discipline alongside technology.

Emerging AI solutions — particularly RAG-based (Retrieval-Augmented Generation) document Q&A systems — offer a technically feasible path forward. However, research from Deakin University (2024) and IBM (2026) shows that even well-designed AI knowledge systems fail when the underlying knowledge is outdated, poorly formatted, or structurally fragmented. The problem is not just retrieval — it is knowledge governance.

---

### 🇲🇾 Malaysia Level — Same Problem, Local Constraints

Malaysia has been trying to solve this for decades. The e-government initiative launched in **1996** included the GOE-EGDMS (Generic Office Environment – Electronic Government Document Management System) as a flagship project. Yet by 2020, adoption of the Digital Document Management System (DDMS) was still "below satisfactory" (DDMS Guidelines paper, 2020).

Key barriers specific to Malaysia:

- Systems exist but retrieval is still broken — staff struggle to find documents even in agencies with DDMS deployed
- Fragmented procurement: different agencies implemented different systems, producing incompatible silos
- No interoperability standard: documents from one ministry cannot be searched or accessed by another
- Training and change management were underinvested; technology rollout without culture change produced shelf-ware
- Language complexity: Bahasa Malaysia, English, and occasionally local languages create indexing inconsistencies

Compared with South Korea — a peer country that successfully modernised its e-government through a centralized coordination body and mandatory interoperability standards — Malaysia's decentralised, agency-by-agency approach has produced a patchwork of partial solutions rather than a unified knowledge system.

The practical implication: any solution targeting Malaysian government agencies must be **low-friction to adopt**, work on top of existing document repositories rather than replacing them, and be usable without heavy retraining.

---

### 🌴 Sarawak Level — The Specific Context

Sarawak adds a third layer of complexity on top of the national challenges:

**From the baseline (2012):** A direct study of Sarawak state public services found that records management practices were weakest specifically in **access and retrieval** — even when documents existed, staff could not reliably find them. There was no central records registry, indexing was inconsistent, and inter-agency document sharing required manual coordination.

**From the current picture (2026):** Sarawak is actively investing in AI and digital transformation under the SDEB 2030. The Sarawak AI Centre (SAIC) was established, and the citizen-facing Dayang AI assistant was launched. But the focus so far has been on **external-facing services** — helping citizens navigate government websites — not on **internal knowledge retrieval** for civil servants. The internal document management gap remains unaddressed.

Sarawak-specific constraints that a solution must consider:
- Rural-urban digital divide — state agencies outside Kuching may have limited or unreliable connectivity
- Ageing and shrinking workforce — document knowledge often trapped in experienced staff, who are increasingly retiring
- Mixed language documents — Bahasa Malaysia, English, and occasionally Iban or other Sarawakian languages in community-level records
- Budget and procurement constraints typical of a state (rather than federal) government

---

## Recurring Pain Factors — Across All Three Levels

The following pain points appear consistently across all 8 sources, spanning international, Malaysian, and Sarawak research:

---

### 🔴 Pain Factor 1: Documents Exist But Can't Be Found
**Frequency:** Mentioned in all 8 sources

The most universal finding. Whether at a global scale (15% discoverability), Malaysia national level (DDMS adoption failure), or Sarawak state level (poor indexing and access), the pattern is identical: documents are created and filed, but retrieval fails. Staff know the information exists somewhere; they just can't get to it.

> *"Finding the right information is often time-consuming"* — Hackathon problem statement  
> *"Fewer than 15% of government records are easily discoverable"* — Esper, 2024  
> *"Records access is the weakest area"* — Sarawak Records Management Study, 2012

---

### 🔴 Pain Factor 2: No Single Source of Truth — Multiple Versions, No Currency
**Frequency:** Mentioned in 6 of 8 sources

Policy documents, SOPs, and circulars exist in multiple versions across shared drives, email threads, printed binders, and systems. Staff cannot tell which version is current. This leads to inconsistent decisions and compliance failures — the equivalent of two departments operating under different rules for the same regulation.

> *"65% of employees say the guidelines governing their work are already outdated"* — IBM IBV, 2026  
> *"Different versions of the same policy can lead to inconsistent decisions"* — IBM IBV, 2026  
> *"No consistent records inventory"* — Sarawak Records Management Study, 2012

---

### 🔴 Pain Factor 3: Siloed Systems That Don't Talk to Each Other
**Frequency:** Mentioned in 7 of 8 sources

Each department maintains its own document store, filing system, and workflow. Documents created in one agency are invisible to another. Cross-agency coordination requires manual email chains and physical document transfers. The silo structure is organizational before it is technical.

> *"Interoperability gaps — government IT systems do not communicate with each other"* — e-Government Malaysia study, 2017  
> *"Siloed storage — each department manages its own records with no cross-department discoverability"* — Sarawak study, 2012  
> *"Legacy systems, departmental silos... have created an environment where institutional memory remains trapped"* — Esper, 2024

---

### 🔴 Pain Factor 4: Institutional Knowledge Walks Out the Door
**Frequency:** Mentioned in 5 of 8 sources

Senior civil servants carry critical institutional knowledge — how policies were interpreted, why certain decisions were made, which circulars supersede others — that is never written down or indexed. When they retire or leave, that knowledge disappears. Malaysia's ageing public sector workforce makes this especially acute.

> *"Government agencies face a 34% retirement rate among senior staff over the next five years"* — Esper, 2024  
> *"Ageing population and labour shortages — fertility rate fell from 2.76 to 1.6"* — The Edge Sarawak, 2026  
> *"When key people leave, context leaves with them"* — IBM IBV, 2026

---

### 🔴 Pain Factor 5: Technology Deployed Without Adoption
**Frequency:** Mentioned in 5 of 8 sources (strongest at Malaysia level)

Malaysia has deployed document management systems. Sarawak has invested in e-government platforms. Yet adoption remains low and usage is superficial. Staff revert to manual processes because systems are hard to use, training was insufficient, and the culture never changed around them. The DDMS paper makes this the central finding.

> *"Adoption of the DDMS is still below satisfaction"* — Malaysia DDMS Study, 2020  
> *"Poor user experience — civil servants find systems difficult to use, reverting to manual processes"* — e-Government Malaysia, 2017  
> *"AI adoption concentrated in flagship agencies, not distributed across all government agencies"* — The Edge Sarawak, 2026

---

### 🔴 Pain Factor 6: Slow Decision-Making as a Direct Consequence
**Frequency:** Mentioned in 6 of 8 sources

Information inaccessibility doesn't just frustrate employees — it directly delays decisions. Policy implementation is slower. Service delivery is slower. Citizens wait longer. And in a government context, slow decisions carry operational, financial, and sometimes legal consequences.

> *"Leading to slower decision-making and reduced productivity"* — Hackathon problem statement  
> *"40–60% reductions in policy implementation time"* seen in agencies that fix knowledge fragmentation — Esper, 2024  
> *"Systematic, efficient records management provides comprehensive information to guarantee unbiased decision"* — Malaysia court records study

---

### 🟡 Pain Factor 7 (Technical): AI Retrieval Systems Fail on Poor Knowledge Quality
**Frequency:** Mentioned in 3 of 8 sources (technical papers)

Even when AI is deployed to solve the retrieval problem, it fails if the underlying documents are poorly formatted, outdated, or inconsistently structured. RAG systems specifically suffer from missing content hallucination, ranking failures, and context-window limitations when applied to large, messy document corpora.

> *"If the wrong document or an outdated policy is retrieved, the answer can still be wrong"* — IBM IBV, 2026  
> *"Seven failure points in RAG systems — from missing content to incomplete extraction"* — Deakin, 2024  
> *"Basic RAG often struggles with complex QA tasks in legal and regulatory domains"* — arXiv, 2025

---

## Summary Matrix: Pain Factors by Scope

| Pain Factor | 🌐 International | 🇲🇾 Malaysia | 🌴 Sarawak |
|---|:---:|:---:|:---:|
| Documents exist but can't be found | ✅ | ✅ | ✅ |
| No single source of truth / version confusion | ✅ | ✅ | ✅ |
| Siloed systems, no interoperability | ✅ | ✅ | ✅ |
| Institutional knowledge loss (staff departure) | ✅ | ✅ | ✅ |
| Technology deployed without adoption | ✅ | ✅ | ✅ |
| Slow decision-making as outcome | ✅ | ✅ | ✅ |
| AI/RAG fails on poor knowledge quality | ✅ | — | — |

Every single pain factor appears at **all three geographic levels**. The problem is not unique to Sarawak or Malaysia — it is universal. Sarawak is, however, at a **particularly actionable inflection point**: the SDEB 2030 creates political will and budget, SAIC provides a coordination body, and there is no existing internal-facing AI knowledge tool yet deployed.

---

## Implications for Solution Design

Based on the synthesis, a winning solution should:

1. **Prioritize retrieval + verification over raw retrieval** — not just return documents, but surface the most current version with a source citation
2. **Work on top of existing document stores** — not require agencies to migrate or restructure their existing systems
3. **Be low-friction to use** — civil servants must be able to query in natural language, not learn a new interface or system
4. **Handle diverse document formats** — PDFs, Word docs, scanned circulars, meeting minutes in mixed languages
5. **Show provenance clearly** — every answer should show which document it came from, when that document was last updated, and which department owns it
6. **Acknowledge what it doesn't know** — a system that says "I don't have a current policy on this" is safer than one that hallucinates an answer

---

*All content paraphrased for compliance with source licensing restrictions. Sources cited inline and in individual research files.*
