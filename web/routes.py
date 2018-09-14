from django.http import HttpResponse
from django.conf import settings
from db import conn, wordConn
import os
import math
import json
import time

PAGE_LEN = 10
PREVIEW_LEN = 60

def fetch(request, resId):
    source = conn.hget("source", resId).decode("utf-8")
    rendered = conn.hget("rendered", resId).decode("utf-8")
    title = conn.hget("title", resId).decode("utf-8")
    time = conn.hget("time", resId).decode("utf-8")
    uri = conn.hget("uri", resId).decode("utf-8")

    result = { "source": source, "rendered": rendered, "title": title, "time": time, "uri": uri };

    return HttpResponse(json.dumps(result))

def search(request, kws, page=1):
    beginTime = time.time()

    kws = kws.split("+")
    queryScript = open(os.path.join(settings.BASE_DIR, "web", "scripts", "query.lua")).read()
    start = PAGE_LEN * (page-1)
    end = PAGE_LEN * page -1
    reply = wordConn.eval(queryScript, len(kws), *kws, start, end)

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
