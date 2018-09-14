#!/usr/bin/env python

from config import config
from db import conn

conn.delete("extractor.pending")
conn.delete("extractor.working")
maxId = conn.get("crawler.id")
conn.lpush("extractor.pending", *list(range(1, int(maxId) + 1)))
