# C002 input

The disposable `synology-magnet-c002` repository is a real Chrome Manifest V3 extension with two controlled regressions:

- release metadata no longer agrees across the package, manifest and README;
- popup JavaScript references a DOM element ID that no longer exists.

The repository's existing `npm test` validator detects both regressions. The exact injected lines and gold-standard corrections must not be disclosed to the pilot.
