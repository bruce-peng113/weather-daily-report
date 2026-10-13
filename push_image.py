#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蕉内 · 天气日报 → 飞书群【发图片】
流程：换 token → 用 Chrome 截图看板 → 上传图片拿 image_key → 发到群里
用法：python3 push_image.py
"""

import json
import os
import subprocess
import urllib.request
import datetime

# 加载本地 .env（若存在），方便本地跑时不用手动 export
def _load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
_load_env()

# 敏感凭证从环境变量读取，避免泄露进公开仓库
APP_ID = os.environ.get("FEISHU_APP_ID", "")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
CHAT_ID = os.environ.get("FEISHU_CHAT_ID", "")  # 小机灵鬼 群

BASE = os.path.dirname(os.path.abspath(__file__))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HTML = os.path.join(BASE, "index.html")
PNG = os.path.join(BASE, "dashboard.png")


def get_token():
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode(),
        headers={"Content-Type": "application/json"},
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    if resp.get("code") != 0:
        raise RuntimeError(f"token 获取失败: {resp}")
    return resp["tenant_access_token"]


def screenshot():
    """用 Chrome headless 截图看板"""
    cmd = [
        CHROME, "--headless=new", "--no-sandbox", "--allow-file-access-from-files",
        "--disable-gpu",         f"--screenshot={PNG}", "--window-size=1200,1790",
        "--hide-scrollbars", "--virtual-time-budget=8000",
        f"file://{HTML}?png=1",
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return PNG


def upload_image(token, png_path):
    """上传图片，拿 image_key"""
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    with open(png_path, "rb") as f:
        img_data = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image_type"\r\n\r\nmessage\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="dashboard.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + img_data + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/im/v1/images",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if resp.get("code") != 0:
        raise RuntimeError(f"图片上传失败: {resp}")
    return resp["data"]["image_key"]


def send_image(token, image_key):
    """发图片消息到群"""
    payload = {
        "receive_id": CHAT_ID,
        "msg_type": "image",
        "content": json.dumps({"image_key": image_key}),
    }
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    if resp.get("code") != 0:
        raise RuntimeError(f"发图失败: {resp}")
    return resp


def send_text(token, text):
    payload = {
        "receive_id": CHAT_ID,
        "msg_type": "text",
        "content": json.dumps({"text": text}),
    }
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return resp


if __name__ == "__main__":
    try:
        token = get_token()
        print("✅ token 获取成功")
        screenshot()
        print("✅ 看板截图完成")
        image_key = upload_image(token, PNG)
        print("✅ 图片上传成功，image_key:", image_key)
        # 先发一句说明
        today = datetime.date.today().isoformat()
        send_text(token, f"☀️ 每日天气预警日报 · {today}")
        # 再发图片
        resp = send_image(token, image_key)
        print("✅ 图片已发到群里:", resp.get("code"), resp.get("msg"))
    except Exception as e:
        print("❌ 失败:", e)
