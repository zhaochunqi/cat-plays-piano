<!--
提交新模型产出前，请先跑完 README「如何添加新条目」的 1–4 步。
本模板用于在 PR 里交代这次贡献的关键信息，方便维护者核对与合并。
-->

## 新增模型产出

- **模型 ID**：<!-- 如 gemini-3.1-pro -->
- **思考级别**：<!-- off / low / medium / high / xhigh / max，不支持则 none -->
- **生成日期**：<!-- YYYY-MM-DD -->
- **SVG 文件**：<!-- entries/<model>-<thinking>-<date>.svg -->

## 效果评测（note）

<!-- 一句话效果评测理由，将展示在放大视图。
     例：夜景三角钢琴+烛光，猫坐琴凳弹奏姿态正确，氛围与细节最完整。 -->

## 五维评分（各 0–10，仅用于雷达图，不参与排序）

| 维度 | 猫 cat | 钢琴 piano | 演奏 playing | 场景 scene | 细节 detail |
| --- | --- | --- | --- | --- | --- |
| 分数 |  |  |  |  |  |

## 提交清单

- [ ] `entries/<model>-<thinking>-<date>.svg` 已放入 `entries/`
- [ ] `entries.json` 已追加一条 `{ "model", "thinking", "date", "file" }`
- [ ] `rankings.json` 已追加一条 `{ "file", "note", "scores", "order" }`（含动画作品加 `"animated": true`）
- [ ] 固定 prompt `Generate an SVG of a cat playing a piano.` 未改动
- [ ] 未带入任何工具脚本（仅提交源文件）

---

提交后 GitHub Pages 会自动重新构建，可在线上地址预览：
<https://zhaochunqi.github.io/cat-plays-piano/>
