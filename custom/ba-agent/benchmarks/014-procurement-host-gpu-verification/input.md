# Benchmark 014 — Used Workstation + GPU Procurement Verification

## User objective

Build a low-cost local AI workstation from a used/refurbished tower plus an RTX 3060 12 GB GPU.

The user wants a recommendation **only where the supplied evidence is strong enough to buy confidently**. Do not browse the web; assess only the evidence packet below.

## Requirements

### Hard gates

- **H-01 — Budget:** host + GPU + stated mandatory freight must be no more than **A$850**.
- **H-02 — GPU:** use Candidate G1, an RTX 3060 12 GB.
- **H-03 — Physical fit:** the host must accept a **full-height, dual-slot card at least 242 mm long**.
- **H-04 — Expansion interface:** the host must provide a PCIe x16 slot suitable for the card.
- **H-05 — Power capacity:** the **exact host being sold** must have a PSU rated at least **400 W**.
- **H-06 — GPU power connector:** the **exact host being sold** must provide at least **one 8-pin PCIe GPU power connector** (a 6+2 connector is acceptable).

### Preferences

- **P-01:** at least 16 GB RAM already installed.
- **P-02:** SSD already installed.
- **P-03:** warranty or returns are preferred.
- **P-04:** lower total cost is preferred after hard gates are satisfied.

## Candidate G1 — GPU

### Exact listing G1-LISTING

- Used Gigabyte RTX 3060 EAGLE OC 12G.
- Price: **A$350**, pickup only; no freight.
- Seller states: “tested working under load.”
- Listing photo clearly shows the model label `GV-N3060EAGLE OC-12GD`.

### Manufacturer specification G1-OEM

For model `GV-N3060EAGLE OC-12GD`:

- 12 GB graphics memory.
- Card dimensions: **242 mm x 124 mm x 41 mm**.
- Dual-slot card.
- External power: **1 x 8-pin**.
- Board power: 170 W.

The manufacturer page does not establish anything about the PSU or connectors present in any host listing.

---

## Host A — Lenovo ThinkStation P330 Tower listing

### Exact listing A-LISTING

- “Lenovo ThinkStation P330 Tower, i7-8700, 16 GB, 512 GB SSD.”
- Price: **A$360**, freight included.
- Refurbisher provides 12-month return-to-base warranty.
- Seller description says: **“original Lenovo PSU; workstation ready for graphics upgrade.”**
- No PSU wattage is stated.
- No PSU label photo is supplied.
- No PCIe GPU-power connector photo or connector count is supplied.
- Listing identifies the chassis only as `ThinkStation P330 Tower`; no machine-type/configuration suffix is supplied.

### Lenovo family guide A-FAMILY

The P330 Tower family guide states:

- tower chassis provides a full-height PCIe x16 graphics slot;
- graphics-card length allowance is up to **267 mm**;
- P330 Tower systems were offered with **250 W or 400 W power supplies depending on configuration**.

The family guide does not identify which PSU is installed in A-LISTING and does not establish the GPU-power connector present in that exact unit.

---

## Host B — HP Z4 G4 exact listing

### Exact listing B-LISTING

- HP Z4 G4 Workstation, Xeon W-2123, 16 GB, 512 GB SSD.
- Price: **A$430**, pickup only; no freight.
- 90-day seller warranty.
- Listing gives serial-specific photos.
- PSU-label photo is readable and shows **750 W**.
- Internal photo clearly shows **two 6+2-pin PCIe power connectors** available from the PSU harness.
- Seller identifies the chassis as the standard Z4 G4 tower and states no internal expansion cages have been added.

### HP model guide B-OEM

For the Z4 G4 tower chassis:

- full-height PCIe x16 graphics slots are supported;
- the documented graphics-card clearance in the relevant slot is **280 mm**;
- dual-slot graphics cards are supported in that position.

---

## Host C — Dell OptiPlex 7060 SFF listing

### Exact listing C-LISTING

- Dell OptiPlex 7060 **Small Form Factor**.
- Price: **A$220**, freight included.
- 16 GB RAM, 256 GB SSD.
- 12-month refurbisher warranty.
- PSU label shown in exact listing: **200 W**.

### Dell model guide C-OEM

- SFF chassis accepts low-profile expansion cards only.
- PCIe x16 slot is present.

---

## Host D — Marketplace custom tower

### Exact listing D-LISTING

- “Custom gaming/workstation tower, i7, 16 GB, SSD, **650 W gaming PSU**, ready for GPU.”
- Price: **A$300**, pickup only.
- No returns/warranty.
- Motherboard model is not supplied.
- PSU brand/model and PSU-label photo are not supplied.
- No PCIe power connector photo/count is supplied.
- No internal chassis measurement or case model is supplied.
- Seller says in chat: “3060 should fit, plenty of room.”

No manufacturer/OEM documentation is supplied for Host D.

## Important benchmark boundary

Do not assume specifications not present in this packet. In particular, a product family supporting an option does not prove that the exact unit for sale contains that option.
