# BA Specialist Pipeline Stage

## Metadata

```json
{
  "agent_path": "custom/ba-agent/skills/prepare-procurement-specification/SKILL.md",
  "agent_sha256": "a820bf449f4e9daf6280ec16d526271fd86cd5c7a807cd78395e10add81f12d7",
  "agent_version": "0.2.0",
  "ended_at": "2026-09-05T21:27:07Z",
  "error": null,
  "finish_reason": "STOP",
  "max_output_tokens": 8192,
  "model": "gemini-3.7-flash",
  "pipeline": "Benchmark 034 \u2014 Optimal fixed procurement control",
  "run_id": "b034-g37-procurement-control-019",
  "stage_id": "procurement-specification",
  "stage_index": 1,
  "stage_input_sha256": "26fa3397cb5ca68e2465aa744e01d993f9d3b5be3f6212574817307b6505b0f0",
  "stage_name": "Prepare Procurement Specification",
  "started_at": "2026-09-05T21:26:59Z",
  "status": "success",
  "temperature": 0.0,
  "upstream_output_sha256": null,
  "usage": {
    "candidatesTokenCount": 1897,
    "promptTokenCount": 2929,
    "promptTokensDetails": [
      {
        "modality": "TEXT",
        "tokenCount": 2929
      }
    ],
    "serviceTier": "standard",
    "thoughtsTokenCount": 685,
    "totalTokenCount": 5511
  }
}
```

---

## Stage output

### 1. Procurement Objective

Procure **65 ergonomic task chairs** across two Mariner Legal offices meeting workplace ergonomic, safety, and commercial warranty standards within target cost and delivery parameters.

---

### 2. Domain Classification

- **Domain:** Furniture / physical fit-out.
- **Domain-specific assumptions:** Commercial office task seating across two office locations. No IT, networking, electrical infrastructure, structural mounting, or software integration scope applies.

---

### 3. Specification Register

| Spec ID | Requirement / Capability | Strength | Source Reference / Wording | Rationale | Evidence Needed from Candidate / Vendor |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SPEC-01** | **Total Quantity**<br>Supply of 65 commercial ergonomic task chairs distributed across two offices. | **Hard minimum** | Baseline P-01 ("Purchase quantity is 65 chairs.") | Standard fleet volume requirement across two office locations. | Vendor commitment to supply 65 units of the specified exact model. |
| **SPEC-02** | **Seat-Height Adjustment Range**<br>Seat-height adjustment range must span at least 420 mm to 540 mm (i.e. minimum height $\le 420\text{ mm}$ and maximum height $\ge 540\text{ mm}$). | **Hard minimum** | Baseline P-02 / ERG-2026-14 ("The chair must support seat-height adjustment spanning at least 420 mm to 540 mm.") | Workplace ergonomics assessment compliance for diverse staff population. | Manufacturer technical data sheet or dimensional specification showing continuous or stepped adjustment spanning at least 420 mm to 540 mm. |
| **SPEC-03** | **Seat-Depth Adjustment Range**<br>Adjustable seat depth with an available range that includes 450 mm through 500 mm (i.e. minimum depth $\le 450\text{ mm}$ and maximum depth $\ge 500\text{ mm}$). | **Hard minimum** | Baseline P-03 / ERG-2026-14 ("The chair must support adjustable seat depth with an available range that includes 450 mm through 500 mm.") | Workplace ergonomics assessment compliance for user thigh length accommodation. | Manufacturer technical data sheet or dimensional drawing showing seat-depth adjustment range encompassing 450 mm to 500 mm. |
| **SPEC-04** | **Lumbar Support Height Adjustment**<br>User-adjustable lumbar support height. | **Hard minimum** | Baseline P-04 / ERG-2026-14 ("The chair must provide user-adjustable lumbar support height.") | Ergonomic back support customization required by ergonomic baseline. | Manufacturer specification confirming independent user-adjustable lumbar height mechanism. |
| **SPEC-05** | **Armrest Multi-Axis Adjustment**<br>Armrests must be adjustable for both height and lateral width. | **Hard minimum** | Baseline P-05 / ERG-2026-14 ("Armrests must be adjustable for both height and lateral width.") | Ergonomic arm support and shoulder alignment requirement. | Manufacturer specification explicitly confirming both height adjustability and lateral width adjustability of armrests. |
| **SPEC-06** | **User Weight Capacity**<br>Maximum user weight rating of at least 150 kg for the exact offered model. | **Hard minimum** | Baseline P-06 / WHS accommodation register ("The exact chair model must be rated for users up to at least 150 kg.") | Work Health and Safety (WHS) accommodation compliance. | Manufacturer published specification or certified rating document confirming $\ge 150\text{ kg}$ safe working load. |
| **SPEC-07** | **Commercial-Duty Rating**<br>Documented by the manufacturer for full-day commercial office use. | **Hard minimum** | Baseline P-07 / Facilities operating profile ("The exact model must be documented by the manufacturer for full-day commercial office use.") | Facilities operational durability requirement for continuous commercial office operation. | Manufacturer product literature or test classification certifying full-day/commercial task use. |
| **SPEC-08** | **Commercial Warranty**<br>Commercial-use warranty coverage of at least 5 years. | **Hard minimum** | Baseline P-08 / PR-08 ("The exact offered model must carry at least a 5-year commercial-use warranty.") | Commercial procurement policy risk and lifecycle protection. | Manufacturer written commercial warranty statement covering $\ge 5\text{ years}$. |
| **SPEC-09** | **Target Unit Price**<br>Unit price of A$750 ex GST per chair or less. | **Target** | Baseline P-09 ("The procurement team is targeting A$750 ex GST per chair or less. This is not a Hard minimum.") | Procurement budget benchmark (does not disqualify higher bids, used for scoring/value assessment). | Itemized commercial pricing quotation per unit ex GST for a volume of 65 chairs. |
| **SPEC-10** | **Delivery Lead Time**<br>Delivery to both office locations within 10 weeks of purchase order. | **Target** | Baseline P-10 ("Delivery to both offices within 10 weeks of purchase order is preferred for programme timing. This is a Target, not an eligibility gate.") | Programme scheduling preference. | Vendor lead-time quotation to the two specified delivery locations. |
| **SPEC-11** | **Recycled Material Content**<br>Manufacturer evidence of 30% or greater recycled material content by weight. | **Preference** | Baseline P-11 ("Preference for manufacturer evidence of 30% or greater recycled material content by weight. This is not a Hard minimum.") | Environmental preference / sustainability scoring. | Manufacturer environmental product declaration (EPD), sustainability datasheet, or certified declaration of recycled content percentage by weight. |
| **SPEC-12** | **Upholstery Colour / Finish Selection**<br>Upholstery colour selection is deferred to post-shortlist configuration. | **Unknown / Deferred** | Baseline P-12 ("Final upholstery colour is not yet selected. Colour must remain a post-shortlist configuration decision and must not block evaluation of otherwise eligible chair platforms.") | Final aesthetic choice pending; standard platform compatibility required. | Vendor catalogue showing available standard commercial upholstery ranges/palettes (for subsequent selection). |

---

### 4. Compatibility / Dependency Questions

1. **Two-Office Delivery Split:** What is the specific quantity breakdown and site delivery address for each of the two offices? *(Required for freight quotation and logistics scheduling prior to PO issuance; does not affect chair platform eligibility).*
2. **Standard Commercial Fabric Availability:** Does the offered base model include standard tier commercial fabrics without lead time exceeding the targeted delivery envelope? *(Required to confirm configuration options post-shortlist).*

---

### 5. Exclusions / Deferred Scope

- **Brand / Reseller Exclusivity:** No sole-source, specific brand mandates, or incumbent reseller exclusivity apply.
- **Upholstery Colour Selection:** Colour selection is deferred to post-shortlist configuration and is excluded from initial technical pass/fail eligibility.
- **Assembly / Installation Services:** Non-furniture services (IT, building works, structural alterations) are strictly out of scope. Delivery and on-site placement terms remain standard commercial delivery.

---

### 6. Downstream Procurement Handoff

- **For `expand-procurement-market`:**
  - Broaden search across commercial office furniture manufacturers and alternate authorized commercial dealers beyond the incumbent reseller.
  - Screen candidate platforms strictly against Hard minimums: height range $\ge [420, 540]\text{ mm}$, depth range $\ge [450, 500]\text{ mm}$, adjustable lumbar height, 2D (height + width) adjustable armrests, $\ge 150\text{ kg}$ rating, full-day commercial duty rating, and $\ge 5\text{-year}$ commercial warranty.
  - Seek options that align with Target unit price ($\le \text{A}\$750\text{ ex GST}$), Target delivery ($\le 10\text{ weeks}$), and Preference ($\ge 30\%$ recycled content).
- **For `verify-procurement-options`:**
  - Verify exact manufacturer datasheets for candidate claims.
  - Verify missing candidate attributes (e.g., C-03 armrest lateral-width adjustability, C-02 weight rating compliance, C-02 recycled-content documentation) directly against verified manufacturer evidence without assuming compliance.

PIPELINE_HANDOFF_COMPLETE: PROCUREMENT_SPECIFICATION
