# Sources and attribution

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
included. Original notes and scripts were prepared with AI assistance and checked
against local evidence; independent reproductions are welcome.
