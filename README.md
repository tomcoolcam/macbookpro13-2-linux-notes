# MacBookPro13,2 Linux notes

Reproducible observations from Linux suspend/resume and Touch Bar experiments
on an Apple MacBookPro13,2. This is an investigation log, not a working suspend fix.

> MacBook Pro is a trademark of Apple Inc., registered in the U.S. and other
> countries and regions. This independent project is not affiliated with,
> sponsored by, or endorsed by Apple Inc.

## Current findings

| Component | Observed behavior |
| --- | --- |
| Local console and keyboard | Worked after the latest instrumented s2idle cycle |
| Thunderbolt / external USB3 | Controllers became inaccessible after that cycle |
| Wi-Fi | Replied to 3/5 immediate post-resume pings; first two were lost |
| Touch Bar | Lighting and mode switching worked with locally adapted drivers; those modules were absent in the latest cycle |
| Sleep | Latest machine-suspend phase lasted about 120 seconds; controller recovery still failed |

The test machine reported Arch Linux kernel `7.2.6-arch2-1`, firmware
`529.120.1.0.0`, and the boot option `pcie_port_pm=off`. Findings are specific
to this configuration. The external storage device was disconnected for testing.

## Evidence

- [Linux installation and configuration](docs/linux-setup.md)

- [Latest native PMCSR measurements and macOS comparison](docs/2026-09-17-native-pmcsr.md)
- [Earlier short s2idle experiment](docs/2026-09-17-s2idle.md)
- [Earlier observations and limitations](docs/background.md)
- [Diagnostic script and usage](scripts/README.md)
- [Selected, sanitized trace evidence](data/2026-09-17/README.md)
- [Sources and attribution](docs/sources.md)

The firmware power-on methods were called, but the Thunderbolt register-access
sequence did not reach its write step. ACPI power calls still returned success.
The underlying loss of device access remains unexplained.

New native PCI measurements show valid PMCSR values before D3 writes and
`0xffff` readbacks about 50–53 ms later, before the respective ACPI power calls.
The kernel initially masks these readbacks into state 3. This narrows the
observed sequence but does not establish a recovery fix.

## Contributing observations

Include the exact model, kernel, boot options, loaded drivers, attached devices,
test procedure, and before/after behavior. Distinguish measured facts from
hypotheses. Remove identifiers and credentials from logs before submitting.
Do not repeat a sleep experiment from an already broken PCI device state.

Original documentation and diagnostic code are provided under the MIT license.
Upstream drivers and firmware are not included; their licenses remain separate.
