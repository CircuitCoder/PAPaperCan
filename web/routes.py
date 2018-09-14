from django.http import HttpResponse
from django.conf import settings
from db import conn, wordConn, lookupConn
import os
import math
import json
import time
import jieba
import jieba.analyse

PAGE_LEN = 10
PREVIEW_LEN = 60
KEYWORD_COUNT = 5
CANDIDATE_COUNT = 20
RECOMMEND_LEN = 3
RECOMMEND_PREVIEW_LEN = 20

queryScript = open(os.path.join(settings.BASE_DIR, "web", "scripts", "query.lua")).read()
coeffScript = open(os.path.join(settings.BASE_DIR, "web", "scripts", "coeff.lua")).read()

_time = time

def fetch(request, resId):
    b = _time.time()
    # TODO: stash keywords
    source = conn.hget("source", resId).decode("utf-8")
    rendered = conn.hget("rendered", resId).decode("utf-8")
    title = conn.hget("title", resId).decode("utf-8")
    time = conn.hget("time", resId).decode("utf-8")
    uri = conn.hget("uri", resId).decode("utf-8")

    text = conn.hget("text", resId).decode("utf-8")
    kws = jieba.analyse.extract_tags(text, topK = KEYWORD_COUNT)

    candidates = wordConn.eval(queryScript, len(kws), *kws, 0, CANDIDATE_COUNT-1, resId)
    coeffs = [lookupConn.eval(coeffScript, 2, resId, c) for c in candidates];
    coeffs = [c[0] / c[1] for c in coeffs]
    ptrs = list(range(0, len(coeffs)))
    ptrs.sort(key=lambda x: coeffs[x], reverse = True)
    recommends = ptrs[:RECOMMEND_LEN]
    recommends = [candidates[x] for x in recommends]

    titles = conn.hmget("title", *recommends)
    previews = conn.hmget("text", *recommends)

    previews = map(lambda x: x
            .decode("utf-8")[:RECOMMEND_PREVIEW_LEN], previews)
    previews = list(previews)

    recommends = [{ "id": recommends[i].decode(), "title": titles[i].decode("utf-8"), "preview": previews[i] } for i in range(0, len(recommends))]

    print(_time.time() - b)
    result = { "source": source, "rendered": rendered, "title": title, "time": time, "uri": uri, "recommends": recommends };

    return HttpResponse(json.dumps(result))

def search(request, kws, page=1):
    beginTime = time.time()

    kws = kws.split("+")
    start = PAGE_LEN * (page-1)
    end = PAGE_LEN * page -1
    reply = wordConn.eval(queryScript, len(kws), *kws, start, end, -1)

    total = reply[-1]
    if total == 0:
        resp = { "result": [], "pages": 0, "time": time.time() - beginTime }
        return HttpResponse(json.dumps(resp))

    pages = math.ceil(total / PAGE_LEN)
    ids = reply[:-1]

    titles = conn.hmget("title", *ids)
    previews = conn.hmget("text", *ids)

    previews = map(lambda x: x
            .decode("utf-8")[:PREVIEW_LEN], previews)
    previews = list(previews)

    result = [{ "id": ids[i].decode(), "title": titles[i].decode("utf-8"), "preview": previews[i] } for i in range(0, len(ids))]
    endTime = time.time()

    resp = { "result": result, "pages": pages, "time": endTime - beginTime, "total": total };
    return HttpResponse(json.dumps(resp))
