# cat-plays-piano

LLM 对比展示项目：固定 prompt `Generate an SVG of a cat playing a piano.`，
收集不同模型 / 不同思考级别的产出，通过 GitHub Pages 按模型分组并排展示。

线上地址：<https://zhaochunqi.github.io/cat-plays-piano/>

只展示作品，不做评分或主观评判。

## 如何添加新条目

优先用本仓库自带的 skill `.agents/skills/cat-plays-piano/SKILL.md`。
手动流程：

1. 用目标模型（及思考级别）跑固定 prompt，拿到纯 SVG。
2. 存为 `entries/<model>-<thinking>-<date>.svg`；模型不支持思考级别时用 `none`。
3. 在 `entries.json` 追加一条：

   ```json
   { "model": "…", "thinking": "…", "date": "YYYY-MM-DD", "file": "entries/…" }
   ```

4. commit + push。

## 数据约定

| 字段 | 说明 |
| --- | --- |
| `model` | 模型 ID，如 `ox-alpha-free` |
| `thinking` | 思考级别 `off` / `low` / `medium` / `high` / `xhigh` / `max`，不支持则 `null` |
| `date` | 生成日期 `YYYY-MM-DD` |
| `file` | 相对仓库根的路径 |

同一模型支持多个思考级别时，每个级别各生成一份，页面内并排对比。
