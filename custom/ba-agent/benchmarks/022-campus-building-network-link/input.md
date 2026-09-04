# Benchmark 022 — Campus Building Network Link Architecture

## User objective

The user wants Building B connected to the main campus network in Building A with a reliable **1 Gbit/s target** for normal business traffic. The link should avoid dependence on the public internet and should be maintainable by the internal network team.

Their first implementation idea is: **“Run one outdoor Cat6 Ethernet cable directly between the two existing switches; the buildings are only about 900 metres apart.”**

Do not reject the connectivity outcome merely because that exact mechanism is infeasible. Design the smallest defensible topology that preserves the objective.

Do not browse the web. Treat the supplied evidence below as authoritative.

## Supplied site evidence

- The measured pathway between the two communications rooms is approximately **900 metres**.
- A continuous underground communications conduit already links the two rooms.
- The conduit has spare usable capacity, but its internal condition and exact pull route have not been surveyed for this project.
- Power and rack space are available in both communications rooms.
- No intermediate powered communications cabinet exists along the route.
- Installing new powered cabinets along the route is not preferred.
- The buildings have separate electrical services. The network team prefers an electrically isolated inter-building medium.

## Supplied Ethernet evidence

- For this benchmark, standards-compliant 1000BASE-T over balanced copper has a **100 metre maximum channel length**.
- The proposed single 900 metre Cat6 channel therefore cannot provide a standards-compliant direct 1000BASE-T link.
- The packet supplies no approved copper extender/repeater design and no powered midpoint location.

## Supplied equipment evidence

- Each existing managed switch has one currently unused **SFP+ cage**.
- The exact switch models and firmware versions have not been supplied.
- No evidence is supplied that any particular optical module, cable assembly, connector type, wavelength or vendor coding is compatible with either switch.
- The switches can carry an ordinary Layer-2 uplink, but the required VLANs, spanning-tree behavior, monitoring and change window have not yet been supplied.

## Service and delivery evidence

- **1 Gbit/s is a target**, not an approved hard minimum.
- Actual current and forecast traffic volume is not supplied.
- Availability/redundancy requirements are Unknown; the user has not said whether a single link is acceptable.
- Required restoration time, maintenance window and migration/rollback expectations are Unknown.
- Whether Building B needs only existing campus VLANs or a new routed/security boundary is Unknown.
- Budget and delivery date are not supplied.
- Procurement may verify exact candidates only after the architecture defines capability and compatibility checks.

## Important benchmark boundaries

- Do not pretend 900 metre copper Ethernet is feasible merely because Cat6 is available.
- Do not invent intermediate cabinets, power, extenders or active repeaters.
- Do not claim that an SFP+ cage proves compatibility with any specific transceiver, fibre type, connector, wavelength, speed mode or vendor product.
- Do not silently promote the 1 Gbit/s target into a hard minimum.
- Do not invent single-mode versus multimode adequacy from distance alone unless the design keeps exact candidate compatibility and installed-path validation explicit.
- Do not invent VLANs, IP addressing, routing, firewalling, redundancy, monitoring tools, construction requirements or outage windows.
- Route unresolved service scope/availability questions back to BA/service ownership; route exact module/cable/vendor compatibility and candidate evidence to Procurement.
