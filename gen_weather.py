#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蕉内 · 每日天气预警日报 —— 自动生成脚本
数据源：高德天气 API（免费，Web服务）
输出：data.json（供 index.html 看板渲染）
用法：python3 gen_weather.py
"""

import json
import urllib.request
import urllib.parse
import datetime
import os
import time

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

# 高德天气 Key 从环境变量读取，避免泄露进公开仓库
KEY = os.environ.get("AMAP_KEY", "")
BASE = "https://restapi.amap.com/v3/weather/weatherInfo"
HIST_BASE = "https://archive-api.open-meteo.com/v1/archive"  # 免费历史天气，无需 Key

# 城市 → 经纬度（用于查去年同期历史天气）
COORDS = {
    "哈尔滨": (45.80, 126.53), "长春": (43.88, 125.32), "沈阳": (41.80, 123.43), "大连": (38.91, 121.60),
    "北京": (39.90, 116.41), "天津": (39.08, 117.20), "石家庄": (38.04, 114.51), "太原": (37.87, 112.55), "呼和浩特": (40.82, 111.65),
    "西安": (34.27, 108.95), "兰州": (36.06, 103.83), "银川": (38.49, 106.23), "西宁": (36.62, 101.78), "乌鲁木齐": (43.83, 87.62),
    "南京": (32.06, 118.80), "苏州": (31.30, 120.58), "杭州": (30.27, 120.16), "宁波": (29.87, 121.54),
    "合肥": (31.82, 117.23), "福州": (26.07, 119.30), "厦门": (24.48, 118.09), "济南": (36.65, 117.12), "青岛": (36.07, 120.38),
    "武汉": (30.59, 114.31), "长沙": (28.23, 112.94), "郑州": (34.75, 113.63), "南昌": (28.68, 115.86),
    "广州": (23.13, 113.26), "深圳": (22.54, 114.06), "海口": (20.04, 110.32), "南宁": (22.82, 108.32),
    "成都": (30.57, 104.07), "重庆": (29.56, 106.55), "昆明": (25.04, 102.71), "贵阳": (26.65, 106.63), "拉萨": (29.65, 91.14),
}

# 37 核心城市：分区 → 城市列表（name 用于展示，adcode 用于精确请求）
REGIONS = [
    {"side": "north", "id": 1, "name": "东北", "cities": [
        {"name": "哈尔滨", "adcode": "230100"}, {"name": "长春", "adcode": "220100"},
        {"name": "沈阳", "adcode": "210100"}, {"name": "大连", "adcode": "210200"}]},
    {"side": "north", "id": 2, "name": "华北", "cities": [
        {"name": "北京", "adcode": "110100"}, {"name": "天津", "adcode": "120100"},
        {"name": "石家庄", "adcode": "130100"}, {"name": "太原", "adcode": "140100"},
        {"name": "呼和浩特", "adcode": "150100"}]},
    {"side": "north", "id": 3, "name": "西北", "cities": [
        {"name": "西安", "adcode": "610100"}, {"name": "兰州", "adcode": "620100"},
        {"name": "银川", "adcode": "640100"}, {"name": "西宁", "adcode": "630100"},
        {"name": "乌鲁木齐", "adcode": "650100"}]},
    {"side": "south", "id": 4, "name": "华东", "cities": [
        {"name": "南京", "adcode": "320100"}, {"name": "苏州", "adcode": "320500"},
        {"name": "杭州", "adcode": "330100"}, {"name": "宁波", "adcode": "330200"},
        {"name": "合肥", "adcode": "340100"}, {"name": "福州", "adcode": "350100"},
        {"name": "厦门", "adcode": "350200"}, {"name": "济南", "adcode": "370100"},
        {"name": "青岛", "adcode": "370200"}]},
    {"side": "south", "id": 5, "name": "华中", "cities": [
        {"name": "武汉", "adcode": "420100"}, {"name": "长沙", "adcode": "430100"},
        {"name": "郑州", "adcode": "410100"}, {"name": "南昌", "adcode": "360100"}]},
    {"side": "south", "id": 6, "name": "华南", "cities": [
        {"name": "广州", "adcode": "440100"}, {"name": "深圳", "adcode": "440300"},
        {"name": "海口", "adcode": "460100"}, {"name": "南宁", "adcode": "450100"}]},
    {"side": "south", "id": 7, "name": "西南", "cities": [
        {"name": "成都", "adcode": "510100"}, {"name": "重庆", "adcode": "500100"},
        {"name": "昆明", "adcode": "530100"}, {"name": "贵阳", "adcode": "520100"},
        {"name": "拉萨", "adcode": "540100"}]},
]

# 穿衣建议模板（可在此修改，改完重跑脚本即可）
CLOTHING = {
    "东北": "羽绒服+毛呢，哈尔滨泼水成冰慎行",
    "华北": "早晚外套，中午长袖，昼夜温差 12°+",
    "西北": "厚外套+围巾挡风，西宁、乌鲁木齐夜间近冰点",
    "华东": "江浙沪晚穿毛呢+外套+带伞；闽南短袖 OK；鲁中加薄外套",
    "华中": "长袖+薄外套，郑州回暖 11° 加件",
    "华南": "短袖+防晒，午后的雷雨，出门带伞",
    "西南": "长袖+外套，川黔阴雨湿冷；昆明、拉萨昼夜 15°+ 早晚加衣",
}


def fetch_last_year(city_name, today):
    """拉去年同期（去年同一周）的平均高低温，来自 Open-Meteo 免费历史接口"""
    try:
        lat, lon = COORDS[city_name]
        ly_year = today.year - 1
        start = (today - datetime.timedelta(days=365)).isoformat()
        # 取去年同期前后共 7 天的平均，更稳
        start = (today - datetime.timedelta(days=365) - datetime.timedelta(days=3)).isoformat()
        end = (today - datetime.timedelta(days=365) + datetime.timedelta(days=3)).isoformat()
        params = urllib.parse.urlencode({
            "latitude": lat, "longitude": lon,
            "start_date": start, "end_date": end,
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "Asia/Shanghai",
        })
        with urllib.request.urlopen(f"{HIST_BASE}?{params}", timeout=15) as r:
            hist = json.loads(r.read().decode("utf-8"))
        dmax = hist["daily"]["temperature_2m_max"]
        dmin = hist["daily"]["temperature_2m_min"]
        avg_high = round(sum(dmax) / len(dmax))
        avg_low = round(sum(dmin) / len(dmin))
        return f"{avg_high}/{avg_low}°"
    except Exception as e:
        return None


def fetch(city):
    params = urllib.parse.urlencode({"key": KEY, "city": city["adcode"], "extensions": "all"})
    url = f"{BASE}?{params}"
    # 重试 4 次，遇到限流等待更久
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                data = json.loads(r.read().decode("utf-8"))
            if data.get("info") == "CUQPS_HAS_EXCEEDED_THE_LIMIT":
                time.sleep(1.2)  # 限流，等久一点重试
                continue
            return data
        except Exception:
            if attempt < 3:
                time.sleep(0.8)
            else:
                raise
    time.sleep(0.6)  # 请求间隔，避免触发高德 QPS 限流


def analyze_cities(region):
    """拉取某区域所有城市天气，返回结构化数据 + 区域统计"""
    cities = []
    highs, lows = [], []
    weather_counter = {}
    alerts = []
    for c in region["cities"]:
        try:
            data = fetch(c)
            if "forecasts" not in data or not data["forecasts"]:
                print(f"  [警告] {c['name']} 返回异常: {data.get('info', '')}")
                continue
            fc = data["forecasts"][0]
            cast = fc["casts"][0]  # 当天
            province = fc["province"].rstrip("省").rstrip("市").rstrip("自治区").rstrip("特别行政区")
            high = int(float(cast["daytemp_float"]))
            low = int(float(cast["nighttemp_float"]))
            day_weather = cast["dayweather"]
            night_weather = cast["nightweather"]
            # 未来几天温度走势（高德 casts 含今天~大后天，最多4天）
            trend = []
            for cc in fc["casts"]:
                try:
                    trend.append(int(float(cc["daytemp_float"])))
                except Exception:
                    trend.append(None)
            # 合并早晚天气描述
            weather = day_weather if day_weather == night_weather else f"{day_weather}转{night_weather}"
            weather_counter[day_weather] = weather_counter.get(day_weather, 0) + 1
            if day_weather in ("雨", "雷阵雨", "中雨", "大雨", "暴雨", "雪", "雨夹雪", "小雪", "中雪", "大雪"):
                alerts.append(f"{c['name']}{day_weather}")
            highs.append(high)
            lows.append(low)
            ly = fetch_last_year(c["name"], datetime.date.today())
            cities.append({
                "province": province,
                "name": c["name"],
                "high": high,
                "low": low,
                "weather": weather,
                "lastYear": ly,  # 去年同期 "高/低°"
                "trend": trend,  # 未来几天最高温走势
            })
        except Exception as e:
            print(f"  [警告] 拉取 {c['name']} 失败: {e}")
    if not cities:
        return None
    avg = round(sum(highs) / len(highs), 1)
    summary = {
        "avg": f"{avg}°",
        "high": f"{max(highs)}°",
        "low": f"{min(lows)}°",
        "swing": f"{max(highs)-min(lows)}°+",
        "alert": ("；".join(alerts) if alerts else "无预警，天气平稳"),
    }
    tag_main = sorted(weather_counter.items(), key=lambda x: -x[1])[0][0] if weather_counter else "—"
    return cities, summary, f"{min(lows)}-{max(highs)}° {tag_main}"


def build():
    today = datetime.date.today()
    regions_out = []
    all_highs, all_lows = [], []
    for r in REGIONS:
        print(f"拉取 {r['name']} 区…")
        res = analyze_cities(r)
        if not res:
            continue
        cities, summary, tag = res
        regions_out.append({
            "side": r["side"],
            "id": r["id"],
            "name": r["name"],
            "tag": tag,
            "clothing": CLOTHING.get(r["name"], ""),
            "summary": summary,
            "cities": cities,
        })
        for c in cities:
            all_highs.append(c["high"])
            all_lows.append(c["low"])

    # 找最高/最低温城市（遍历所有已生成的城市）
    highest_city = None
    lowest_city = None
    for r in regions_out:
        for c in r["cities"]:
            if highest_city is None or c["high"] > highest_city["high"]:
                highest_city = c
            if lowest_city is None or c["low"] < lowest_city["low"]:
                lowest_city = c

    output = {
        "meta": {
            "title": "每日天气预警日报",
            "subtitle": "7 大区 · 37 核心城市 · 冷暖一图分",
            "date": today.isoformat(),
            "version": "v7-自动生成",
            "dataSource": "高德实时数据",
        },
        "todaySummary": {
            "highest": {"value": f"{max(all_highs)}°", "city": highest_city["name"] if highest_city else ""},
            "lowest": {"value": f"{min(all_lows)}°", "city": lowest_city["name"] if lowest_city else ""},
            "nationalAvg": f"{round(sum(all_highs+all_lows)/len(all_highs+all_lows))}°",
            "over30": f"{sum(1 for h in all_highs if h >= 30)} 城",
            "legend": ["冷", "热"],
        },
        "regions": regions_out,
        "keyJudgment": {
            "warning": "哈尔滨、长春有雨夹雪，路面结冰；西宁、乌鲁木齐夜间近冰点",
            "noWarning": "其他大部天气平稳",
        },
        "actions": {
            "restock": {"label": "复购", "text": "北方羽绒服+围巾；江浙沪薄毛呢+外套；广州短袖"},
            "wash": {"label": "洗车", "text": "北方大部适合，江浙沪、华南延后"},
            "outdoor": {"label": "裤装、户外", "text": "广州午后有雷雨，选早场；其他大部 OK"},
        },
    }
    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 生成完成 → {outpath}")
    print(f"   日期 {today} · 城市 {len(all_highs)} 个 · 最高 {max(all_highs)}° 最低 {min(all_lows)}°")


if __name__ == "__main__":
    build()
