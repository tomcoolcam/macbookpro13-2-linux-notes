# MacBookPro13,2 Linux notes

Reproducible observations from Linux suspend/resume and Touch Bar experiments
on an Apple MacBookPro13,2. This is an investigation log, not a working suspend fix.

> MacBook Pro is a trademark of Apple Inc., registered in the U.S. and other
> countries and regions. This independent project is not affiliated with,
> sponsored by, or endorsed by Apple Inc.

## Current findings

| Component | Observed behavior |
| --- | --- |
| Local console and keyboard | Worked in earlier tests; no separate user confirmation for the September 18 cycles |
| Thunderbolt / external USB3 | Remained accessible in three s2idle cycles with experimental LC sleep omission |
| External SSD | Two cycles with SSD attached; 256 MiB read hashes matched before/after each cycle |
| Wi-Fi | Latest immediate post-resume check: 3/5 replies, first two lost |
| Touch Bar | Previously worked with locally adapted drivers; those modules were absent during these tests |
| Sleep power | User reported 5.9 W in one SSD cycle; low-power sleep remains unresolved |

The test machine reported Arch Linux kernel `7.2.6-arch2-1`, firmware
`529.120.1.0.0`, and the boot option `pcie_port_pm=off`. Existing D3cold guards
remained active. September 18 tests temporarily disabled internal iBridge USB
wakeup and omitted the entire root-switch LC sleep function using a private
experimental module. These are specific test conditions, not stock Linux behavior.

## Evidence

- [September 18: LC omission, SSD checks, and PCI save/restore ordering](docs/2026-09-18-lc-sleep-ordering.md)
- [Linux installation and configuration](docs/linux-setup.md)
- [Earlier native PMCSR measurements and macOS comparison](docs/2026-09-17-native-pmcsr.md)
- [Earlier short s2idle experiment](docs/2026-09-17-s2idle.md)
- [Earlier observations and limitations](docs/background.md)
- [Diagnostic script and usage](scripts/README.md)
- [Selected, sanitized earlier trace evidence](data/2026-09-17/README.md)
- [Sources and attribution](docs/sources.md)

The earlier controller failures remain valid observations. Later experiments
narrow the investigation: controller D3hot transitions can succeed when LC sleep
is omitted, without the experimental NO_D3 protection. This does not establish
which operation inside the omitted function causes the failure, or how to enter
and leave a genuinely low-power state correctly.

## Contributing observations

Include the exact model, kernel, boot options, loaded drivers, attached devices,
test procedure, and before/after behavior. Distinguish measured facts from
hypotheses. Remove identifiers and credentials from logs before submitting.
Do not repeat a sleep experiment from an already broken PCI device state.

Original documentation and diagnostic code are provided under the MIT license.
Upstream drivers and firmware are not included; their licenses remain separate.
