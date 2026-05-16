# BHA Project Sources 路由索引

更新时间：2026-05-16
仓库：`waynehou90-bit/banned`
分支：`json`
索引范围：`project_sources/**`

本文件用于帮助 ChatGPT 历史 Project 在 `project_sources` 下优先选择相关专题包。

## 使用顺序

1. 先读本文件判断专题包。
2. 再读对应专题包的 `README.md` 和 `manifest.json` 判断覆盖范围与 chunk 数量。
3. 最后读对应专题包的 `chunks.md` 提取可引用材料。
4. 每条史实判断必须附带 `citation_id`、`title`、`date`、`source`、`file_path`、`chunk_index`。

## 当前专题包

| 专题包 | 适用问题 | 主要关键词 | 证据文件 |
|---|---|---|---|
| `suyu-taoyong` | 粟裕、陶勇、军队批判、文革军队材料 | 粟裕、陶勇、批粟裕、批判粟裕、首长秘书、军队批判材料、文革军队、军委批判 | `project_sources/suyu-taoyong/chunks.md` |
| `maozedong-pishi` | 毛泽东批示、讲话、指示、文革期间毛的态度 | 毛泽东、毛主席、批示、指示、讲话 | `project_sources/maozedong-pishi/chunks.md` |
| `wenge-zhongyangwenjian` | 文革中央文件、中共中央通知决定、中央文革材料 | 文化大革命、中共中央、通知、决定、中央文革、文件 | `project_sources/wenge-zhongyangwenjian/chunks.md` |
| `renminribao-1966-1976` | 人民日报舆论、官方宣传、报刊定性 | 人民日报、文化大革命、革命委员会、批判、造反派、红卫兵 | `project_sources/renminribao-1966-1976/chunks.md` |
| `hongqi-zazhi` | 红旗杂志、理论定性、路线斗争叙述 | 红旗、文化大革命、阶级斗争、路线斗争、继续革命 | `project_sources/hongqi-zazhi/chunks.md` |
| `zhouenlai-wenge` | 周恩来与文革、国务院、中央文革互动 | 周恩来、总理、中央文革、国务院、文化大革命 | `project_sources/zhouenlai-wenge/chunks.md` |
| `qunzhongzuzhi-zaofanpai` | 群众组织、造反派、红卫兵、革委会 | 群众组织、造反派、红卫兵、革命委员会、群众专政 | `project_sources/qunzhongzuzhi-zaofanpai/chunks.md` |
| `tequan-ganbu-zinv` | 特权、干部子女、走资派、资产阶级法权 | 特权、干部子女、走资派、官僚主义、资产阶级法权 | `project_sources/tequan-ganbu-zinv/chunks.md` |
| `linbiao-jiuyisan` | 林彪、九一三、批林批孔 | 林彪、九一三、913事件、批林批孔、林彪反党集团 | `project_sources/linbiao-jiuyisan/chunks.md` |
| `sirenbang-pipan` | 四人帮、江青、张春桥、姚文元、王洪文、后续批判 | 四人帮、江青、张春桥、姚文元、王洪文、批判四人帮 | `project_sources/sirenbang-pipan/chunks.md` |

## 分析方法入口

- `CHATGPT_PROJECT_INSTRUCTIONS.md`：可直接复制到 Project instructions 的总指令。
- `docs/HISTORY_PROJECT_INSTRUCTIONS.md`：历史 Project 详细接入指令。
- `docs/HISTORICAL_ANALYSIS_METHOD.md`：人民史观、唯物史观、多源鉴别、阶级影响分析方法。

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

不得把单一 chunk 直接等同完整历史事实。涉及争议性历史问题时，先区分材料性质，再依据时间、地点、人物、事件推进、材料矛盾和阶级影响进行判断。

## 证据边界

- `project_sources/*/chunks.md` 是当前 Project 可直接索引的档案材料。
- `project_sources/*/README.md` 和 `manifest.json` 是包级元数据，不是史实正文证据。
- `scripts/`、`app/`、`schema/`、`openapi.yaml` 是工程文件，不作为历史事实证据。
- 如果专题包不存在或 chunk 不足，应说明“当前 Project 已索引材料不足”，并建议新增导出包或调用远程 BHA 检索 API。
