# Native PCI power transition: invalid readback before ACPI power-off

Investigation update, 2026-09-17. No working suspend/resume fix is claimed.

## Test and measurement

**OBSERVED:** One instrumented s2idle cycle on MacBookPro13,2, Arch Linux
`7.2.6-arch2-1`, firmware `529.120.1.0.0`, with `pcie_port_pm=off` and the
previously documented D3cold guard rules. External USB devices were disconnected;
the experimental Touch Bar modules were not loaded. PCI identities and Wi-Fi
passed the preflight checks after a fresh boot.

The private diagnostic script captured existing kernel PCI configuration reads
and writes inside `pci_set_low_power_state`, plus the later power-state checks.
Instruction probes recorded the unmasked 16-bit values, target state, cached
state and configuration API return status. Kernel image and running-kernel
build identifiers were matched, and instruction/register/stack locations were
checked before installing the probes. No additional PCI hardware accesses were
introduced by these probes. The script currently published in this repository
predates this private extension and does not reproduce these new measurements.

## Selected measurement results

**OBSERVED:** All four devices requested state 3. The table contains only the
necessary register values and relative timing from the same cycle.

| Device | PMCSR before write | Requested write value | PMCSR after wait | Write return to readback |
| --- | --- | --- | --- | --- |
| RP05 NHI | `0x0108` | `0x010b` | `0xffff` | 51.792 ms |
| RP09 NHI | `0x0108` | `0x010b` | `0xffff` | 50.092 ms |
| RP05 XHC2 | `0x0100` | `0x0103` | `0xffff` | 52.162 ms |
| RP09 XHC3 | `0x0100` | `0x0103` | `0xffff` | 52.597 ms |

The configuration API returned zero for each of the two reads and the write
on each device. The write value is the requested value, not independent proof
of hardware acceptance. Each invalid readback preceded that device's subsequent
ACPI power call and `_PS3` execution. At the native readback probe, cached state
was still 0; at the later `pci_update_current_state` probe it was 3 and PMCSR
was again `0xffff`. The outer power-state function returned zero.

**DERIVED:** The installed kernel's inspected control flow masks this native
readback with 3 before updating cached state. The measured `0xffff` can therefore
be treated as state 3 at that check; the later status update recognizes the
inaccessible value. A zero configuration API status alone does not establish
valid PMCSR contents. The loss is now localized to the interval between the
valid native pre-write read and the native post-write/readback, before the
device's subsequent ACPI power call and before the system sleep phase.

This does not establish that the write alone causes the loss: the devices are
handled concurrently and shared controller, link or power effects remain open.
Nor does this prove physical D3cold or that temporary inaccessibility during
power-off is itself the cause of the later resume failure. Adding a `0xffff`
check might improve error reporting; it is not a demonstrated recovery fix.

## Resume and measurement quality

**OBSERVED:** The machine-suspend phase lasted 119.614 seconds; the complete
sleep call took 126.585 seconds. IRQ 9 and an ACPI fixed-event wake were logged,
consistent with the armed 120-second RTC alarm. The specific fixed event was
not separately traced. The user confirmed working keyboard input after wake;
Wi-Fi answered the last three of five immediate test packets. NHI/bridge
configuration remained inaccessible and XHC2/XHC3 disappeared from PCI sysfs.

The 22 installed probes reported no missed hits; the three new native probes
each fired 17 times. Trace buffers reported no overruns or dropped events.
Other devices produced valid native readbacks. The test completed, probes were
removed, the RTC alarm was cleared and the original sleep selection restored.

## What the macOS comparison actually measures

**OBSERVED:** Private analysis of the macOS 12.7.6 NHI driver matched its build
identifier and two logging call sites to the existing controlled sleep log.
The `publishPCILinkData` path reads the rootport PMCSR and stores the associated
`TBTPCI_PMCSR` property. It emits the same diagnostic block through two logging
paths; six selected records form three such pairs.

**DERIVED:** Those macOS PMCSR values describe RP05/RP09 rootports, not the NHI
or XHC endpoints measured above. The paired log lines are not two independent
register measurements. A later registry snapshot need not refresh the stored
value. These limits prevent a direct endpoint-register comparison with Linux.

**OBSERVED:** The matching macOS driver contains a conditional `TRPE` path in
`prePCIWake`; its execution during the successful cycle was not established.
Linux traces show the endpoint `_PS0`, `PCED` and `UGIO` calls, but no `TRPE`
call in the inspected resume interval. This is not evidence that Linux must
invoke that method. **HYPOTHESIS:** Differences in platform preparation or PCI
restoration may contribute; the necessary conditions and causal link remain
unproven. No manual firmware call or reset is proposed from this comparison.

## Evidence and publication limits

This table and text are original summaries of private measurements and offline
analysis. Full traces, device identifiers, local paths, firmware, Apple code,
disassembly and proprietary binaries are not included. The experiment has not
been independently reproduced. See [sources and attribution](sources.md).
