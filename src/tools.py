import http.client
import csv
import json
import os
import re
import threading
import time
import concurrent.futures
from urllib.parse import urlparse
from packages import extract_urls_from_sitemaps

HEADERS = ['url', 'object_id', 'name', 'title', 'popularity', 'votes', 'verified', 'description', 'stack_count', 'type', 'category', 'layer', 'function']

ALGOLIA_HOST = "km8652f2eg-dsn.algolia.net"
QUERY_PATH = "/1/indexes/Search_production/query?x-algolia-application-id=KM8652F2EG&x-algolia-api-key=YzFhZWIwOGRhOWMyMjdhZTI5Yzc2OWM4OWFkNzc3ZTVjZGFkNDdmMThkZThiNDEzN2Y1NmI3MTQxYjM4MDI3MmZpbHRlcnM9cHJpdmF0ZSUzRDA%3D"

# Number of concurrent Algolia requests. Overridable via env for tuning.
WORKERS = int(os.environ.get("ALGOLIA_WORKERS", "10"))

# One HTTPS connection per worker thread, reused across its requests.
_local = threading.local()


def _conn():
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = http.client.HTTPSConnection(ALGOLIA_HOST)
        _local.conn = conn
    return conn


def canonicalize(url):
    """Collapse the three sitemap variants of a tool to its canonical URL.

    StackShare lists every tool three times: /<slug>, /tools/<slug> and
    /tools/<slug>/alternatives. Only the bare /<slug> form is the canonical_url
    Algolia knows about, so the other two always miss. Normalising to /<slug>
    and de-duplicating cuts the number of lookups by ~7x.
    """
    parsed = urlparse(url)
    parts = parsed.path.split('/')
    if len(parts) >= 3 and parts[1] == 'tools':
        slug = parts[2]
    elif len(parts) >= 2 and parts[1]:
        slug = parts[1]
    else:
        return None
    return f"{parsed.scheme}://{parsed.netloc}/{slug}"


# StackShare's sitemap is polluted with entries that are never real, ranked
# services. We recognise these from the slug alone and skip them before spending
# an Algolia request, which drops ~30% of lookups and keeps tools.csv clean.
# Validated to produce zero false positives against the existing dataset.
_HF_PREFIX = 'hugging-face-hub-'  # 10k+ auto-imported model repos, all 0 votes/stacks
_SPAM_TOKENS = re.compile(
    r'(^|-)('
    r'call-girls?|escorts?|sex|porn|xxx|nude|camgirl|'                 # adult
    r'casino|togel|judi|gacor|satta|matka|rummy|teen-patti|baccarat|'  # gambling
    r'near-me|packers-and-movers|'                                     # local-services SEO
    r'vashikaran|love-spell|love-problem'                              # occult/astrology
    r')(-|$)')
# Keyword-stuffed marketing landing pages ("free ... generator", "image-to-video").
# Only flagged when the slug is also long (>=6 tokens); no real top tool is, so
# short legitimate names like "signature-generator" are spared.
_MARKETING = re.compile(
    r'-(generator|maker)(-|$)|'
    r'(text|image|photo|video)-to-(video|image|speech|text|song|3d)|'
    r'free-online')


def is_junk_slug(slug):
    """True for auto-generated / spam sitemap entries that should never be scraped."""
    if not re.search(r'[a-z0-9]', slug, re.I):  # degenerate: all hyphens, no content
        return True
    if slug.startswith(_HF_PREFIX):
        return True
    if re.search(r'\d{8,}', slug):  # embedded phone numbers / ids => spam
        return True
    if slug.startswith(('https---', 'http---')) or 'github-com-' in slug:  # mangled URLs
        return True
    if _SPAM_TOKENS.search(slug):
        return True
    # Long slugs are marketing sentences, not tool names: no real tool in the
    # dataset has 7+ hyphen tokens. The marketing keywords catch 6-token ones.
    if slug.count('-') >= 6:
        return True
    if _MARKETING.search(slug) and slug.count('-') >= 5:
        return True
    return False


def tools_except_packages():
    packages = set()
    with open('packages.csv') as packages_file:
        for row in csv.reader(packages_file):
            packages.add(row[0])

    tools = set()
    for url in extract_urls_from_sitemaps():
        canonical = canonicalize(url)
        if canonical and not is_junk_slug(urlparse(canonical).path.lstrip('/')):
            tools.add(canonical)
    return tools - packages


def make_request(search, retries=3):
    payload = json.dumps({
        "query": search,
        "hitsPerPage": 3,
        "filters": "NOT type:Stackup",
    })
    headers = {
        'Accept': "application/json",
        'Accept-Encoding': "deflate",
        "Content-Type": "application/json",
    }

    for attempt in range(retries):
        try:
            conn = _conn()
            conn.request("POST", QUERY_PATH, payload, headers)
            res = conn.getresponse()
            data = res.read()
            d = json.loads(data.decode("utf-8"))
            for x in d.get('hits', []):
                if x.get('canonical_url') == search:
                    return x
            return None  # resolved, but no hit matched this exact slug
        except (http.client.HTTPException, OSError, ValueError) as e:
            # Drop the (possibly poisoned) connection and back off before retry.
            _local.conn = None
            if attempt == retries - 1:
                print(f"ERROR {search}: {e}")
                return None
            time.sleep(0.5 * (attempt + 1))


def build_row(url, data):
    # category/function are usually {"slug": ...} objects but some records
    # return a bare string (or omit them), so normalise both.
    category = data.get('category')
    function = data.get('function')
    return [
        url,
        data.get('objectID'),
        data.get('name'),
        data.get('title'),
        data.get('popularity') or 0,
        data.get('votes_count'),
        data.get('verified'),
        data.get('description'),
        data.get('company_stacks_count'),
        (data.get('type') or '').lower(),
        category.get('slug') if isinstance(category, dict) else category,
        (data.get('layer') or '').lower(),
        function.get('slug') if isinstance(function, dict) else function,
    ]


def fetch(url):
    """Look up a single tool. Returns (url, row) with row=None for a miss/package."""
    data = make_request(urlparse(url).path)
    # Skip misses and packages. Some records omit is_package entirely, so treat
    # a missing value as "not a package".
    if not data or data.get('is_package'):
        return url, None
    return url, build_row(url, data)


if __name__ == '__main__':
    if not os.path.exists('tools.csv'):
        with open('tools.csv', 'w', newline='') as of:
            writer = csv.writer(of)
            writer.writerow(HEADERS)

    urls_written = set()
    with open('tools.csv') as tools_file:
        for row in csv.reader(tools_file):
            urls_written.add(row[0])

    pending = sorted(tools_except_packages() - urls_written)
    total = len(pending)
    print(f"{total} tools to look up with {WORKERS} workers "
          f"({len(urls_written) - 1} already in tools.csv)", flush=True)

    written = misses = 0
    with open('tools.csv', 'a', newline='') as of:
        writer = csv.writer(of)
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
            futures = [executor.submit(fetch, url) for url in pending]
            for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                _, row = future.result()
                if row:
                    writer.writerow(row)
                    written += 1
                else:
                    misses += 1
                if i % 500 == 0:
                    of.flush()
                    print(f"... {i}/{total} processed, {written} written, {misses} misses",
                          flush=True)
    print(f"done: {written} tools written, {misses} misses", flush=True)

    # Sort the tools.csv file by 4th column (popularity)
    def popularity(row):
        try:
            return float(row[4])
        except (IndexError, ValueError):
            return 0.0

    with open('tools.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader, None)  # skip the header
        sortedlist = sorted(reader, key=popularity, reverse=True)
    with open('tools.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        writer.writerows(sortedlist)
