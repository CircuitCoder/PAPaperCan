#!/usr/bin/env python

FAKE_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.9 Safari/537.36"

from config import config
from db import conn
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

targetRe = [re.compile(p) for p in config["filter"]["target"]]
allowedRe = [re.compile(p) for p in config["filter"]["allowed"]]

def crawl(uri):
    resp = requests.get(uri, headers = {
        "Accept-Charset": "utf-8",
        "User-Agent": FAKE_UA,
    })

    if not resp.headers["content-type"].startswith("text/html"):
        print("Incorrect Content-Type")
        return

    content = requests.utils.get_unicode_from_response(resp)
    soup = BeautifulSoup(content, features="html5lib")

    if any(p.match(uri) for p in targetRe):
        resId = conn.incr("crawler.id")
        print(f"Is a target URI, allocated ID {resId}")
        conn.hset("uri", resId, uri)
        conn.hset("raw", resId, content)
        # Notify extractor
        conn.lpush("extractor.pending", resId)

    for link in soup.find_all("a"):
        href = link.get("href")
        if href is None:
            continue

        href = href.split("#")[0]
        href = urljoin(uri, href) # Normalize

        if not any(p.match(href) for p in allowedRe):
            # Not a target
            continue
        if conn.sadd("crawler.stored", href) == 0:
            # Already in store
            continue
        if any(p.match(href) for p in targetRe):
            print(f"Pushing new target {href} to head")
            conn.lpush("crawler.pending.prioritized", href)
        else:
            print(f"Pushing new link {href} to tail")
            conn.lpush("crawler.pending", href)


def loop():
    while True:
        uri = conn.rpoplpush("crawler.pending.prioritized", "crawler.working")
        if uri is None:
            uri = conn.brpoplpush("crawler.pending", "crawler.working").decode("utf-8")
        else:
            uri = uri.decode("utf-8")

        if conn.sadd("crawler.backlog", uri) == 0:
            print(f"{uri} already crawled, skipping")
            return

        print(f"Working on: {uri}")
        crawl(uri)
        conn.lrem("crawler.working", 0, uri)

failedReqs = conn.lrange("crawler.working", 0, -1)
if len(failedReqs) > 0:
    conn.lpush("crawler.pending", *failedReqs)

# TODO: multithreading
loop()
