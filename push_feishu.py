#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蕉内 · 天气日报 → 飞书群推送
用法：python3 push_feishu.py
前提：已运行 gen_weather.py 生成 data.json
配置：FEISHU_WEBHOOK 环境变量，或直接改下方 WEBHOOK
"""

import json
import os
import urllib.request

# 飞书群机器人 webhook（在飞书群 → 设置 → 群机器人 → 自定义机器人 里获取）
WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")


def build_text(data):
    """把看板数据拼成飞书可读的富文本"""
    s = data["todaySummary"]
    lines = []
    lines.append(f"☀️ 每日天气预警日报 · {data['meta']['date']}")
    lines.append(f"最高 {s['highest']['value']}（{s['highest']['city']}） · 最低 {s['lowest']['value']}（{s['lowest']['city']}） · 全国均温 {s['nationalAvg']} · 30°+ {s['over30']}")
    lines.append("")
    for r in data["regions"]:
        lines.append(f"【{r['name']}】{r['tag']}")
        city_line = "  ".join(f"{c['name']} {c['high']}°/{c['low']}° {c['weather']}" for c in r["cities"])
        lines.append(city_line)
        lines.append(f"👕 {r['clothing']}")
        lines.append("")
    kj = data["keyJudgment"]
    lines.append(f"⚠️ 预警：{kj['warning']}")
    lines.append(f"✅ 无预警：{kj['noWarning']}")
    lines.append("")
    a = data["actions"]
    lines.append(f"🛒 复购：{a['restock']['text']}")
    lines.append(f"🧽 洗车：{a['wash']['text']}")
    lines.append(f"🏃 户外：{a['outdoor']['text']}")
    return "\n".join(lines)


def send(text):
    payload = json.dumps({"msg_type": "text", "content": {"text": text}}).encode("utf-8")
    req = urllib.request.Request(WEBHOOK, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


if __name__ == "__main__":
    if not WEBHOOK:
        print("❌ 未配置飞书 webhook。请设置环境变量 FEISHU_WEBHOOK，或在本脚本 WEBHOOK 变量填入。")
        exit(1)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json"), encoding="utf-8") as f:
        data = json.load(f)
    text = build_text(data)
    try:
        resp = send(text)
        print("✅ 推送成功:", resp)
    except Exception as e:
        print("❌ 推送失败:", e)
