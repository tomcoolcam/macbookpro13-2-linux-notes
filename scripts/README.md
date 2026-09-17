# Experimental diagnostic recorder

This recorder was developed for one MacBookPro13,2. It changes kernel tracing
state and needs root. Review it before use. `--sleep` initiates a real suspend,
which previously left USB3/Thunderbolt unusable and in another run required a
forced power-off. Disconnect external storage and save your work first.
It is not a repair tool or a general-purpose laptop suspend tester.

Without `--sleep`, it only checks tracing and reads power-supply information:

```sh
sudo python3 scripts/resume-trace.py
```

`--visible-diagnostics` temporarily enables PM messages and changes console
logging, restoring the original settings on normal exit/Python exceptions.
A kernel hang or power-off prevents that cleanup; no persistent boot changes
are installed. The script keeps a dedicated trace instance and removes its
probes on normal completion. Inspect cleanup errors before reusing it.

A sleep experiment requires an explicitly chosen reachable ping target:

```sh
sudo env MBP_PING_TARGET=YOUR_ROUTER_ADDRESS MBP_WIFI_INTERFACE=wlp2s0 \
  python3 scripts/resume-trace.py --sleep --visible-diagnostics
```

Output defaults to `./results`; `MBP_TRACE_DIR` overrides this directory.
The recorder requires kernel BTF, tracefs, matching probe symbols, RTC wakealarm,
`rtcwake`, `iw`, `ping` and systemd tools. Preflight checks are specific to this
machine's PCI addresses, internal USB identity and `pcie_port_pm=off` boot option.
An optional local service called `mbp13-network-resume.service` must not be active.
Sleep bypasses systemd sleep hooks. It arms a 120-second RTC alarm after syncing,
saves durable phase markers, and saves the trace before post-resume PCI reads.
Missing iBridge modules are recorded and their probes omitted.

Limitations: markers and console output cannot guarantee trace survival through
a hard reset. The public PCI wrapper probe does not cover every internal PCI
transition. Collected journals and network output may contain private information;
results are ignored by Git and must be reviewed before sharing.

The private original completed the 2026-09-17 experiment. This public copy changes
output/network configuration; syntax and CLI help were checked, but it has not
been used for another sleep experiment.
