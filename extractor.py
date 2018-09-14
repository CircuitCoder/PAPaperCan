#!/usr/bin/env python

from bs4 import BeautifulSoup
from config import config
from db import conn
from datetime import datetime
import traceback
import time
import re

def A2009(content, soup, scripts):
    container = soup.find(id="cntMain")
    if container is None:
        return None

    if container.find(id="lantern") is not None:
        # Is images
        return None

    title = container.select_one("#ArticleTit").get_text()
    infoline = container.select_one("#ArtFrom")
    if infoline is None:
        return None

    acount = len(infoline.select("a"))

    if acount == 3:
        timeStr = infoline.contents[2].replace("\u3000", "").replace("\t", "").replace("\n", "").replace(" ", "")
        time = datetime.strptime(timeStr, u"%Y年%m月%d日%H:%M")
        source = infoline.select("a")[1].get_text()
    elif acount <= 2:
        infoStr = infoline.contents[2]
        segs = infoStr.replace("\u3000", "").replace("\t", "").replace(" ", "").split("\n")
        segs = list(filter(lambda x: len(x) > 0, segs))
        timeStr = segs[0]
        time = datetime.strptime(timeStr, u"%Y年%m月%d日%H:%M")
        source = ' '.join(segs[1:])
    else:
        return None


    textRegion = container.find(id="ArticleCnt");
    if textRegion.select_one("> p") is None:
        # Is video
        return None
    [x.extract() for x in textRegion.select("#Reading")]
    while textRegion.contents[0].name == "p" and textRegion.contents[0].contents and textRegion.contents[0].contents[0].name == "a":
        textRegion.contents[0].extract()
    text = textRegion.get_text()
    rendered = str(textRegion)

    return {
        "title": title,
        "time": time,
        "source": source,
        "text": text,
        "rendered": rendered
    }

def A2010(content, soup, scripts):
    container = soup.find(id="C-Main-Article-QQ")
    if container is None:
        return None

    title = container.select_one("> .hd h1").get_text()
    infoline = container.select_one("> .hd .titBar .info")
    if infoline is None:
        return None

    timeStr = None
    if infoline.select_one("> .pubTime") is None:
        timeStr = infoline.contents[0]
    else:
        timeStr = infoline.select_one("> .pubTime").get_text()
    time = datetime.strptime(timeStr, u"%Y年%m月%d日%H:%M")

    source = infoline.select_one("> .infoCol").get_text()

    textRegion = container.find(id="Cnt-Main-Article-QQ");
    text = textRegion.get_text()
    rendered = str(textRegion)

    return {
        "title": title,
        "time": time,
        "source": source,
        "text": text,
        "rendered": rendered
    }


timePattern = re.compile("var articTime = '(.*)';")
sourcePattern = re.compile("var articSour = '<a[^>]*>(.*)</a>'")
def V2010(content, soup, scripts):
    if soup.find(id="v-Article-QQ") is None:
        return None
    container = soup.find(id="playerIn")
    title = container.select_one("h1").get_text()

    infoline = container.select_one(".info")
    time = None
    source = None
    if infoline is not None:
        timeStr = infoline.contents[0].replace(" ", "").replace("\t", "").replace("\n", "").replace("\u3000", "")
        time = datetime.strptime(timeStr, u"%Y年%m月%d日%H:%M")
        source = infoline.select_one("a").get_text()
    else:
        for script in scripts:
            text = script.get_text();
            if text.find("var articTime") == -1:
                continue
            time = timePattern.search(text).group(1)
            source = sourcePattern.search(text).group(1)
        if time is None:
            raise Exception("Cannot find time and source")
    text = ""
    rendered = ""
    for para in container.select("> p"):
        text += para.get_text();
        rendered += str(para)

    return {
        "title": title,
        "time": time,
        "source": source,
        "text": text,
        "rendered": rendered
    }

def A2018(content, soup, scripts):
    container = soup.select_one("#Main-Article-QQ .qq_article")
    if container is None:
        root = soup.find(id="Main-Article-QQ")
        if root is None:
            return None
        container = soup.find(id = "C-Main-Article-QQ")
    if container is None:
        return None

    title = container.select_one("> .hd h1").get_text()
    infoline = container.select_one("> .hd .qq_bar .a_Info")
    time = None
    source = None
    if infoline is not None:
        timeStr = infoline.select_one("> .a_time").get_text()
        time = datetime.strptime(timeStr, u"%Y-%m-%d %H:%M")
        source = infoline.select_one("> .a_source").get_text()
    else:
        infoline = container.select_one("> .hd .tit-bar .ll")
        if infoline is None:
            return None
        timeStr = infoline.select_one("> .article-time").get_text(" ")
        time = datetime.strptime(timeStr, u"%Y-%m-%d %H:%M")
        sourceElem = infoline.select_one("> [bosszone=\"jgname\"]")
        if sourceElem is None:
            sourceElem = infoline.select_one("> .color-a-1")
        source = sourceElem.get_text()

    textRegion = container.find(id="Cnt-Main-Article-QQ");

    if textRegion.find(id = "backqqcom"):
        textRegion.find(id = "backqqcom").extract()

    text = textRegion.get_text()
    rendered = str(textRegion)

    return {
        "title": title,
        "time": time,
        "source": source,
        "text": text,
        "rendered": rendered
    }

RECIPES = [A2010, A2009, A2018, V2010]

def tryRecipes(content):
    soup = BeautifulSoup(content, features="html5lib")

    scripts = [script.extract() for script in soup.find_all("script")]

    for style in soup.find_all("style"):
        style.extract()
    for video in soup.find_all("video"):
        video.extract()

    for recipe in RECIPES:
        result = recipe(content, soup, scripts)
        if result is not None:
            return result
    return None

def extract(resId):
    content = conn.hget("raw", resId).decode("utf-8")
    try:
        result = tryRecipes(content)
    except:
        raise Exception(f"Errored processing {resId}")
    if result is None:
        return False

    conn.hset("title", resId, result["title"])
    conn.hset("text", resId, result["text"])
    conn.hset("time", resId, result["time"])
    conn.hset("source", resId, result["source"])
    conn.hset("rendered", resId, result["rendered"])
    return result

def loop():
    while True:
        resId = conn.brpoplpush("extractor.pending", "extractor.working").decode("utf-8")
        if extract(resId):
            print(f"Success on {resId}")
            # Notify tokenizer 
            conn.lpush("tokenizer.pending", resId)
            conn.rpush("ready", resId)
        else:
            print(f"Failed on {resId}")
            conn.lpush("extractor.failed", resId)
        conn.lrem("extractor.working", 0, resId)

# failedReqs = conn.lrange("extractor.working", 0, -1)
# conn.delete("extractor.working")
# count = len(failedReqs)
# if count > 0:
#     conn.lpush("extractor.pending", *failedReqs)
#     print(f"Recovered: {failedReqs}")

while True:

    try:
        loop()
    except Exception as e:
        traceback.print_exception(None, e, e.__traceback__)

# print(extract(29365))
