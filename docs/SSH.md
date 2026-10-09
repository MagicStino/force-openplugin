# Remote Access: SSH and SFTP

RC3 uses the requested shared login **root / mpc**, port **22**. RC2 does not contain this change.

Open **PLUGINS → VST → Plugin Manager → REMOTE ACCESS**. The page shows the current device IP address, port, username, password and actual connection status. **Running** means the local SSH port accepts connections; **Stopped** means it does not. Enable retries startup; Disable stops SSH and saves that choice across reboots.

In an SFTP client, enter the displayed IP, port 22, username root and password mpc. Browse **/media** for mounted internal, SD and USB storage and your sample folders. Access is unrestricted root access. The password is public and shared: use a trusted network and do not expose port 22 to the Internet.

The password hash is included during image construction because the root filesystem is read-only. Host keys remain unique and generated on each device. Telnet and SSH forwarding are disabled. Startup errors are recorded under `/data/openplugin/ssh/error.log`.

## Verified on the owner's Force — 10 October 2026

- SSH connection returned OpenSSH 9.6.
- Password login as `root` with `mpc` succeeded; a read-only command confirmed root access and listed mounted storage.
- A 64-byte temporary file was uploaded by SFTP, downloaded again, and verified byte-for-byte with matching SHA256.
- The temporary remote file was removed and its absence confirmed.
- The connected device exposed `/media/MUSIC`, `/media/SSD` and other mounts. Names vary by device and connected storage.

The transfer test used `/tmp` to avoid changing sample libraries. It proves SFTP file transfer on this Force, not transfers into every storage volume. Disable/re-enable, reboot persistence, long transfers and physical MPC Gen1 operation remain untested. These results do not prove safe flashing on other devices.
