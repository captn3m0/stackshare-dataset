"""Download StackShare's tools sitemap.

StackShare is served through Vercel's bot checkpoint, which fingerprints the
TLS handshake (JA3) and blocks plain curl/wget. curl_cffi replays a real
Chrome handshake so the request goes through, and is pip-installable (unlike
the curl-impersonate binary), so it works on stock CI runners.
"""
import os
import sys

from curl_cffi import requests

URL = "https://stackshare.io/sitemap/tools.xml"
OUT = "sitemaps/tools.xml"


def download(url=URL, out=OUT):
    directory = os.path.dirname(out)
    if directory:
        os.makedirs(directory, exist_ok=True)

    response = requests.get(url, impersonate="chrome", timeout=300, stream=True)
    try:
        response.raise_for_status()
        with open(out, "wb") as f:
            for chunk in response.iter_content(chunk_size=1 << 16):
                f.write(chunk)
    finally:
        response.close()

    print(f"wrote {os.path.getsize(out)} bytes to {out}")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else URL
    out = sys.argv[2] if len(sys.argv) > 2 else OUT
    download(url, out)
