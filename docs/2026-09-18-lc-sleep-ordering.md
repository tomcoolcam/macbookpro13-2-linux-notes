# LC sleep omission and PCI save/restore ordering

Measurements: September 17–18, 2026. Report: September 19, 2026.
This is an experimental result on one MacBookPro13,2, not a general suspend fix.

## Conditions

Arch Linux `7.2.6-arch2-1`, `pcie_port_pm=off`, existing D3cold guards retained.
Direct kernel s2idle with an approximately 120-second RTC wake alarm.
Internal iBridge USB wakeup temporarily disabled, then restored.
The successful September 18 runs omitted the entire `tb_lc_set_sleep` call
for each of the two root switches. This omitted its reads and writes, not just
one selected control bit. A private temporary module performed the omission;
it was removed after each run and is not distributed here.

The NO_D3 experiment module was absent in all three runs below. Its additional
runtime-PM references were therefore absent too. Touch Bar modules were absent.
The attached SSD used a USB-A adapter on a USB-C port and the external XHCI path;
it was not mounted, and the checks only read from it.

## OBSERVED: three successful reduced-intervention runs

| Run | External SSD during sleep | Machine-suspend interval | Result |
| --- | --- | ---: | --- |
| A | Absent | 119.768 s | Monitored PCI identities accessible after resume |
| B | Attached | 119.701 s | PCI identities accessible; SSD read hashes matched |
| C, additional PM phase tracing | Attached | 120.014 s | Same checks passed |

Both NHI and both external XHCI controllers underwent native D3hot transitions
in these runs. Recorded post-write PMCSR values were `0x010b` for NHI and
`0x0103` for XHCI, with successful configuration-access status.
In runs B and C, a direct 256 MiB read before and after sleep produced the same
SHA-256 within each run, with unchanged checked device identity and topology.
This verifies that read sample, not a full-disk integrity check or write workload.

The user reported stable 5.9 W during run B. Measurement location and battery
charge condition were not reconfirmed for that run, so this is not a controlled
power benchmark. No new power measurement was reported for run C.
The experiment module was unloaded and iBridge wakeup restored after each run.
Run C had no trace-buffer overruns, dropped events, or missed kprobes reported.

## OBSERVED: invalid bridge saves follow LC sleep in a failed run

A September 17 failed run retained the normal LC function while applying the
four-controller NO_D3 protection. Both LC calls returned zero. The first
instrumented invalid bridge-save DWORD appeared 50.805 ms and 51.976 ms after
the respective LC return. Both upstream bridges saved an invalid vendor/device
DWORD (`0xffffffff`) before the machine-suspend phase began.

Those intervals measure the first recorded bad values, not the physical
power-off latency. NHI save entry was traced, but its saved DWORD contents
were not captured in that profile. Differences in NO_D3/runtime-PM protection
and wakeup settings limit a direct two-run causal comparison.

With LC omitted, run C captured 16 standard configuration DWORDs for each of
six selected bridges (both upstream bridges and their NHI/XHCI downstream
bridges); none was `0xffffffff`.

## OBSERVED: bridge restoration is later than controller restoration

In run C the six selected bridges entered suspend-late with `state_saved=0`
and cached D0. Both upstream bridges still had those values at suspend-noirq
entry. At resume-noirq entry, all six had `state_saved=1` and cached D0.
Their restore calls occurred in ordinary resume, after the controller restores.

| Restore entry | Milliseconds after machine-suspend end |
| --- | ---: |
| XHCI, second domain | 30.692 |
| XHCI, first domain | 36.659 |
| NHI, first domain | 45.741 |
| NHI, second domain | 48.746 |
| Upstream bridge, first domain | 107.045 |
| Upstream bridge, second domain | 108.841 |

These are software call-entry timings, not proof of hardware acceptance of
every restore write. The successful control demonstrates that late bridge
restoration alone does not imply a failed resume when LC sleep is omitted.

## DERIVED

- Native controller D3hot alone is insufficient to explain the observed failure:
  it succeeded under the documented LC-omission conditions without NO_D3.
- In the failed trace, normal bridge saving was already too late to obtain a
  valid standard header after LC sleep had been requested.
- Skipping LC sleep preserves functionality in these short tests but has not
  demonstrated low-power sleep, D3cold operation, or long-term reliability.

Inspection of the matching installed kernel also shows why an early save is
not a trivial fix: `state_saved` can affect whether the suspend path performs
power preparation, and bridge restore may be deferred when software regards
the device as having stayed in D0. Merely setting that flag earlier would change
more than the snapshot contents.

## HYPOTHESIS and next experiments

LC sleep may invalidate the assumption that a bridge classified as remaining
in D0 retains usable configuration. Correct earlier save data may be necessary,
but insufficient if link/power recovery or restore ordering is also wrong.

The next Linux experiment is a reversible early snapshot, first validated while
awake. Snapshot validity, normal power transitions, and early restoration must
be investigated separately. No such snapshot replacement has been tested yet.
A Boot Camp driver-package inspection is planned as an additional comparison;
there are no Windows test results yet.

Only original, sanitized observations are published. Private traces, firmware,
Apple binaries, and experimental kernel modules are not included.
