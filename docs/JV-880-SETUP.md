# JV-880 ROM setup (3.9.1.6)

Open the installed **JV-880 card** and tap **Install ROM files** once. There is no separate setup tab or second confirmation tap. The card description and catalog footer report startup, failure and completion; the footer shows download progress. If another task is running, a visible message asks you to wait.

Save your project and unload JV-880 instances before importing. The action downloads the external [community archive](https://archive.org/details/jv880_rompack_v1), checks its pinned SHA-256 and imports only the five base files into the registered portable plugin folder. Existing files, especially user NVRAM, are never overwritten. After completion, close and reload JV-880. Optional expansions remain manual.

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

Offline tests cover real JV-880 catalog identity, single-press job dispatch, busy feedback, non-JV card hiding, copying and preserving files. The archive's five-file import passed locally. Hardware testing remains pending. The generic red-bar plugin skin issue is separate and unresolved.
