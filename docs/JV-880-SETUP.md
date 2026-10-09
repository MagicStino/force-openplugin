# JV-880 combined setup (3.9.1.7 source)

Save your project, then open the **JV-880 card** in CATALOG and tap **Install ROMs + plugin** once. This action restarts the app automatically after preparation. Finish or clear unrelated queued changes first. No separate JV tab is needed.

Step 1 checks/stages the five required ROM files, reusing valid existing files or downloading the external archive with its pinned SHA-256. Step 2 downloads and checks the plugin package, then installs the plugin and fills missing ROM files. Existing ROM files and NVRAM are preserved. Download or validation failure stops preparation before installation. Optional expansions remain manual. Existing wrong-size files cause setup to stop rather than overwrite your data.

The [author](https://github.com/sd88me/mpc-vst-jv880/blob/master/docs/ROMS.md) requires your own v1.0.0 dump and warns that v1.0.1 causes emulator CPU traps. The author does not endorse this archive. Its fingerprint identifies the inspected download; it does not independently prove firmware revision, permission to redistribute or hardware compatibility. Use files you are entitled to use. ROMs are not bundled in our images.

| Required file | Bytes |
|---|---:|
| `jv880_rom1.bin` | 32768 |
| `jv880_rom2.bin` | 262144 |
| `jv880_waverom1.bin` | 2097152 |
| `jv880_waverom2.bin` | 2097152 |
| `jv880_nvram.bin` | 32768 |

Destination: `<installed JV-880 folder>/jv880-roms/roms/`. The archive also contains optional SR-JV80-01 through 19, placed manually in `roms/expansions/`. RD-500 files are unrelated and excluded.

Download needs internet and 200 MiB free temporary space. Failures appear on the card and footer; tap the same button to retry. Wrong-size existing files are reported and must be moved aside manually. Arbitrary personal dumps follow the author's manual copy instructions; no general file picker exists.

Pinned archive SHA-256: `f29a3d59bce0e46696d6b618fe8c2d40d2db92459a8e7c2ca114f196cfde7cf4`.

Search uses case-insensitive substrings of titles, authors, IDs, descriptions and tags. For example, `880` finds JV-880; no plugin-specific aliases are added.

Offline tests cover JV-880 identity, combined dispatch, busy feedback, ROM setup on uninstalled cards, copying and preserving files. Combined setup requires hardware testing. The generic red-bar plugin skin issue is separate and unresolved.
