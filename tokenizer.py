#!/usr/bin/env python

from config import config
from db import conn, wordConn
import jieba
import jieba.analyse
import math

THREAD_COUNT = 2
jieba.enable_parallel(THREAD_COUNT)

def tokenize(resId):
    title = conn.hget("title", resId)
    titleSegs = jieba.cut(title)
    text = conn.hget("text", resId)
    textSegs = jieba.cut(text)

    stash = {}

    for word in titleSegs:
        if word not in stash:
            stash[word] = 0
        stash[word] += 50

    for word in text:
        if word not in stash:
            stash[word] = 0
        stash[word] += 10

    for k, v in stash.items():
        wordConn.zadd(k, resId, math.log(v))

def loop():
    while True:
        resId = conn.brpoplpush("tokenizer.pending", "tokenizer.working").decode("utf-8")
        print(f"Working on {resId}")
        tokenize(resId)
        conn.lrem("tokenizer.working", 0, resId)

failedReqs = conn.lrange("tokenizer.working", 0, -1)
conn.delete("tokenizer.working")
count = len(failedReqs)
if count > 0:
    conn.lpush("tokenizer.pending", *failedReqs)
    print(f"Recovered: {failedReqs}")
loop()
