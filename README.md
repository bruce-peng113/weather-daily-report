# 每日天气预警日报（Weather Daily Report）

🌐 [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

面向服装 / 电商运营的多城市天气日报看板，自动拉取天气数据、生成可视化看板、推送图片到飞书群。

> 背景：卖衣服每天要盯天气判断备货和推款，这套工具把「看天气」这件事全自动化——每天早上定时生成当天 36 城天气日报，直接推送到飞书群，一眼看清全国冷暖、降温城市、穿衣建议。

## 功能特性

- 🌡️ **多城市实时天气**：高德天气 API，支持 36+ 核心城市（可按分区自定义）
- 📊 **可视化看板**：中国气象局色阶（蓝冷→红热）、天气 emoji 图标、未来 4 天温度走势折线
- 🗺️ **中国地图热力**：省均温填色 + 虚线省界/国界/九段线（阿里 DataV 官方 GeoJSON）
- 📅 **去年同期对比**：Open-Meteo 免费历史接口，判断今年偏冷还是偏热
- 📱 **飞书图片推送**：自动截图看板，通过飞书机器人发图片到群
- ⏰ **可定时自动化**：配合任意定时任务，每天早上固定时间自动跑

## 效果预览

![看板示例](dashboard.png)

## 快速开始

### 1. 配置凭证

```bash
cp .env.example .env
# 编辑 .env，填入你的高德 Key 和飞书凭证
```

### 2. 安装依赖

无需 pip 安装，仅用 Python 标准库 + Chrome（截图用）。

### 3. 生成看板

```bash
python3 gen_weather.py      # 拉取天气数据，生成 data.json
open index.html             # 浏览器打开看板
```

### 4. 推送到飞书

```bash
python3 push_image.py       # 截图 + 发图片到飞书群
```

## 需要申请的两样东西

| 凭证 | 去哪里申请 |
|------|-----------|
| 高德天气 Key | https://lbs.amap.com/ → 控制台 → 应用管理 → 创建应用 → 添加 Key（选「Web 服务」） |
| 飞书机器人 | 飞书开放平台 → 自建应用 → 添加「机器人」能力 → 开权限 im:message + im:resource + im:chat |

## 目录结构

```
weather-dashboard/
├── index.html          # 看板（数据与版式分离）
├── gen_weather.py      # 拉取数据生成 data.json
├── push_image.py       # 截图 + 推飞书图片
├── push_feishu.py      # 旧版文字推送（备查）
├── china.json          # 中国地图 GeoJSON
├── .env.example        # 凭证模板
└── .gitignore
```

## 自定义

- **改城市清单**：编辑 `gen_weather.py` 顶部的 `REGIONS`（城市名 + adcode）
- **改穿衣建议**：编辑 `gen_weather.py` 顶部的 `CLOTHING` 字典
- **改版式/配色**：编辑 `index.html` 里的 `tempColor()`、`weatherIcon()`、`renderMap()`

## 常见问题

- **高德限流**：免费 Key 有 QPS 限制，脚本已内置重试 + 间隔，无需手动处理
- **截图白屏**：Chrome headless 打开本地文件需加 `--allow-file-access-from-files`（脚本已处理）
- **飞书发不了图**：群「自定义机器人 webhook」不能发图，必须走「自建应用 + im/v1/images 上传」

## 许可

[MIT License](LICENSE)
