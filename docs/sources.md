# Sources and attribution

## LC sleep and ordering update, 2026-09-18

- Primary evidence: private September 17–18 traces and September 18 read-only
  SSD checks. The running kernel BTF supplied structure/bitfield layouts;
  matching installed kernel disassembly validated instruction probes.
- Linux Thunderbolt implementation, used to interpret function boundaries:
  https://github.com/torvalds/linux/blob/master/drivers/thunderbolt/lc.c
  and https://github.com/torvalds/linux/blob/master/drivers/thunderbolt/tb.c.
- Linux PCI save/restore and PM dispatch: the `pci.c` and `pci-driver.c` sources
  linked below. These GPL sources and the private GPL experiment module are
  not included in, or relicensed by, this MIT documentation repository.
- The power figure is a user report, with measurement limitations in the report.

## Native PMCSR update, 2026-09-17

- Primary Linux evidence: private trace of the installed `7.2.6-arch2-1`
  kernel and offline inspection of its matching `vmlinux`. Running/image build
  identifiers and probe instruction sites were checked. The report publishes
  selected original measurement results, not kernel code or disassembly.
- Explanatory Linux PCI implementation:
  https://github.com/torvalds/linux/blob/master/drivers/pci/pci.c
  and https://github.com/torvalds/linux/blob/master/drivers/pci/pci-driver.c.
  Linux code retains its upstream GPL licensing; it is not relicensed under MIT.
- Primary macOS evidence: existing private IORegistry snapshots and Unified Log
  records from the controlled sleep on macOS 12.7.6, plus private offline analysis
  of the local AppleThunderboltNHI driver. Its build identifier and logging call
  sites were matched to the recorded messages. Only original observations and
  interpretations are included here; Apple binaries and disassembly are excluded.

## Earlier investigation

- Original iBridge/Touch Bar driver investigated:
  https://github.com/roadrunner2/macbook12-spi-driver
  Local source checkout: ddfbc7733542b8474a0e8f593aba91e06542be4f.
  Upstream is GPL-licensed; this repository does not redistribute its code.
- Linux power debugging:
  https://www.kernel.org/doc/html/latest/power/basic-pm-debugging.html
- ACPICA status handling:
  https://github.com/torvalds/linux/blob/master/drivers/acpi/acpica/nseval.c
- ACPICA status definitions:
  https://github.com/torvalds/linux/blob/master/include/acpi/acexcep.h

Upstream master links explain implementation concepts; they are not asserted to
be the exact source revision of the test kernel. Firmware method descriptions
come from offline disassembly of this machine's ACPI tables. Raw firmware tables,
full journals, private conversation logs and third-party driver sources are not
included. No Apple firmware, AML bytecode, decompiled ACPI tables, or proprietary
Apple binaries are redistributed by this repository. Original notes and scripts
were prepared with AI assistance and checked against local evidence; independent
reproductions are welcome.
