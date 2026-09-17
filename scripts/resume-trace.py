#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""One instrumented s2idle cycle, or a tracing-only check. No PCI resets."""
import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import time

ROOT = Path(os.environ.get('MBP_TRACE_DIR', 'results')).resolve()
TR = Path('/sys/kernel/tracing')
PCI = Path('/sys/bus/pci/devices')
EXPECTED = {'03:00.0': '86807815', '04:00.0': '8680d315',
            '05:00.0': '8680d215', '06:00.0': '8680d415',
            '79:00.0': '86807815', '7a:00.0': '8680d315',
            '7b:00.0': '8680d215', '7c:00.0': '8680d415',
            '02:00.0': 'e414ba43'}

def run(*args, timeout=30):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return {'exit': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}

def read(p):
    try:
        return p.read_text().strip()
    except OSError as e:
        return str(e)

def dump(p, value):
    p.write_text(json.dumps(value, indent=2) + '\n')

def durable(p, text):
    with p.open('w') as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    fd = os.open(p.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

def phase(out, name):
    # Separate files preserve earlier milestones if a later write blocks.
    durable(out / ('phase-' + name + '.txt'), time.strftime('%FT%T%z') + '\n')
    print('PHASE ' + name, flush=True)

@contextmanager
def diagnostics(out, enabled):
    settings = {
        '/sys/module/printk/parameters/console_suspend': 'N',
        '/sys/power/pm_print_times': '1',
        '/sys/power/pm_debug_messages': '1',
    } if enabled else {}
    original = {p: Path(p).read_text().strip() for p in settings}
    if enabled:
        p = '/proc/sys/kernel/printk'
        original[p] = Path(p).read_text().strip()
        values = original[p].split()
        values[0] = '8'
        settings[p] = ' '.join(values)
    durable(out/'diagnostic-settings-before.json', json.dumps(original, indent=2)+'\n')
    changed = []
    try:
        for p, value in settings.items():
            # Also restore a setting if a write partially succeeds.
            changed.append(p)
            Path(p).write_text(value)
            assert Path(p).read_text().split() == value.split(), p
        yield
    finally:
        errors = {}
        for p in reversed(changed):
            try:
                Path(p).write_text(original[p])
                assert Path(p).read_text().split() == original[p].split(), p
            except Exception as e:
                errors[p] = repr(e)
        durable(out/'diagnostic-settings-restored.json', json.dumps(
            {'errors': errors}, indent=2)+'\n')
        if errors:
            raise RuntimeError('Diagnostic settings restoration failed: '+repr(errors))

def probe_command(command):
    # tracefs rejects the implicit seek used by Python's append file object.
    fd = os.open(TR/'kprobe_events', os.O_WRONLY | os.O_APPEND)
    try:
        os.write(fd, (command+'\n').encode())
    finally:
        os.close(fd)

def snapshot():
    result = {}
    for addr in [*EXPECTED, '00:1c.4', '00:1d.0', '00:1d.3', '00:14.0']:
        p = PCI / ('0000:' + addr)
        d = {a: read(p/a) for a in ['power_state', 'power/runtime_status',
             'firmware_node/path', 'firmware_node/power_state']}
        try:
            with (p/'config').open('rb') as f:
                d['config'] = f.read(4).hex()
        except OSError as e:
            d['config'] = str(e)
        result[addr] = d
    return result

def offsets():
    # Obtain layouts from the running kernel itself, never guess master offsets.
    b = Path('/sys/kernel/btf/vmlinux').read_bytes()
    magic, ver, flags, hlen, to, tl, so, sl = struct.unpack_from('<HBBIIIII', b)
    assert magic == 0xEB9F and ver == 1
    s = b[hlen+so:hlen+so+sl]
    def text(o):
        return s[o:s.find(b'\0', o)].decode()
    found = {}
    p = hlen+to
    while p < hlen+to+tl:
        name, info, size = struct.unpack_from('<III', b, p)
        p += 12
        kind, n = (info >> 24) & 31, info & 65535
        extra = {1:4, 2:0, 3:12, 4:12*n, 5:12*n, 6:8*n, 7:0, 8:0,
                 9:0, 10:0, 11:0, 12:0, 13:8*n, 14:4, 15:12*n,
                 16:0, 17:4, 18:0, 19:12*n}[kind]
        if kind == 4 and text(name) in ('acpi_evaluate_info', 'pci_dev', 'acpi_device', 'device', 'kobject', 'acpi_namespace_node'):
            for j in range(n):
                mn, mt, bit = struct.unpack_from('<III', b, p+12*j)
                if text(mn) in ('full_pathname', 'dev', 'kobj', 'name', 'parent'):
                    assert bit % 8 == 0
                    found[text(name)+'.'+text(mn)] = bit//8
        p += extra
    return found

def preflight():
    assert read(Path('/sys/class/dmi/id/product_name')) == 'MacBookPro13,2'
    assert '[none]' in read(Path('/sys/power/pm_test'))
    assert 'pcie_port_pm=off' in Path('/proc/cmdline').read_text().split()
    assert not read(Path('/sys/class/rtc/rtc0/wakealarm')), 'Existing RTC alarm'
    states = snapshot()
    for addr, identity in EXPECTED.items():
        assert states[addr]['config'] == identity, 'Unhealthy PCI: '+addr
    for p in Path('/sys/bus/usb/devices').iterdir():
        if (p/'idVendor').exists() and not p.name.startswith('usb'):
            assert (read(p/'idVendor'), read(p/'idProduct')) == ('05ac', '8600'), 'External USB: '+p.name
    assert run('ping', '-I', os.environ.get('MBP_WIFI_INTERFACE', 'wlp2s0'), '-c', '3', '-W', '2', os.environ['MBP_PING_TARGET'])['exit'] == 0
    assert run('systemctl', 'is-active', 'mbp13-network-resume.service')['stdout'].strip() != 'active'

def main(test, visible=False):
    assert os.geteuid() == 0
    if test and not os.environ.get('MBP_PING_TARGET'):
        raise SystemExit('Set MBP_PING_TARGET to a reachable host before --sleep')
    ROOT.mkdir(parents=True, exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix='resume-trace-', dir=ROOT))
    out.chmod(0o755)
    (ROOT/'resume-trace-latest.txt').write_text(str(out)+'\n')
    print(out, flush=True)
    group = 'mbpresume'+str(os.getpid())
    inst = TR/'instances'/group
    created = []
    original_sleep = re.search(r'\[([^]]+)\]', Path('/sys/power/mem_sleep').read_text())[1]
    started = time.strftime('%Y-%m-%d %H:%M:%S')
    alarm = False
    result = {'mode': 'sleep' if test else 'probe-check', 'boot_id': read(Path('/proc/sys/kernel/random/boot_id'))}
    o = offsets()
    dump(out/'btf-offsets.json', o)
    pci_name = o['pci_dev.dev'] + o['device.kobj'] + o['kobject.name']
    acpi_name = o['acpi_device.dev'] + o['device.kobj'] + o['kobject.name']
    probes = {
        'aml': f'p:{group}/aml acpi_ps_execute_method path=+0(+{o["acpi_evaluate_info.full_pathname"]}($arg1)):string',
        'aml_ret': f'r128:{group}/aml_ret acpi_ps_execute_method status=$retval:x32',
        'acpi_power': f'p:{group}/acpi_power acpi_device_set_power device=+0(+{acpi_name}($arg1)):string state=$arg2:s32',
        'acpi_power_ret': f'r128:{group}/acpi_power_ret acpi_device_set_power status=$retval:s32',
        'pci_power': f'p:{group}/pci_power pci_set_power_state device=+0(+{pci_name}($arg1)):string state=$arg2:s32',
        'pci_power_ret': f'r128:{group}/pci_power_ret pci_set_power_state status=$retval:s32',
        'ib_suspend': f'p:{group}/ib_suspend apple_ibridge:appleib_suspend',
        'ib_resume': f'p:{group}/ib_resume apple_ibridge:appleib_resume',
    }
    touchbar_modules = {name: Path('/sys/module', name).exists()
                        for name in ('apple_ibridge', 'apple_ib_tb')}
    dump(out/'touchbar-modules.json', touchbar_modules)
    if not touchbar_modules['apple_ibridge']:
        del probes['ib_suspend']
        del probes['ib_resume']
    node = '$arg1'
    parts = []
    for level in range(8):
        parts.append(f'n{level}=+{o["acpi_namespace_node.name"]}({node}):x32')
        node = f'+{o["acpi_namespace_node.parent"]}({node})'
    probes['aml_inner'] = f'p:{group}/aml_inner acpi_ds_begin_method_execution ' + ' '.join(parts)
    try:
        if test:
            preflight()
        inst.mkdir()
        (inst/'tracing_on').write_text('0')
        (inst/'buffer_size_kb').write_text('4096')
        (inst/'trace_clock').write_text('global')
        for name, definition in probes.items():
            probe_command(definition)
            created.append(name)
            (inst/'events'/group/name/'enable').write_text('1')
        for event in ['suspend_resume', 'device_pm_callback_start', 'device_pm_callback_end']:
            (inst/'events/power'/event/'enable').write_text('1')
        dump(out/'probes.json', probes)
        (inst/'tracing_on').write_text('1')
        if test:
            dump(out/'before.json', snapshot())
            (out/'wakeup-before.txt').write_text(read(Path('/sys/kernel/debug/wakeup_sources')))
            Path('/sys/power/mem_sleep').write_text('s2idle')
            with diagnostics(out, visible):
                phase(out, '01-before-sync')
                os.sync()
                phase(out, '02-after-sync')
                # Arm only after the global sync, so it cannot consume the alarm.
                alarm = True
                rtc = run('rtcwake', '-m', 'no', '-s', '120')
                durable(out/'rtc.json', json.dumps(rtc, indent=2)+'\n')
                assert rtc['exit'] == 0 and read(Path('/sys/class/rtc/rtc0/wakealarm'))
                (inst/'trace_marker').write_text('BEFORE_S2IDLE')
                phase(out, '03-before-suspend')
                begin = time.clock_gettime(time.CLOCK_BOOTTIME)
                # Direct kernel suspend deliberately excludes recovery hooks.
                Path('/sys/power/state').write_text('mem')
                result['elapsed_boottime'] = time.clock_gettime(time.CLOCK_BOOTTIME)-begin
                (inst/'trace_marker').write_text('AFTER_S2IDLE')
                (inst/'tracing_on').write_text('0')
                phase(out, '04-suspend-returned')
                # Save the trace before any PCI reads that could themselves hang.
                durable(out/'trace.txt', (inst/'trace').read_text())
                phase(out, '05-trace-saved')
            dump(out/'after.json', snapshot())
            (out/'wake-irq.txt').write_text(read(Path('/sys/power/pm_wakeup_irq')))
            (out/'wakeup-after.txt').write_text(read(Path('/sys/kernel/debug/wakeup_sources')))
        else:
            # Read-only battery query causes ordinary AML evaluations.
            with diagnostics(out, visible):
                phase(out, 'probe-check')
                for p in Path('/sys/class/power_supply').glob('*/uevent'):
                    read(p)
                time.sleep(2)
            (inst/'tracing_on').write_text('0')
        if not (out/'trace.txt').exists():
            durable(out/'trace.txt', (inst/'trace').read_text())
        dump(out/'buffer-stats.json', {p.parent.name:p.read_text() for p in (inst/'per_cpu').glob('cpu*/stats')})
        (out/'kprobe-profile.txt').write_text((TR/'kprobe_profile').read_text())
    except BaseException as e:
        result['error'] = repr(e)
        raise
    finally:
        if inst.exists():
            (inst/'tracing_on').write_text('0')
            if not (out/'trace.txt').exists():
                (out/'trace.txt').write_text((inst/'trace').read_text())
            (inst/'events/enable').write_text('0')
            inst.rmdir()
        for name in reversed(created):
            probe_command(f'-:{group}/{name}')
        if alarm:
            result['rtc_cleanup'] = run('rtcwake', '-m', 'disable')
        Path('/sys/power/mem_sleep').write_text(original_sleep)
        dump(out/'result.json', result)
        os.sync()
    if test:
        dump(out/'wifi-link.json', run('iw', 'dev', os.environ.get('MBP_WIFI_INTERFACE', 'wlp2s0'), 'link'))
        dump(out/'wifi-ping.json', run('ping', '-I', os.environ.get('MBP_WIFI_INTERFACE', 'wlp2s0'), '-c', '5', '-W', '2', os.environ['MBP_PING_TARGET']))
        dump(out/'journal.json', run('journalctl', '-k', '-b', '--since', started, '--no-pager'))
        os.sync()
    print('Finished:', out, flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sleep', action='store_true')
    parser.add_argument('--visible-diagnostics', action='store_true',
                        help='Temporarily enable PM console messages; restore on exit')
    args = parser.parse_args()
    with Path('/run/mbp13-thunderbolt-test.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        main(args.sleep, args.visible_diagnostics)
