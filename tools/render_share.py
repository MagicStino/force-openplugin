#!/usr/bin/env python3
"""Render the Tracks16 social card using an owner-supplied Force photograph.

Requires Playwright and Chromium for PNG output. --html-only writes the card
HTML for preview or rendering with another browser installation.
"""
import argparse
import base64
from pathlib import Path


def share(assets):
    photo = 'data:image/png;base64,' + base64.b64encode(
        (assets / 'manager-0.9/catalog.png').read_bytes()).decode()
    return f'''<!doctype html><html lang="en"><meta charset="utf-8">
<title>MagicStino OpenPlugin 0.9 social card</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#101317;color:#f3f4ef;font-family:Arial,sans-serif}}
.canvas{{width:1200px;height:630px;position:relative;overflow:hidden;padding:46px 50px}}
.brand{{font-size:21px;font-weight:700;letter-spacing:-.5px}}.compat{{position:absolute;right:50px;top:49px;font-size:16px;letter-spacing:1px;color:#a4e5d3}}
h1{{font-size:54px;line-height:1.02;letter-spacing:-2px;margin:44px 0 20px}}.copy{{width:540px}}
.lead{{font-size:23px;color:#a4e5d3;margin:0 0 30px}}.features{{font-size:20px;line-height:1.8;color:#e2e5e5}}
.photo{{position:absolute;right:50px;top:148px;width:485px;margin:0}}.photo img{{display:block;width:100%;border:1px solid #566269;border-radius:10px}}figcaption{{font-size:13px;line-height:1.5;color:#abb6bd;margin-top:12px}}
footer{{position:absolute;left:50px;right:50px;bottom:35px;border-top:1px solid #455159;padding-top:20px;display:flex;justify-content:space-between;font-size:16px;color:#abb6bd}}
</style><div class="canvas"><div class="brand">MagicStino / OPENPLUGIN 0.9</div><div class="compat">OPENPLUGIN MANAGER · AKAI FORCE</div>
<div class="copy"><h1>Browse and install<br>in a breeze.</h1><p class="lead">16 audio tracks + 16 plugin tracks.</p>
<div class="features">A–Z · Newest · Oldest · Popular<br>Move eligible plugins: Internal ↔ SSD<br>Repair plugin skins · SSH / SFTP<br>Fast PNG browsing</div></div>
<figure class="photo"><img src="{photo}" alt="OpenPlugin running on a real Force"><figcaption>Actual screen on the owner’s Force.<br>Full-image hardware acceptance pending.</figcaption></figure>
<footer><span>magicstino.github.io/force-openplugin</span><span>Independent community firmware</span></footer></div></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, default=Path(__file__).resolve().parents[1] / 'website/assets')
    parser.add_argument('--html-only', type=Path, help='Write preview HTML instead of rendering PNGs')
    args = parser.parse_args()
    html = share(args.assets)
    if args.html_only:
        args.html_only.write_text(html)
        return
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1200, 'height': 630}, device_scale_factor=1)
        page.set_content(html)
        page.locator('img').evaluate_all('(xs)=>Promise.all(xs.map(x=>x.decode()))')
        # Update the legacy path too, while metadata uses a fresh cache-safe URL.
        for name in ('share-card-0.9.png', 'share-card.png'):
            page.screenshot(path=str(args.assets / name))
            print(name)
        browser.close()


if __name__ == '__main__':
    main()
