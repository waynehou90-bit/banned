# 一键做成历史 Project 可查档案库

目标：让 ChatGPT 历史 Project 不依赖本地 SQLite 运行能力，也能直接检索 Banned Historical Archives 的专题档案材料。

实现方式：

```text
本地全量数据库 db/bha.sqlite
  ↓
默认专题配置 packs/default_packs.json
  ↓
批量导出 project_sources/<pack-name>/chunks.md
  ↓
提交 GitHub
  ↓
ChatGPT Project 索引 waynehou90-bit/banned
  ↓
Project 直接查档案包
```

## 1. 本地生成数据库

```bash
git clone https://github.com/waynehou90-bit/banned.git
cd banned

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/sync_source.py --branch json --target data/raw
python scripts/init_db.py --db db/bha.sqlite
python scripts/ingest_json.py --input data/raw/json --db db/bha.sqlite
```

如果需要 txt 分支：

```bash
python scripts/sync_source.py --branch txt --target data/raw
python scripts/ingest_text.py --input data/raw/txt --db db/bha.sqlite
```

## 2. 一键导出默认专题包

```bash
python scripts/export_default_packs.py --db db/bha.sqlite
```

默认会导出：

```text
project_sources/maozedong-pishi/
project_sources/wenge-zhongyangwenjian/
project_sources/renminribao-1966-1976/
project_sources/hongqi-zazhi/
project_sources/zhouenlai-wenge/
project_sources/suyu-taoyong/
project_sources/qunzhongzuzhi-zaofanpai/
project_sources/tequan-ganbu-zinv/
project_sources/linbiao-jiuyisan/
project_sources/sirenbang-pipan/
```

每个专题包包含：

```text
README.md       # 命中材料索引
chunks.md       # 给 ChatGPT Project 索引的正文 chunk
chunks.jsonl    # 结构化结果
manifest.json   # 生成参数
```

## 3. 只导出某几个专题

```bash
python scripts/export_default_packs.py \
  --db db/bha.sqlite \
  --only maozedong-pishi suyu-taoyong
```

## 4. 自定义新增专题

编辑：

```text
packs/default_packs.json
```

新增一项：

```json
{
  "pack_name": "example-topic",
  "query": "关键词1 关键词2 关键词3",
  "limit": 200,
  "source": "",
  "date": ""
}
```

然后重新运行：

```bash
python scripts/export_default_packs.py --db db/bha.sqlite --only example-topic
```

## 5. 提交到 GitHub

```bash
git add project_sources packs docs scripts

git commit -m "Add BHA Project source packs"
git push
```

## 6. 在 ChatGPT 历史 Project 中接入

1. 打开历史 Project。
2. 点击添加 Source / GitHub。
3. 选择 `waynehou90-bit/banned`。
4. 等待仓库索引完成。
5. 把 `docs/HISTORY_PROJECT_INSTRUCTIONS.md` 中的指令复制到 Project instructions。

## 7. Project 中的提问方式

推荐这样问：

```text
请优先检索 waynehou90-bit/banned 仓库 project_sources 下的 BHA 专题档案包。
围绕“粟裕、陶勇、文革期间军队批判材料”检索并回答。
每个判断必须列出 citation_id、title、date、source、file_path、chunk_index。
```

## 8. 重要边界

历史 Project 能查的是：

```text
已导出并提交到 project_sources/ 的专题包
```

不能查的是：

```text
仍只存在于本地 db/bha.sqlite 的全量数据库
```

如果问题超出专题包范围，需要新增导出包，或部署 FastAPI / MCP 做全库实时检索。

## 9. 后续升级路径

```text
阶段 1：Project source pack
适合当前使用，稳定、直接、低成本。

阶段 2：FastAPI + Custom GPT Action
适合远程实时查询全库。

阶段 3：MCP Server / ChatGPT App
适合把检索能力变成 Project 可长期调用的工具。
```
