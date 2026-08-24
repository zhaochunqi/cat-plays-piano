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

## 提交 PR 示例

没有仓库写权限时，用 fork 方式贡献。下面以新增 `gemini-3.1-pro (extend)` 为例，跑完「如何添加新条目」的 1–4 步后，按此流程提交：

```bash
# 1. 克隆你 fork 后的仓库
git clone https://github.com/<你的用户名>/cat-plays-piano.git
cd cat-plays-piano

# 2. 关联上游，保持与主干同步
git remote add upstream https://github.com/zhaochunqi/cat-plays-piano.git
git fetch upstream

# 3. 基于上游主干新建分支（命名：add-<模型>-<日期>）
git checkout -b add-gemini-3.1-pro-extend-2026-08-25 upstream/main

# 4. 放置 SVG，并编辑 entries.json / rankings.json（字段见「数据约定」）
#    entries/gemini-3.1-pro-extend-2026-08-25.svg

# 5. 提交（message 用 feat: add <模型> [<思考级别>]）
git add entries/gemini-3.1-pro-extend-2026-08-25.svg entries.json rankings.json
git commit -m "feat: add gemini-3.1-pro (extend)"

# 6. 推到你自己的 fork
git push -u origin add-gemini-3.1-pro-extend-2026-08-25

# 7. 打开 PR
#    https://github.com/zhaochunqi/cat-plays-piano/compare
```

> 只提交 `entries/`、`entries.json`、`rankings.json` 等源文件；工具和迁移脚本留在 `/tmp` 或隔离工作区，不要带进 PR。

PR 标题建议与 commit message 一致，描述里贴一句 `note`（效果评测理由）即可；合入后 GitHub Pages 自动重新构建。

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
| `animated` | 可选布尔；为 `true` 时该作品 SVG 含动画（CSS/SMIL），画廊卡片与放大视图显示「▶ 动画」徽章 |

不在 `rankings.json` 榜单内的条目，页面排序时垫底。

## 评分标准

五维各 0–10，**仅用于放大视图的雷达图展示，不参与排序**（排序由 `order` 决定）。核心原则：这一题的判分锚点是「猫到底有没有在弹钢琴」，而不是「画得好不好看」。任何维度的高分都不能弥补「猫没真正在钢琴前弹奏」这一根本缺失。

| 维度 | 判定要点 | 分段参考 |
| --- | --- | --- |
| `cat`（猫） | 猫的形态是否准确、像猫、有神采 | 形态崩坏 1–3；过得去 4–6；准确可爱 7–10 |
| `piano`（钢琴） | 是否出现可辨认、结构完整的钢琴（琴身/琴键/琴腿/谱架齐整） | 无钢琴 0–1；只有键盘板缺琴身或结构错乱 2–6；完整立式 7–8；完整三角钢琴 9–10 |
| `playing`（演奏） | **最关键维度**：猫是否真的在钢琴前、爪子是否明确落在琴键、是否呈弹奏姿态 | 坐/立于琴前、双爪明确落键、姿态正确 8–10；在琴凳/琴前姿态看似正确但爪子与琴键关系含糊或未明确落键 4–5；趴在琴上爪子搭键（非坐姿弹奏）4–5；坐键盘上/琴盖上没碰键、悬浮、纯坐着无交互 ≤ 3 |
| `scene`（场景） | 氛围、构图、附加元素的完整度 | 极简/跑题 1–4；完整有氛围 5–9；最佳 10 |
| `detail`（细节） | 线条、纹理、阴影、附加元素（音符/乐谱/肉垫等）的精细度 | 几乎无细节 0–3；一般 4–6；丰富 7–10 |

> 一致性检查：若某作品的 `playing` 高于 7，其 `note` 必须能支撑「爪子明确落在琴键、呈弹奏姿态」；否则应下调到 4–5 档。这是避免「画得漂亮但没在弹」被高估的主要护栏。

同一模型支持多个思考级别时，每个级别各生成一份，页面内并排对比。
