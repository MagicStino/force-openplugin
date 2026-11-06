# OpenPlugin Manager 0.9.0 updates

[Read the manual](GUIDE.md) · [Release notes](RELEASE-0.9.0.md)

The complete Force image includes OpenPlugin Manager 0.9.0, permanent managed-drive startup support, SSH/SFTP and Tracks16. The standalone package updates the manager and matching skin; existing firmware services are still required.

For a controlled standalone upgrade, save your project and extract the full `OpenPlugin-Manager-0.9.0` package. Verify its checksum and transfer the entire directory. From an external SSH shell, run `sh install.sh -y -t /sdcard/Synths`. The installer stops/restarts the application, backs up settings and replaces the PlMg registration. Do not update the running manager from inside itself. Keep binary and skin together.

To remove this portable test/standalone installation, use `sh uninstall.sh -y -t /sdcard/Synths` from that same extracted package. This does not remove the firmware's built-in manager or other plugins. Boot registration restores the firmware manager after reboot. Do not blindly restore old settings over later plugin changes.

A stock drive mounted noexec is not a general standalone installation target. The manager's Storage feature creates a restricted executable view for eligible managed packages and retains its own startup hook in the 0.9.0 image.
