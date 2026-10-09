# Remote Access: SSH and SFTP

OpenPlugin 0.7 introduces a **REMOTE ACCESS** tab inside Plugin Manager. Shared images start the dedicated SSH service automatically. Each device generates its own host key and 24-character random password on first startup; neither is included in the downloadable image.

1. Connect the Force or MPC Gen1 to your network.
2. Open **PLUGINS → VST → Plugin Manager → REMOTE ACCESS**.
3. Read the device IP address and tap **Show / Hide password**. Username: **root**, port: **22**.
4. Connect with an SSH client, or choose **SFTP** in a file-transfer app and enter the same details. Verify the host-key fingerprint when first connecting.

SFTP starts in root's home directory. Browse **/media** for mounted internal storage, SD cards and USB drives. These are the device's actual mounts; folder names depend on the storage connected. You can transfer samples into your chosen sample folder. This is full root access, not a samples-only account: editing system files can prevent startup. Use it on a trusted network and do not expose port 22 to the Internet.

**Disable SSH** stops the dedicated service, restores the previous root password hash, and saves the disabled choice across reboots. **Enable SSH** starts it again using the same device-local password. Telnet is not enabled. The password is stored only on the device in a root-readable file under `/data/openplugin/ssh`; do not share a personalized filesystem dump.

The stock root filesystem is read-only. Startup creates a private shadow file on `/data` and bind-mounts it over `/etc/shadow`; disabling restores the original mount. Stock rootfs bytes are not rewritten at runtime. SSH enables password authentication for root. Forwarding is disabled, and SFTP uses OpenSSH's internal server. Existing vendor SSH configuration is not edited. The dedicated unit conflicts with the vendor SSH unit so that two servers do not compete for port 22.

## Optional public-key build

The build script's optional fourth argument still selects the older key-only service instead of automatic password-service startup. Supply an Ed25519 public key, never the private key. The Remote Access Enable button can deliberately switch to the password service.

## Validation status

Host tests cover password generation and permissions, preservation of other accounts, password reuse, persistent disabling, and failed enable rollback. The supplied ARM firmware's OpenSSL and SSH configuration parser are checked under emulation. Native compilation and image structural checks do not prove that login, SFTP, startup or touchscreen controls work on physical hardware. Test on the Force before describing this as hardware verified; MPC Gen1 remains unverified.
