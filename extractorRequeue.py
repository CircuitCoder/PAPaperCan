#!/usr/bin/env python

from config import config
from db import conn

failedReqs = conn.lrange("extractor.working", 0, -1)
conn.delete("extractor.working")
count = len(failedReqs)
if count > 0:
    conn.lpush("extractor.pending", *failedReqs)
    print(f"Recovered: {failedReqs}")

failedReqs = conn.lrange("extractor.failed", 0, -1)
conn.delete("extractor.failed")
count = len(failedReqs)
if count > 0:
    conn.lpush("extractor.pending", *failedReqs)
    print(f"Requeued count: {count}")
