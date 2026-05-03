# Daily News Aggregator

每日自动汇总《新闻联播》及国内外重点新闻，通过 AI 生成摘要和标签分类，导出为结构化表格。

## 功能

- 自动抓取央视网《新闻联播》每日文字版
- 通过 RSS 获取 BBC、NPR 等国际新闻
- DeepSeek AI 自动生成 50 字以内中文摘要
- 自动打标签：政治、经济、科技、军事、民生、国际、社会、文体
- 按标签分组排序，导出 CSV 和 Excel
- GitHub Actions 每天北京时间 21:00 自动运行

## 数据来源

| 来源 | 类型 | 内容 |
|------|------|------|
| 央视网 (CCTV) | 网页抓取 | 《新闻联播》每日文字版 |
| BBC World | RSS | 国际头条新闻 |
| BBC Top | RSS | 综合热点新闻 |
| NPR World | RSS | 国际新闻 |

## 输出格式

表格列：`日期 | 标签 | 标题 | 摘要 | 来源 | 链接`

输出文件保存在 `data/` 目录下：
- `daily_news.csv` — CSV 格式，GitHub 可直接预览
- `daily_news.xlsx` — Excel 格式，带格式美化

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/iorangejuice12138-lgtm/daily-news.git
cd daily-news
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

```bash
export DEEPSEEK_API_KEY=sk-你的key
```

### 4. 本地运行

```bash
python main.py
```

运行结果会保存在 `data/` 目录下。

## GitHub Actions 自动化

### 配置步骤

1. Fork 或克隆本仓库到你的 GitHub
2. 进入仓库 **Settings** → **Secrets and variables** → **Actions**
3. 添加 Secret：`DEEPSEEK_API_KEY`，值为你的 DeepSeek API Key
4. 去 **Actions** 页面点击 **Run workflow** 手动测试一次

### 定时任务

- 每天北京时间 **21:00** 自动运行
- 结果自动 commit 回仓库
- 也可在 Actions 页面手动触发

## 项目结构

```
daily-news/
├── main.py              # 主入口
├── scraper.py           # 新闻抓取（央视网 + RSS）
├── analyzer.py          # AI 摘要与标签（DeepSeek）
├── exporter.py          # CSV / Excel 导出
├── config.py            # 配置文件
├── requirements.txt     # Python 依赖
├── .github/workflows/
│   └── daily_news.yml   # GitHub Actions 配置
└── data/
    ├── daily_news.csv   # 输出：CSV 表格
    └── daily_news.xlsx  # 输出：Excel 表格
```

## 技术栈

- Python 3.11+
- httpx — HTTP 请求
- BeautifulSoup4 — 网页解析
- feedparser — RSS 解析
- openai (DeepSeek API) — AI 文本分析
- openpyxl — Excel 生成
- GitHub Actions — 定时自动化

## License

MIT
