#!/usr/bin/env python3
"""Submit the current public sitemap URLs to Yandex IndexNow."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
HOST = "rednd.ru"
ORIGIN = f"https://{HOST}"
ENDPOINT = "https://yandex.com/indexnow"
KEY_RE = re.compile(r"[A-Za-z0-9-]{8,128}")


def sitemap_urls() -> list[str]:
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    root = ET.parse(ROOT / "sitemap.xml").getroot()
    urls = [node.text or "" for node in root.findall("s:url/s:loc", ns)]
    if not urls or any(not url.startswith(f"{ORIGIN}/") for url in urls):
        raise ValueError("sitemap contains an empty or foreign URL")
    if len(urls) != len(set(urls)):
        raise ValueError("sitemap contains duplicate URLs")
    if len(urls) > 10_000:
        raise ValueError("IndexNow accepts at most 10,000 URLs per request")
    return urls


def main() -> int:
    key = os.environ.get("INDEXNOW_KEY", "")
    if not KEY_RE.fullmatch(key):
        print("INDEXNOW_KEY must contain 8-128 letters, digits or hyphens", file=sys.stderr)
        return 2
    urls = sitemap_urls()
    payload = json.dumps(
        {
            "host": HOST,
            "key": key,
            "keyLocation": f"{ORIGIN}/{key}.txt",
            "urlList": urls,
        }
    ).encode("utf-8")
    request = Request(
        ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "rednd-indexnow/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            status = response.status
    except HTTPError as exc:
        print(f"IndexNow rejected the request with HTTP {exc.code}", file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"IndexNow request failed: {exc.reason}", file=sys.stderr)
        return 1
    if status not in {200, 202}:
        print(f"IndexNow returned unexpected HTTP {status}", file=sys.stderr)
        return 1
    state = "verified" if status == 200 else "accepted; key verification pending"
    print(f"IndexNow {state}: {len(urls)} sitemap URLs (HTTP {status})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
