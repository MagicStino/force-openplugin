# Optional SSH access

The default build does not enable OpenPlugin SSH. To include it, create an
Ed25519 key pair on your computer and supply only its public key:

```sh
ssh-keygen -t ed25519 -f "$HOME/.ssh/openplugin_ed25519"
bash build.sh /path/Force-3.9.1-update.img \
  /path/MPC-3.9.1-Gen1-update.img /path/output \
  "$HOME/.ssh/openplugin_ed25519.pub"
```

After the image has been validated and installed on your device:

```sh
ssh -i "$HOME/.ssh/openplugin_ed25519" root@DEVICE_IP
```

The service generates unique host keys under `/data/openplugin/ssh` and permits
key-only root access. Password login and forwarding are disabled; no Telnet
is added. Root's locked password field becomes `*`, an unusable password,
to permit public-key authentication. Vendor SSH configuration remains intact.

Actual network login is untested. Keep the private key on your computer and
never publish personalized SSH firmware as a generic download.
