# Linux setup on the test machine

Recorded on 2026-09-17 from installed packages, configuration files, bootctl and
selected runtime sysfs values. This describes the machine used for this
investigation, not a recommended installation recipe. Configuration files are
reported separately from verified runtime behavior. Personal identifiers,
partition UUIDs, network addresses, SSIDs and credentials are omitted.

## Distribution and relevant packages

Arch Linux, rolling release, x86-64. Running kernel: `7.2.6-arch2-1`.
These are observed package versions, not versions others must install.

| Package | Installed version |
| --- | --- |
| linux | 7.2.6.arch2-1 |
| linux-headers | 7.2.6.arch2-1 |
| linux-firmware | 20260910-2 |
| systemd | 261.3-1 |
| mkinitcpio | 42-1 |
| intel-ucode | 20260812-1 |
| kbd | 2.10.0-1 |
| networkmanager | 1.58.1-1 |
| wpa_supplicant | 2:2.12-1 |
| openssh | 10.5p1-1 |
| ufw | 0.36.2-7 |
| zram-generator | 1.2.1-1 |
| acpica | 20251212-1 |
| nvme-cli | 3.0-1 |

## Boot and storage

- Bootloader: systemd-boot 261.3-1-arch; loader menu timeout 3 seconds.
- Current entry: `arch-linux.efi`, a Type #2 Unified Kernel Image (UKI),
  at `/boot/EFI/Linux/arch-linux.efi`; systemd-stub 261.3-1-arch.
- Secure Boot is reported disabled/unsupported by bootctl on this firmware.
- Internal SSD: root filesystem on partition 3, ext4; Linux EFI System Partition
  on partition 2, vfat mounted at `/boot`. A separate original Apple EFI partition
  remains on partition 1. Identifiers and exact partition sizes are not published.
- Root fstab options: `rw,relatime`; root fsck pass 1. `/boot` is currently mounted
  read-write with restrictive `fmask=0077,dmask=0077`, fsck pass 2.

Sanitized running command line (placeholder is not a usable boot configuration):

```text
root=PARTUUID=<ROOT_PARTITION_ID> zswap.enabled=0 rw rootfstype=ext4 pcie_port_pm=off
```

`pcie_port_pm=off` is an existing resume experiment, not a demonstrated fix.
`zswap.enabled=0` is present; compressed swap is instead configured through
zram-generator, with `[zram0]` and `compression-algorithm = zstd`.

The mkinitcpio linux preset enables only `default`, producing the UKI above.
A fallback path exists in the preset, but `fallback` is not in the enabled preset
list; this does not establish whether an older fallback file exists on disk.

Configured hooks:

```text
base udev autodetect microcode modconf kms keyboard keymap consolefont block filesystems fsck
```

The main configuration has `MODULES=()`, supplemented by
`/etc/mkinitcpio.conf.d/60-applespi.conf`:

```sh
MODULES+=(applespi)
```

## Console, graphics and keyboard

The investigated workflow uses Linux virtual consoles and SSH.
`mbp13-framebuffer.service` sets `/dev/fb0` geometry to 2560×1600, 32 bits per pixel,
before gettys start. i915 is the graphics driver seen in the experiment trace;
this is not a desktop graphics validation.

Relevant `/etc/vconsole.conf` entries:

```ini
FONT=latarcyrheb-sun32
KEYMAP=de-latin1
XKBLAYOUT=de
XKBMODEL=pc105
XKBOPTIONS=terminate:ctrl_alt_bksp
```

The XKB entries are recorded file contents; they do not establish an active
X11/Wayland session. The console uses the keymap and font entries.

`/etc/modprobe.d/applespi.conf` contains:

```text
options applespi iso_layout=1
```

The early module inclusion and existing `modconf` hook put the driver option
into the UKI/initramfs. The UKI was rebuilt during keyboard setup. Current
`/sys/module/applespi/parameters/iso_layout` reads `Y`.
`mbp13-applespi-verify.service` checks keyboard configuration after boot; it is
a verification helper, not the mechanism applying the option.

TTY8 runs a custom status display (`mbp13-codex-status.service`) that refreshes
approximately every five seconds. It uses `StandardInput=null` and is not an
interactive shell. Console switching and visible input there do not alone prove
that the working console or ordinary userspace has resumed.

## Networking

NetworkManager and sshd are enabled. The wireless device is driven by brcmfmac;
its test interface name is `wlp2s0`. Existing module options are:

```text
options brcmfmac feature_disable=0x2000
options cfg80211 ieee80211_regdom=DE
```

These are machine-specific settings, not a claim that the feature mask is needed
on every installation. `DE` reflects the test location and should not be copied
as a universal regulatory setting.

A custom NetworkManager dispatcher calls a local Wi-Fi routing helper on
interface up/down and DHCP-change events. Routing and connection details are
private and omitted. UFW is installed; this snapshot does not publish its rules
or provide a security audit.

A separate USB Ethernet adapter has runtime power/wake rules and a recovery
helper. That external adapter was not attached during the latest sleep test.
The helper selects a known adapter by a private hardware identifier, so its
configuration is not a portable generic network fix.

## Power policy and sleep configuration

The enabled `mbp13-power.service` runs `/usr/local/sbin/mbp13-power`. It checks
for MacBookPro13,2, then requests:

- CPU `powersave` governor and `balance_power` energy preference.
- Internal NVMe `d3cold_allowed=0` and `power/control=on`.
- Runtime power and wake policy for the known USB Ethernet adapter when present.
- A USB/Thunderbolt D3cold guard.

Runtime CPU policy0 confirms `intel_pstate`, `powersave`, `balance_power`.
Other entries here describe what the scripts request; they are not a claim that
every setting was revalidated on every device after the failed resume.

Installed udev rules also request `d3cold_allowed=0` for these Intel device IDs:
`1578`, `15d3`, `15d2`, `15d4`, `9d2f`, and for PCI rootports `00:1c.4` and
`00:1d.0`. The guard repeats the request for accessible matching devices; it
skips devices already inaccessible. Another rule requests retained runtime
power for Apple NVMe `106b:2003`. Comments in these rules express their intended
purpose; they do not prove the protection worked or configure NVMe APST directly.
**The observed Thunderbolt failure occurred despite these existing guard rules.**

Logind drop-in `/etc/systemd/logind.conf.d/60-codex-headless.conf`:

```ini
[Login]
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
HandleLidSwitchDocked=ignore
IdleAction=ignore
```

Closing the lid is therefore not configured to initiate automatic suspend.

Sleep drop-ins are layered. `60-codex-headless.conf` allows suspend, disables
hibernation/hybrid/suspend-then-hibernate, sets `SuspendState=mem` and initially
selects `MemorySleepMode=deep`. The later `70-codex-s2idle-test.conf` resets that
setting and selects `s2idle`:

```ini
[Sleep]
MemorySleepMode=
MemorySleepMode=s2idle
```

The current `/sys/power/mem_sleep` reads `s2idle [deep]`. This is consistent with
a systemd drop-in selecting s2idle when invoked and the diagnostic recorder
restoring the previously selected kernel mode after its direct test.

## Custom services and hooks

| Name | Purpose and observed installation state |
| --- | --- |
| mbp13-power.service | Applies the policy above; enabled |
| mbp13-framebuffer.service | Console framebuffer geometry; enabled |
| mbp13-applespi-verify.service | Post-boot ISO keyboard verification; enabled |
| mbp13-codex-status.service | Noninteractive TTY8 status display; enabled |
| mbp13-network-resume.service | On-demand USB Ethernet recovery, not a general Wi-Fi fix |

System-sleep hooks reapply the power policy after resume, save USB network
state before sleep, and schedule USB Ethernet recovery afterward. These local
helpers are described here but are not distributed as an installable service
bundle in this repository.

## Touch Bar and experiment-specific differences

Touch Bar lighting and mode switching previously worked using locally adapted
upstream modules. At the current inspection, `apple_ibridge` and `apple_ib_tb`
are not loaded, and prior module lookup after reboot could not find them.
There is no persistent modules-load configuration for them. This is an
experimental driver state, not a completed persistent Touch Bar installation.

The [09:22 experiment](2026-09-17-s2idle.md) used this state, selected s2idle
explicitly, and wrote directly to `/sys/power/state`. It bypassed the systemd
sleep hooks described above. PM console logging was temporarily enabled for
that test and restored afterward. No external USB storage was attached.

The configuration snapshot was taken after the experiment; the Thunderbolt/
USB3 device state is already impaired. It must not be used as a healthy baseline
for another sleep cycle. No running configuration was changed to prepare this
page. This is a current-state record, not a reconstruction of every installation
step or a claim of a fully reproducible clean-install recipe.
