# Northbridge Archive — local OCR workstation request

## User request

We need to replace an aging OCR workstation used to digitize historic records. I would like to get to a buying decision quickly, ideally with a shortlist of hardware, but I do not want us to buy the wrong platform.

The notes below are a mixture of emails and meeting comments. Please work out the right path from requirements through architecture and procurement. If something important means we are not ready to shop yet, stop there rather than guessing.

---

## Source notes

### Records Manager email

- The archive scans bound and loose paper records into TIFF/PDF files.
- The new setup must keep restricted collection images and OCR text **inside the archive network**. Cloud OCR is not permitted under Records Handling Standard RH-7.
- Staff would like search-ready text generated faster than the current machine, but nobody has agreed a contractual processing-time threshold.
- Around **120,000 pages per year** was quoted in the funding request. That is an estimate based on last year, not a guaranteed annual volume.
- Most work is batch processing during staffed hours. There is no requirement for 24x7 processing.

### Digitisation technician notes

- Current workflow uses ScanFlow Desktop plus an OCR engine supplied by a third party.
- The team is considering a newer OCR engine release, but the exact edition and licence have **not been selected**.
- One vendor demonstration used GPU acceleration. The technician therefore suggested buying a powerful GPU.
- Nobody has confirmed whether the OCR edition the archive will license actually supports GPU acceleration, which GPU APIs/models it supports, or whether GPU acceleration materially helps this archive's document mix.
- The current scanner exports files to an SMB share on the existing NAS. The new workstation can continue reading/writing that share.

### Infrastructure notes

- The archive network provides wired Ethernet to the workstation location and access to the existing NAS.
- The exact network link speed at the workstation wall port has not been supplied in this packet.
- Restricted records must remain on the archive network under RH-7.
- Standard managed Windows endpoints are supported by the infrastructure team. A Linux workstation might be supportable, but no decision has been made and support ownership for Linux would need to be established.
- No approved CPU, RAM, GPU, SSD, chassis, power-supply or network-performance minimums have been defined for this replacement.

### Facilities / physical notes

- The replacement must fit under the existing desk.
- Available floor footprint was measured as **up to 240 mm wide and 520 mm deep**. Height is not constrained by the desk.
- The user would prefer a reasonably quiet system, but no noise threshold has been specified.

### Proposed implementation from the technician

> Could we keep one of our existing mini PCs and attach a desktop GPU in an external box over USB? That would avoid replacing the whole PC.

Evidence supplied for the exact mini-PC model:

- two USB-A 3.2 Gen 1 ports;
- one USB-C port documented for USB 3.2 Gen 1 data and DisplayPort Alt Mode;
- the model documentation does **not** list Thunderbolt, USB4 or an external PCIe expansion capability.

No external-GPU enclosure or adapter has been selected.

### Finance note

- Funding target is **around A$2,500** for the workstation hardware.
- This is a planning target, not an absolute approved ceiling.
- Software licensing is funded separately.

### Meeting excerpt

**Records Manager:** “If the mini-PC idea is solid, great. If it is a dead end, I would rather replace it properly.”

**Digitisation technician:** “The demo box had a GPU, so I assume we need one.”

**Infrastructure:** “We need the actual OCR software requirements before we size anything. We also need to know whether the workload is CPU-bound, GPU-bound, memory-bound or storage/network-bound.”

**Records Manager:** “Can we just make a shortlist now and verify the details with sellers later?”

**Infrastructure:** “Some seller checks can wait, but choosing a workstation class before we know the OCR runtime and acceleration requirements could send us down the wrong architecture.”

---

## Evidence status intentionally present in the packet

- On-network/local processing requirement: Confirmed by RH-7.
- 120,000 pages/year: workload estimate, not hard capacity requirement.
- Faster than current machine: desired outcome, no sourced numeric threshold.
- A$2,500: Target, not hard ceiling.
- Windows support: Confirmed standard support path.
- Linux: Candidate/support ownership unresolved.
- under-desk width/depth limits: Confirmed physical constraints.
- GPU requirement: **Unknown**; proposed from a demo, not established by selected OCR software.
- OCR engine edition/licence: **Unknown / not selected**.
- OCR engine hardware/OS/GPU support matrix: **Unknown**.
- workload bottleneck / representative benchmark: **Unknown**.
- network link speed at workstation: Unknown, but existing NAS connectivity is Confirmed.
- exact CPU/RAM/GPU/storage/network sizing: Unknown.
- proposed USB external-GPU route: supplied exact mini-PC evidence does not establish a supported external PCIe path.

The desired outcome is a defensible replacement architecture that can later become a procurement specification and shortlist. Do not force procurement stages if the architecture is not stable enough yet.
