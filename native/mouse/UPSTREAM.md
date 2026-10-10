# Mouse cursor source

Source: https://github.com/bonsaipanda/MPC-Force-SSH-Firmwares
Pinned commit: 64b1b3785270f923549712597d793cfda606463c
Path: ssh/mouse/src/drm_390

Credits: no3z, Amit Talwar and bonsaipanda; Mockba Mod community.
The source repository supplies the Unlicense, preserved in LICENSE.

OpenPlugin changes restrict initialization to MPC, avoid wall-clock build
strings, and reject a DRM layout whose cursor properties do not match the
upstream 800 x 1280 implementation. Unsupported layouts pass MPC's original
atomic commits through untouched. No stock application binary is patched.
Physical mouse clicks and wheel behavior still require device testing.
