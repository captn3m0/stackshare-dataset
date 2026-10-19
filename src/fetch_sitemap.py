"""Download StackShare's tools sitemap.

StackShare is served through Vercel's bot checkpoint, which fingerprints the
TLS handshake (JA3) and blocks plain curl/wget. curl_cffi replays a real
Chrome handshake so the request goes through, and is pip-installable (unlike
the curl-impersonate binary), so it works on stock CI runners.

Datacenter IPs (GitHub runners) get the JS challenge regardless, answered with
HTTP 429 and x-vercel-mitigated: challenge. For that case we fall back to a
headless Chromium (playwright), which solves the challenge like a real browser.
"""
import os
import sys
from urllib.parse import urljoin

from curl_cffi import requests

URL = "https://stackshare.io/sitemap/tools.xml"
OUT = "sitemaps/tools.xml"


class Challenged(Exception):
    pass


def download_with_curl(url, out):
    response = requests.get(url, impersonate="chrome", timeout=300, stream=True)
    try:
        if response.status_code == 429:
            raise Challenged(f"HTTP 429, x-vercel-mitigated={response.headers.get('x-vercel-mitigated')}")
        response.raise_for_status()
        with open(out, "wb") as f:
            for chunk in response.iter_content(chunk_size=1 << 16):
                f.write(chunk)
    finally:
        response.close()


def download_with_browser(url, out):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            # Clear the checkpoint on a tiny page; it reloads itself once solved.
            page.goto(urljoin(url, "/robots.txt"), timeout=180_000)
            page.wait_for_function(
                "!document.title.includes('Vercel Security Checkpoint')", timeout=180_000)
            status, body = page.evaluate(
                "async u => { const r = await fetch(u); return [r.status, await r.text()]; }", url)
        finally:
            browser.close()
    if status != 200 or "<urlset" not in body[:1024]:
        raise RuntimeError(f"browser fetch failed: HTTP {status}: {body[:200]!r}")
    with open(out, "w", encoding="utf-8") as f:
        f.write(body)


def download(url=URL, out=OUT):
    directory = os.path.dirname(out)
    if directory:
        os.makedirs(directory, exist_ok=True)

    try:
        download_with_curl(url, out)
    except Challenged as e:
        print(f"curl_cffi was challenged ({e}), retrying with headless Chromium", flush=True)
        download_with_browser(url, out)

    print(f"wrote {os.path.getsize(out)} bytes to {out}")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else URL
    out = sys.argv[2] if len(sys.argv) > 2 else OUT
    download(url, out)
