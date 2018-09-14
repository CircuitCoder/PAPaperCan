#!/usr/bin/env python

from config import config
from db import conn

conn.delete("tokenizer.pending")
conn.delete("tokenizer.working")
maxId = conn.get("crawler.id")
for i in range(1, int(maxId) + 1):
    if conn.hexists("title", i):
        conn.lpush("tokenizer.pending", i)
