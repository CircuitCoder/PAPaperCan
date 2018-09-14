from django.http import HttpResponse
from django.conf import settings
from db import conn, wordConn
import os
import math
import json
import time

PAGE_LEN = 10
PREVIEW_LEN = 60

def index(request):
    return HttpResponse("Hello, world.")

def search(request, kws, page=1):
    beginTime = time.time()

    kws = kws.split("+")
    queryScript = open(os.path.join(settings.BASE_DIR, "web", "scripts", "query.lua")).read()
    start = PAGE_LEN * (page-1)
    end = PAGE_LEN * page -1
    reply = wordConn.eval(queryScript, len(kws), *kws, start, end)

    totalLen = reply[-1]
    if totalLen == 0:
        resp = { "result": [], "pages": 0, "time": time.time() - beginTime }
        return HttpResponse(json.dumps(resp))

    pages = math.ceil(totalLen / PAGE_LEN)
    ids = reply[:-1]

    titles = conn.hmget("title", *ids)
    previews = conn.hmget("text", *ids)

    previews = map(lambda x: x
            .decode("utf-8")[:PREVIEW_LEN], previews)
    previews = list(previews)

    result = [{ "id": ids[i].decode(), "title": titles[i].decode("utf-8"), "preview": previews[i] } for i in range(0, len(ids))]
    endTime = time.time()

    resp = { "result": result, "pages": pages, "time": endTime - beginTime };
    return HttpResponse(json.dumps(resp))