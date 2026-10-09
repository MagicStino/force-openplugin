# Remote Access: SSH and SFTP

RC3 uses the requested shared login **root / mpc**, port **22**. RC2 does not contain this change.

Open **PLUGINS → VST → Plugin Manager → REMOTE ACCESS**. The page shows the current device IP address, port, username, password and actual connection status. **Running** means the local SSH port accepts connections; **Stopped** means it does not. Enable retries startup; Disable stops SSH and saves that choice across reboots.

In an SFTP client, enter the displayed IP, port 22, username root and password mpc. Browse **/media** for mounted internal, SD and USB storage and your sample folders. Access is unrestricted root access. The password is public and shared: use a trusted network and do not expose port 22 to the Internet.

The password hash is included during image construction because the root filesystem is read-only. Host keys remain unique and generated on each device. Telnet and SSH forwarding are disabled. Startup errors are recorded under `/data/openplugin/ssh/error.log`.

Physical startup, login and file transfer still require testing. A successful build or checksum check does not prove safe flashing.
