---
name: cat-plays-piano
description: 给 cat-plays-piano 画廊仓库添加新条目：用固定 prompt「Generate an SVG of a cat playing a piano.」跑目标模型/思考级别，产出纯 SVG 存入 entries/ 并更新 entries.json，本地验证后 commit + push。触发：给 cat-plays-piano 加条目 / 加个模型的猫弹钢琴 / 跑一下某模型 thinking level 对比 / cat-plays-piano 新条目。
---

# cat-plays-piano — 添加画廊新条目

**核心事实**：本 skill 就在本仓库内（`.agents/skills/cat-plays-piano/`），固定 prompt
**逐字**是 `Generate an SVG of a cat playing a piano.`（不要润色、不要加要求）。
entries.json 是唯一数据源，页面自动渲染；只展示作品，不写任何评分或评判。

## 启动前 5 秒

1. 确认用户给了目标 **model ID** 和 **thinking level**（可能多个级别，都要生成）。
2. 确认能访问该 model：pi 里对应 provider/model 可用（不确定先问，别猜 ID）。
3. `cd ~/ghq/github.com/zhaochunqi/cat-plays-piano && git pull --ff-only`，保持干净起点。

## 流程

1. **生成**：用 pi-subagents 起 child（指定 `model` 与 thinking level），task 就是逐字
   prompt，并要求「输出且仅输出 `<svg>…</svg>` 源码」。同一模型多个思考级别 → 每个
   级别各起一个 child，可并行。
2. **落盘**：child 返回的源码存为
   `entries/<model>-<thinking>-<date>.svg`
   - model 用 pi 的 modelId 原样（如 `ox-alpha-free`），`/` 替换成 `-`。
   - 模型不支持思考级别时用 `none`。
   - date 取当天 `YYYY-MM-DD`。
3. **更新 entries.json**：追加一条（保持数组、合法 JSON）：

   ```json
   { "model": "ox-alpha-free", "thinking": "high", "date": "2026-08-24",
     "file": "entries/ox-alpha-free-high-2026-08-24.svg" }
   ```

4. **验证**（全过才算完）：
   - `python3 -c "import xml.dom.minidom; xml.dom.minidom.parse('<file>')"` — SVG 是合法 XML。
   - `python3 -m json.tool entries.json > /dev/null` — JSON 合法。
   - `python3 -m http.server 8741` + curl 三个 200：`/`、`/entries.json`、新 svg 路径，然后关掉 server。
5. **提交**：`git add -A && git commit`，message 形如
   `feat: add <model>-<thinking> entry`；push 到 main（GitHub Pages 自动发布）。

## 边界

- 不改 prompt、不打分、不加主观评语；卡片元数据只有 model / thinking / date。
- SVG 内容不做"美化"或二次编辑——原样收录各模型的产出，歪了也是数据。
- 生成失败或模型拒答：跳过并在汇报里说明，不留半成品文件。
