#!/usr/bin/env python3
import requests
import json
import os
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

ACCESS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "")
POSTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posts.json")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log.txt")

def log(msg):
    timestamp = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

def create_container(text):
    r = requests.post(
        "https://graph.threads.net/v1.0/me/threads",
        headers=HEADERS,
        data={"media_type": "TEXT", "text": text}
    )
    if not r.ok:
        log(f"API error: {r.status_code} {r.text}")
    r.raise_for_status()
    return r.json()["id"]

def publish(creation_id):
    r = requests.post(
        "https://graph.threads.net/v1.0/me/threads_publish",
        headers=HEADERS,
        data={"creation_id": creation_id}
    )
    if not r.ok:
        log(f"API error: {r.status_code} {r.text}")
    r.raise_for_status()
    return r.json()["id"]

def main():
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        posts = json.load(f)
    now = datetime.now(JST).replace(tzinfo=None)
    changed = False
    for post in posts:
        if post["status"] == "posted":
            continue
        scheduled = datetime.strptime(post["datetime"], "%Y-%m-%d %H:%M")
        if now >= scheduled:
            try:
                creation_id = create_container(post["text"])
                thread_id = publish(creation_id)
                post["status"] = "posted"
                post["posted_at"] = now.strftime("%Y-%m-%d %H:%M:%S")
                post["thread_id"] = thread_id
                changed = True
                log(f"投稿成功: {post['datetime']}")
            except requests.HTTPError as e:
                log(f"投稿失敗: {post['datetime']} - {e} | response: {e.response.text}")
            except Exception as e:
                log(f"投稿失敗: {post['datetime']} - {e}")
    if changed:
        with open(POSTS_FILE, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
