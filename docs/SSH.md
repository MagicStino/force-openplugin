# SSH and SFTP: transfer samples and access your device

**OpenSSH 9.6: SSH root access and SFTP file transfers — tested on Force with OpenPlugin 0.7 RC3.** SFTP is a convenient way to copy samples between your computer and device storage.

![OpenPlugin Remote Access beside Catalog and Find, with SSH and SFTP connection settings](../website/assets/remote-access-guide.png)

*AI-generated interface illustration; the device shows its own IP address.*

## Connect

1. Connect your computer and Force/MPC to the same network.
2. Open **PLUGINS → VST → Plugin Manager → REMOTE ACCESS**.
3. Read the device's **IP address** and check that SSH shows **Running**. Tap **Enable SSH** if needed.
4. In your file-transfer app, choose **SFTP** and enter:

| Setting | Value |
|---|---|
| Host | The IP shown on your device |
| Port | `22` |
| Username | `root` |
| Password | `mpc` |

On the first connection, verify the device's host-key fingerprint before saving it.

## Transfer samples

Browse **`/media`** to find internal storage, SD cards and USB drives. Open your chosen sample folder, then upload or download files using your SFTP app. Our tested Force has `/media/MUSIC` and `/media/SSD`; names depend on your connected storage.

Tested on Force. MPC Gen1 has not yet been tested on hardware.

## Open a root terminal

Use an SSH client with the same connection details. From a terminal:

```sh
ssh root@YOUR_DEVICE_IP
```

Enter `mpc` when asked for the password. This gives full root access to the device.

## Turn access off

Tap **Disable SSH** in the Remote Access tab. The disabled setting is saved across reboots; tap **Enable SSH** to turn it back on.

The password is public and shared, and root can change or delete any device file. Use a trusted network and do not expose port 22 to the Internet. Keep sample transfers in your storage folders.
