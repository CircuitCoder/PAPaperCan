#!/usr/bin/env python

from config import config
from db import conn

for uri in config['seeds']:
    conn.lpush('crawler.pending', uri)
    conn.sadd('crawler.stored', uri)
    print(f"Seed added: {uri}")
