# Google News RSS 爬蟲（含新聞內文）

此範例會爬取 Google News RSS，並進一步打開每篇新聞網址抓取內文段落。

## 安裝

```bash
pip install -r requirements.txt
```

## 執行範例（以 `2330 台積電`）

```bash
python google_news_rss_crawler.py --query "2330 台積電" --limit 5 --output tsmc_news.json
```

## 參數

- `--query`：搜尋關鍵字（預設 `2330 台積電`）
- `--limit`：最多抓幾筆新聞（預設 5）
- `--sleep`：每篇新聞間隔秒數，避免太頻繁請求（預設 1.0）
- `--output`：輸出 JSON 檔案路徑；未指定則直接印到終端

## 輸出欄位

- `title`：標題
- `published`：發布時間
- `source`：來源媒體
- `rss_link`：RSS 提供的連結
- `final_url`：實際跳轉後新聞網址
- `summary`：RSS 摘要
- `content`：解析出的新聞內文（可能因網站反爬機制而為空）

## 注意

1. 各新聞網站的 HTML 結構差異很大，若某些站抓不到內文，建議針對該站增加專屬解析規則。
2. 內文抓取請遵循目標網站服務條款與 robots 規範。
