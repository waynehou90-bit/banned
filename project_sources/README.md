# ChatGPT Project 可索引档案包

这个目录用于放置从本地 SQLite/FTS5 数据库导出的专题档案包。

目的：让 ChatGPT Project 在不能运行本地数据库的情况下，仍然能通过 GitHub 仓库索引读取一批经过检索筛选的档案 chunk。

## 生成方式

先在本地生成数据库：

```bash
python scripts/sync_source.py --branch json --target data/raw
python scripts/init_db.py --db db/bha.sqlite
python scripts/ingest_json.py --input data/raw/json --db db/bha.sqlite
```

然后按专题导出：

```bash
python scripts/export_project_pack.py \
  --db db/bha.sqlite \
  --query "文革 群众组织" \
  --pack-name wenge-qunzhongzuzhi \
  --limit 200
```

生成结构：

```text
project_sources/<pack-name>/
├── README.md       # 命中材料索引
├── chunks.md       # Project 主要索引文本
├── chunks.jsonl    # 结构化结果，便于后续程序处理
└── manifest.json   # 导出参数与时间
```

## 提交到 GitHub

```bash
git add project_sources/<pack-name>
git commit -m "Add BHA project source pack: <pack-name>"
git push
```

随后在 ChatGPT Project 的 GitHub 仓库入口重新索引 `waynehou90-bit/banned`。

## 使用规则

Project 回答时必须遵守：

1. 优先引用 `project_sources/*/chunks.md` 中的 `citation_id`。
2. 每条史实判断至少附带 `title`、`date`、`source`、`file_path`、`chunk_index`。
3. 不把单一 chunk 直接当作完整历史事实。
4. 若材料不足，标注“待核实”。
5. 若问题超出已导出专题包范围，提示需要新增导出包或调用远程 API。
