# Background and earlier observations

An earlier instrumented sleep attempt required a forced power-off. The operator
could view the working console and a separate status console, and noticed
keyboard input on the status console, but could not type into the working session.
Whether the status clock continued updating was unknown. That status program did
not read stdin, so visible input alone did not prove userspace had resumed.
No post-resume trace survived. A complete kernel hang and a session-only problem
could not be distinguished from that evidence.

The Touch Bar had previously worked with locally adapted iBridge/Touch Bar
modules: the operator confirmed illumination and mode switching. Those modules
were absent after reboot and during the later short s2idle test. This configuration
difference is not proof that the Touch Bar driver caused the earlier hang.

Earlier local notes report working macOS sleep on the same machine and lower
power draw than Linux s2idle. The measurements were not a controlled benchmark;
this repository does not claim a directly comparable efficiency result.

Linux already takes the Darwin ACPI paths on this machine. Adding a Darwin OSI
option is therefore not supported as a fix by the current evidence.
