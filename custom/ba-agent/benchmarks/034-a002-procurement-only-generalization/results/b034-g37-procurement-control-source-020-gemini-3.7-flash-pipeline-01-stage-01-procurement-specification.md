# BA Specialist Pipeline Stage

## Metadata

```json
{
  "agent_path": "custom/ba-agent/skills/prepare-procurement-specification/SKILL.md",
  "agent_sha256": "a820bf449f4e9daf6280ec16d526271fd86cd5c7a807cd78395e10add81f12d7",
  "agent_version": "0.2.0",
  "ended_at": "2026-09-05T21:32:37Z",
  "error": null,
  "finish_reason": "STOP",
  "max_output_tokens": 8192,
  "model": "gemini-3.7-flash",
  "pipeline": "Benchmark 034 \u2014 Evidence-preserving fixed procurement control",
  "run_id": "b034-g37-procurement-control-source-020",
  "stage_id": "procurement-specification",
  "stage_index": 1,
  "stage_input_sha256": "2f9c5687cbe0ff0f174ea6aaf3bd165de5d8e75c40460f5e544455e5bb5aa73d",
  "stage_name": "Prepare Procurement Specification",
  "started_at": "2026-09-05T21:32:29Z",
  "status": "success",
  "temperature": 0.0,
  "upstream_output_sha256": null,
  "usage": {
    "candidatesTokenCount": 2191,
    "promptTokenCount": 3013,
    "promptTokensDetails": [
      {
        "modality": "TEXT",
        "tokenCount": 3013
      }
    ],
    "serviceTier": "standard",
    "thoughtsTokenCount": 667,
    "totalTokenCount": 5871
  }
}
```

---

## Stage output

# Procurement Specification: Mariner Legal Ergonomic Task Chairs

---

### 1. Procurement objective

Procure **65 ergonomic task chairs** across two office locations for Mariner Legal to replace existing task seating in accordance with workplace ergonomic assessments, accommodation requirements, facilities duty profile, and procurement policy.

---

### 2. Domain classification

- **Primary domain:** Furniture / physical fit-out.
- **Domain-specific assumptions:** Commercial office environment fit-out across two office delivery locations. No software, IT networking, cabling, or architectural structural integration is required.

---

### 3. Specification register

| Spec ID | Requirement / Capability | Strength | Source Reference / Source Wording | Rationale | Evidence Needed from Candidate / Vendor |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SPEC-01** | **Quantity**<br>Total supply of 65 ergonomic task chairs across two office locations. | **Hard minimum** | P-01: "Purchase quantity is 65 chairs." | Baseline operational requirement for full workplace replacement across two offices. | Vendor quotation confirming supply capacity for 65 units across designated locations. |
| **SPEC-02** | **Seat-Height Adjustment**<br>Seat-height adjustment spanning at least 420 mm to 540 mm. | **Hard minimum** | P-02: "The chair must support seat-height adjustment spanning at least 420 mm to 540 mm." (Workplace ergonomics assessment ERG-2026-14) | Ergonomic fit requirement to accommodate the user population height range. | Manufacturer specification sheet or dimensional drawing showing seat-height range covering at least 420 mm to 540 mm. |
| **SPEC-03** | **Seat-Depth Adjustment**<br>Adjustable seat depth with an available range that includes 450 mm through 500 mm. | **Hard minimum** | P-03: "The chair must support adjustable seat depth with an available range that includes 450 mm through 500 mm." (ERG-2026-14) | Ergonomic fit requirement for varied thigh length support. | Manufacturer specification sheet indicating seat-depth adjustability covering 450 mm to 500 mm. |
| **SPEC-04** | **Lumbar Support Adjustment**<br>User-adjustable lumbar support height. | **Hard minimum** | P-04: "The chair must provide user-adjustable lumbar support height." (ERG-2026-14) | Targeted lower back ergonomic support across diverse postures. | Product technical sheet showing user-adjustable lumbar height mechanism. |
| **SPEC-05** | **Armrest Adjustability**<br>Armrests adjustable for both height and lateral width. | **Hard minimum** | P-05: "Armrests must be adjustable for both height and lateral width." (ERG-2026-14) | Ergonomic accommodation for shoulder, arm, and torso dimensions. | Manufacturer technical documentation confirming independent height and lateral width adjustment. |
| **SPEC-06** | **User Weight Rating**<br>Manufacturer weight rating for users up to at least 150 kg. | **Hard minimum** | P-06: "The exact chair model must be rated for users up to at least 150 kg." (WHS accommodation register) | Compliance with workplace health and safety accommodation standards. | Official manufacturer certification or data sheet stating maximum user weight capacity of at least 150 kg. |
| **SPEC-07** | **Commercial-Use Classification**<br>Documented by the manufacturer for full-day commercial office use. | **Hard minimum** | P-07: "The exact model must be documented by the manufacturer for full-day commercial office use." (Facilities operating profile) | Ensures durability and suitability for full-time commercial workplace operations. | Manufacturer commercial duty rating documentation / commercial warranty rating sheet. |
| **SPEC-08** | **Commercial Warranty**<br>At least a 5-year commercial-use warranty. | **Hard minimum** | P-08: "The exact offered model must carry at least a 5-year commercial-use warranty." (Procurement policy PR-08) | Minimum required asset protection and commercial policy compliance. | Manufacturer warranty statement confirming 5+ years commercial application coverage. |
| **SPEC-09** | **Unit Price**<br>Target unit price of A$750 ex GST per chair or less. | **Target** | P-09: "The procurement team is targeting A$750 ex GST per chair or less. This is not a Hard minimum." | Budgetary cost efficiency goal. | Binding commercial unit pricing in formal vendor quote. |
| **SPEC-10** | **Delivery Lead Time**<br>Delivery to both offices within 10 weeks of purchase order. | **Target** | P-10: "Delivery to both offices within 10 weeks of purchase order is preferred for programme timing. This is a Target, not an eligibility gate." | Programme roll-out schedule alignment. | Quoted delivery lead time to both specified office locations. |
| **SPEC-11** | **Recycled Content**<br>Manufacturer evidence of 30% or greater recycled material content by weight. | **Preference** | P-11: "Preference for manufacturer evidence of 30% or greater recycled material content by weight. This is not a Hard minimum." | Sustainability and environmental impact preference. | Manufacturer environmental declaration, sustainability data sheet, or third-party environmental product declaration (EPD). |
| **SPEC-12** | **Upholstery Colour**<br>Post-shortlist configuration selection. | **Unknown** (Non-eligibility configuration item) | P-12: "Final upholstery colour is not yet selected. Colour must remain a post-shortlist configuration decision and must not block evaluation of otherwise eligible chair platforms." | Aesthetic decision deferred until shortlist platform eligibility is established. | Availability of commercial fabric colour swatches / finish palette from vendor upon request. |

---

### 4. Compatibility / dependency questions

1. **Delivery Site Logistics:** What are the exact quantity splits and delivery access constraints between the two office locations? *(Relevance: affects freight and delivery scheduling for Target SPEC-10, though not individual chair model eligibility).*
2. **Upholstery Standard Fabric Range:** Do candidate platforms offer standard commercial fabric tiers that include typical office palettes at no extra unit cost impact relative to Target SPEC-09?

---

### 5. Exclusions / deferred scope

- **Excluded from scope:** Software, network equipment, power/data connectivity, building works, architectural decision recording (ADR), and IT-style integration testing.
- **Deferred decisions:** Final selection of upholstery fabric colour (SPEC-12), which is explicitly deferred to post-shortlist configuration and must not gate platform technical eligibility.
- **Supplier exclusivity:** No sole-source, incumbent-reseller exclusivity, or mandatory brand constraints apply.

---

### 6. Downstream procurement handoff

- **Market expansion (`expand-procurement-market`):** Must broaden market coverage beyond the single incumbent office-furniture reseller candidate set across qualified commercial seating manufacturers and distributors meeting SPEC-01 through SPEC-08.
- **Verification (`verify-procurement-options`):** Must evaluate all candidate options against Hard minimums (SPEC-01 through SPEC-08), score Target (SPEC-09, SPEC-10) and Preference (SPEC-11) criteria accordingly, and treat SPEC-12 (Upholstery Colour) strictly as a non-blocking configuration item. Missing candidate facts must remain treated as unverified/unknown.

---

## SUPPLIED_CANDIDATE_EVIDENCE_FOR_DOWNSTREAM

### Candidate C-01 — ErgoNova E8 Commercial
**Manufacturer data sheet supplied**
- Seat-height adjustment: 415–555 mm.
- Seat-depth adjustment: 440–515 mm.
- Adjustable lumbar-support height: yes.
- Armrest height adjustment: yes.
- Armrest lateral-width adjustment: yes.
- Maximum user rating: 160 kg.
- Commercial-use classification: full-day commercial task chair.
- Commercial warranty: 7 years.
- Quoted unit price: A$735 ex GST.
- Quoted delivery: 8 weeks.
- Manufacturer recycled-content declaration: 35% by weight.

### Candidate C-02 — ArcSeat Pro 5
**Manufacturer data sheet supplied**
- Seat-height adjustment: 425–545 mm.
- Seat-depth adjustment: 445–510 mm.
- Adjustable lumbar-support height: yes.
- Armrest height adjustment: yes.
- Armrest lateral-width adjustment: yes.
- Maximum user rating: 135 kg.
- Commercial-use classification: full-day commercial task chair.
- Commercial warranty: 10 years.
- Quoted unit price: A$690 ex GST.
- Quoted delivery: 6 weeks.
- Recycled-content evidence: not supplied.

### Candidate C-03 — WorkForm Flex 2
**Manufacturer data sheet supplied**
- Seat-height adjustment: 420–550 mm.
- Seat-depth adjustment: 450–505 mm.
- Adjustable lumbar-support height: yes.
- Armrest height adjustment: yes.
- Armrest lateral-width adjustment: not stated in supplied evidence.
- Maximum user rating: 150 kg.
- Commercial-use classification: full-day commercial task chair.
- Commercial warranty: 5 years.
- Quoted unit price: A$720 ex GST.
- Quoted delivery: 12 weeks.
- Manufacturer recycled-content declaration: 20% by weight.

PIPELINE_HANDOFF_COMPLETE: PROCUREMENT_SPECIFICATION
