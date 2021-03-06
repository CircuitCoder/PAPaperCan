#!/usr/bin/env python

FAKE_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.9 Safari/537.36"

from bs4 import BeautifulSoup
from config import config
from db import conn
from urllib.parse import urljoin
import re
import requests
import time
import traceback

THRESHOLD = 500000
PENDING_EXIT = False

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
    soup = BeautifulSoup(content, features="lxml")

    if any(p.match(uri) for p in targetRe):
        resId = conn.incr("crawler.id")
        print(f"Is a target URI, allocated ID {resId}")

        global THRESHOLD
        if resId >= THRESHOLD:
            global PENDING_EXIT
            PENDING_EXIT = True
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
            continue

        print(f"Working on: {uri}")
        crawl(uri)
        conn.lrem("crawler.working", 0, uri)

        global PENDING_EXIT
        if PENDING_EXIT:
            break

while True:
    failedReqs = conn.lrange("crawler.working", 0, -1)
    conn.delete("crawler.working")
    if len(failedReqs) > 0:
        conn.lpush("crawler.pending", *failedReqs)
        print(f"Recovered: {failedReqs}")

    # TODO: multithreading
    try:
        loop()
        if PENDING_EXIT:
            break
    except Exception as e:
        traceback.print_exception(None, e, e.__traceback__)
        time.sleep(10)
