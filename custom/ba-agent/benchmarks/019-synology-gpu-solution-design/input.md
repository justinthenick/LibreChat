# Benchmark 019 — Synology NAS GPU Outcome-to-Architecture Design

## User objective

The user owns a Synology DS918+ NAS and wants to add local GPU acceleration for AI workloads such as ComfyUI image generation and local LLM inference.

Their first implementation idea is: **“GPU-enable the NAS by adding an NVIDIA GPU, ideally something around RTX 3060 12 GB capability, while keeping the NAS as the main platform.”**

The user does not want the goal rejected merely because that exact mechanism is wrong. If the NAS cannot directly host the GPU, design a practical architecture that still achieves the outcome and can later be handed to procurement.

Do not browse the web. Treat the supplied evidence below as authoritative for this benchmark.

## Supplied environment evidence

### Existing NAS

- Model: **Synology DS918+**.
- CPU: Intel Celeron J3455 with integrated Intel graphics.
- Primary current role: shared storage and NAS services.
- Four 3.5/2.5-inch drive bays are in use for NAS storage.
- The unit has two internal M.2 NVMe slots intended by the vendor for SSD cache use.
- The unit has USB 3.x ports for supported external peripherals/storage.
- The unit has **no user-accessible PCIe expansion slot for a discrete graphics card**.
- The unit has **no Thunderbolt/eGPU interface**.
- The USB ports do not provide a normal PCIe graphics-host path for installing a desktop NVIDIA GPU.
- The internal M.2 cache slots are not supplied as a vendor-supported general-purpose external-GPU expansion mechanism.
- The current DSM platform is not supplied as a vendor-supported arbitrary NVIDIA CUDA workstation host.

### Network and storage

- The NAS is connected to the home LAN with 1 GbE Ethernet.
- It can expose storage to another computer using normal network file-sharing protocols such as SMB/NFS.
- The user is willing to keep large datasets, generated output and backups on the NAS.
- A compute device on the same LAN is acceptable if this is the sensible architecture.

### AI workload intent

- The desired workloads benefit from NVIDIA CUDA-class GPU acceleration.
- A target around **12 GB VRAM** is desirable for the intended local image-generation / model workload range.
- The user wants local execution rather than relying primarily on paid cloud inference.
- The solution should be practical to maintain rather than depending on invasive hardware modification or unsupported kernel/firmware hacks.
- The user is comfortable running Windows or Linux on a separate compute machine if needed.
- It is acceptable for model files/cache to live on local SSD in the compute machine while durable data/output remains on the NAS.

## Budget / operational preferences

- Keep the existing NAS rather than replacing it unless replacement becomes clearly preferable.
- Prefer a solution that can be powered down or idled when AI compute is not needed.
- Additional compute hardware is acceptable if architecture requires it.
- Exact product selection and live pricing are **not** part of this benchmark.

## Important benchmark boundaries

- Do not invent a PCIe slot, Thunderbolt capability, proprietary expansion option or supported NVIDIA-driver path that is not in the evidence packet.
- Do not present USB-to-GPU or M.2-to-desktop-GPU hacks as an ordinary supported solution.
- Do not mistake the NAS integrated Intel graphics for a replacement for the requested CUDA-class workload.
- Do not recommend an exact PC/GPU product. Produce a procurement-ready capability specification only after the architecture is chosen.
