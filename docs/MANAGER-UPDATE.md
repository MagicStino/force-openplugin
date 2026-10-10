# Standalone Plugin Manager 0.7.1-rc1 update

This experimental ZIP updates the existing OpenPlugin manager binary and Akai interface together, adding PulyTek's catalog thumbnail. It is for an existing Force/MPC Gen1 OpenPlugin 0.7 installation on 3.9.1. It is not firmware and is not installed through USB Drive Update. Physical-device validation of this standalone update is pending.

## Install over SSH

1. Save your project and verify the downloaded ZIP against its `.sha256` file on your computer. Extract the ZIP; transfer the entire `Plugin-Manager-0.7.1-rc1` folder to device storage with SFTP.
2. Ensure your writable Synths installation location supports executable files and is in the device's SynthContentLocations. The portable installer defaults to `/sdcard/Synths`. Choose a known working Synths location with `-t` when necessary; it rejects noexec mounts. Do not place the plugin on a noexec SSD mount.
3. Connect over SSH using your existing OpenPlugin access. Run as root from the transferred folder:

   ```sh
   sh install.sh
   ```

   For a different working Synths location: `sh install.sh -t /absolute/path/Synths`. The installer verifies package checksums, backs up MPC.settings, stops MPC, installs the manager folder and replaces the existing `PlMg` plugin-list UID exactly once, then restarts MPC. The built-in firmware files, registration and remote-access services remain unchanged. Existing valid portable registration is retained by the boot synchronizer.
4. Load Plugin Manager again and tap **Refresh catalog**. PulyTek should show its thumbnail and rc3 beta download under Effects. The picture is part of the manager's skin; installing PulyTek alone does not update the catalog thumbnail.

Do not update the manager from inside its own running plugin. Use the external SSH shell so the installer survives stopping MPC. Copying a single PNG or just the `.so` is insufficient; binary frame mappings and skin assets must match.

## Roll back

Save first. From the same extracted folder run `sh uninstall.sh` (use the same `-t` path if one was chosen). This removes the portable manager entry, not the original built-in firmware manager. Reboot so the existing OpenPlugin registration service registers the original manager again. Keep the installer-created settings backup. Do not overwrite MPC.settings blindly, as later plugin installations may have changed it.

## Validation and reproduce

Host tests verify the PulyTek frame and existing mappings. The portable installer is tested against isolated settings containing the built-in manager, including repeated installation, checksum integrity and boot synchronizer preservation. ARM load/export checks and generated skin bounds are checked; none establish physical touchscreen/CPU compatibility.

With pinned dependencies under `.deps`, install `requirements-build.txt` and Playwright Chromium as for the native build, then run:

```sh
python3 tools/build_native.py --output build/manager-preview
python3 tools/package_manager.py
```

The ZIP includes complete manager/tooling sources and pinned upstream dependency sources with notices. No firmware image is produced or flashed.
