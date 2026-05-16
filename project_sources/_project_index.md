# BHA Project Sources Index

更新时间：2026-05-16
仓库：`waynehou90-bit/banned`
分支：`json`
索引范围：`project_sources/**`

## 用途

本文件是 ChatGPT Project 的索引锚点，用于提示 Project 在重新索引 GitHub 仓库时优先读取 `project_sources` 目录下的 BHA 专题档案包。

`project_sources` 目录用于存放从本地 SQLite/FTS5 数据库导出的专题档案包。每个专题包应保持如下结构：

```text
project_sources/<pack-name>/
├── README.md
├── chunks.md
├── chunks.jsonl
└── manifest.json
```

## 重点索引文件

优先索引顺序：

1. `project_sources/*/chunks.md`：Project 主要检索文本，包含正文 chunk 与可追溯元数据。
2. `project_sources/*/README.md`：专题包命中材料索引。
3. `project_sources/*/manifest.json`：导出参数、查询词、记录数量、生成时间。
4. `project_sources/*/chunks.jsonl`：结构化 chunk 数据，供程序处理。
5. `project_sources/README.md`：专题包目录说明与使用规则。

## 回答规则

当 Project 使用 BHA 专题档案包回答历史问题时，必须优先读取 `chunks.md` 中的条目，并保留以下字段：

- `citation_id`
- `title`
- `author`
- `date`
- `source`
- `url`
- `file_path`
- `document_id`
- `chunk_index`
- `char_range`

材料判断分为三层：

1. **可确认**：多个材料互相印证，且来源链条清楚。
2. **可推断**：材料方向一致，但缺少直接原始文件或完整上下文。
3. **待核实**：只有单一 chunk、来源不完整或存在版本冲突。

不得把单一 chunk 直接等同完整历史事实。涉及争议性历史问题时，先区分材料性质：原始文件、报刊文章、个人讲话/批示、后人整理、回忆录、评论文章。再依据时间、地点、人物、事件推进和阶级影响进行判断。

## 边界说明

ChatGPT Project 只能读取已提交到 GitHub 的文本文件。它不能直接运行本地 SQLite 数据库，也不能自动查询 `db/bha.sqlite`。如果当前专题包没有覆盖用户问题，应说明“当前 `project_sources` 已索引材料不足，需要新增专题导出包或调用远程检索 API”。

本文件用于触发并稳定 Project 对 `project_sources` 的重索引口径。实际重索引动作仍需在 ChatGPT Project 的 GitHub source 设置中执行刷新/重新同步。
