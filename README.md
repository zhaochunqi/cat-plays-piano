# cat-plays-piano

LLM 对比展示项目：固定 prompt `Generate an SVG of a cat playing a piano.`，
收集不同模型 / 不同思考级别的产出，通过 GitHub Pages 按模型分组并排展示。

线上地址：<https://zhaochunqi.github.io/cat-plays-piano/>

作品按 `rankings.json` 的 `order` 键排序；点击图片放大可查看该作品的效果评测理由（note），以及五维评分雷达图（猫 / 钢琴 / 演奏 / 场景 / 细节，各 0–10）。

## 如何添加新条目

优先用本仓库自带的 skill `.agents/skills/cat-plays-piano/SKILL.md`。
手动流程：

1. 用目标模型（及思考级别）跑固定 prompt，拿到纯 SVG。
2. 存为 `entries/<model>-<thinking>-<date>.svg`；模型不支持思考级别时用 `none`。
3. 在 `entries.json` 追加一条：

   ```json
   { "model": "…", "thinking": "…", "date": "YYYY-MM-DD", "file": "entries/…" }
   ```

4. 在 `rankings.json` 追加一条 `{ "file", "note", "scores", "order" }`（见下「数据约定」）。

5. commit + push。

## 数据约定

### `entries.json`（每条作品元信息）

| 字段 | 说明 |
| --- | --- |
| `model` | 模型 ID，如 `ox-alpha-free` |
| `thinking` | 思考级别 `off` / `low` / `medium` / `high` / `xhigh` / `max`，不支持则 `null` |
| `date` | 生成日期 `YYYY-MM-DD` |
| `file` | 相对仓库根的路径 |

### `rankings.json`（排序与评分）

| 字段 | 说明 |
| --- | --- |
| `file` | 对应 `entries.json` 的 `file` |
| `note` | 效果评测理由（一句话，点击作品放大时展示） |
| `scores` | 五维评分 `{ cat, piano, playing, scene, detail }`，各 0–10；仅用于放大视图的雷达图展示，**不参与排序** |
| `order` | fractional 排序键，升序越小越靠前（No.1）；改排名只改此值即可（插在中间写 `15.37`），无需手动挪数组、无需脚本 |

不在 `rankings.json` 榜单内的条目，页面排序时垫底。

同一模型支持多个思考级别时，每个级别各生成一份，页面内并排对比。
