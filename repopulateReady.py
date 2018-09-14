#!/usr/bin/env python

from config import config
from db import conn

conn.delete("ready")
maxId = conn.get("crawler.id")
for i in range(1, int(maxId) + 1):
    if conn.hexists("title", i):
        conn.rpush("ready", i) # Can be listed in the main view
