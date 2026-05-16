# Banned Historical Archives 本地数据库

这个仓库用于把 `banned-historical-archives` 资料整理成可检索数据库。当前方案采用 **SQLite + FTS5 全文索引**，优先满足三件事：

1. 本地可复现建库；
2. 能按标题、作者、日期、来源、正文检索；
3. 回答问题时可追溯到原始文件路径和来源链接。

> 说明：本仓库不直接提交原始大文件和生成后的数据库文件。原始资料放在 `data/raw/`，生成数据库放在 `db/`，这些目录默认被 `.gitignore` 排除，避免仓库膨胀。

## 目录结构

```text
.
├── README.md
├── requirements.txt
├── schema/
│   └── sqlite_schema.sql
├── scripts/
│   ├── sync_source.py      # 可选：同步上游 json/txt 分支
│   ├── init_db.py          # 初始化 SQLite 数据库
│   ├── ingest_json.py      # 导入 json/jsonl 文件
│   ├── ingest_text.py      # 导入 txt/md 文件
│   └── search.py           # 命令行检索
├── data/
│   └── raw/                # 本地原始资料，不提交
└── db/                     # 本地数据库，不提交
```

## 快速开始

### 1. 准备环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

当前脚本只使用 Python 标准库，`requirements.txt` 暂时为空，保留给后续向量库、API 服务或分词器扩展。

### 2. 同步上游资料

同步 json 分支：

```bash
python scripts/sync_source.py --branch json --target data/raw
```

如需同步 txt 分支：

```bash
python scripts/sync_source.py --branch txt --target data/raw
```

脚本默认使用：

```text
https://github.com/banned-historical-archives/banned-historical-archives.github.io.git
```

### 3. 初始化数据库

```bash
python scripts/init_db.py --db db/bha.sqlite
```

### 4. 导入资料

导入 json/jsonl：

```bash
python scripts/ingest_json.py --input data/raw/json --db db/bha.sqlite
```

导入 txt/md：

```bash
python scripts/ingest_text.py --input data/raw/txt --db db/bha.sqlite
```

也可以传入任意本地目录，只要里面有 `.json`、`.jsonl`、`.txt` 或 `.md` 文件。

### 5. 检索

```bash
python scripts/search.py --db db/bha.sqlite --query "文革 群众组织" --limit 10
```

输出字段包括：标题、作者、日期、来源、文件路径、chunk 序号和命中文本片段。

## 数据库设计

核心表：

- `documents`：文档级元数据，包括标题、作者、日期、来源、文件路径、来源链接、内容哈希；
- `chunks`：正文切块，默认每块约 1000 字，重叠 120 字；
- `chunks_fts`：SQLite FTS5 全文索引，用于标题、作者、来源、日期、正文联合检索。

导入时会按正文内容哈希去重。同一篇材料若存在多个副本，优先保留第一次导入记录；后续可根据需要改为版本表。

## 给 GPT / RAG 使用的原则

建议把检索层和生成层严格分开：

```text
用户问题
  ↓
SQLite FTS5 精确检索
  ↓
取 top-k chunk + 文档元数据
  ↓
GPT 只基于检索结果回答
  ↓
输出标题、日期、来源、文件路径与证据强度
```

回答历史问题时建议固定证据分级：

1. **可确认**：多个材料互相印证，且来源链条清晰；
2. **可推断**：材料方向一致，但缺少直接原始文件；
3. **待核实**：只有单一材料、来源不完整或存在版本冲突。

不要把单一档案材料直接当作完整历史事实。先说明材料性质，再给出判断边界。

## 后续扩展

后续可以继续加三类能力：

1. `Qdrant / FAISS` 向量索引，用于语义检索；
2. `FastAPI` 服务，把检索接口暴露给 Custom GPT Action 或 MCP；
3. 版本对比表，处理同一材料不同版本、不同校对状态之间的差异。
