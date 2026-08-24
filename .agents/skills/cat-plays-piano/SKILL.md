---
name: cat-plays-piano
description: 给 cat-plays-piano 画廊仓库添加新条目：用固定 prompt「Generate an SVG of a cat playing a piano.」跑目标模型/思考级别，产出纯 SVG 存入 entries/ 并更新 entries.json，可选更新 rankings.json 效果排名，本地验证后 commit + push。触发：给 cat-plays-piano 加条目 / 加个模型的猫弹钢琴 / 跑一下某模型 thinking level 对比 / cat-plays-piano 新条目 / 重新排名画廊。
---

# cat-plays-piano — 添加画廊新条目

**核心事实**：仓库在 `~/ghq/github.com/zhaochunqi/cat-plays-piano`，固定 prompt
**逐字**是 `Generate an SVG of a cat playing a piano.`（不要润色、不要加要求）。
`entries.json` 是作品数据源（页面自动渲染）；`rankings.json` 是效果排行榜
（按效果顺序的文件名数组，带 `entries/` 前缀），页面加载后按它动态排序，
榜首常驻首页首展位。

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

4. **排名（可选）**：用户要求排名/更新榜单时，把新作品渲染成图逐张目测
   （headless Chrome 截图联系表即可），按效果（猫的还原度、钢琴结构、
   构图细节）插入 `rankings.json` 合适位置；不要求排名就追加到末尾，
   页面对不在榜内的条目自动垫底。注意文件名要带 `entries/` 前缀，
   与 entries.json 的 `file` 字段完全一致。
5. **验证**（全过才算完）：
   - `python3 -c "import xml.dom.minidom; xml.dom.minidom.parse('<file>')"` — SVG 是合法 XML。
   - `python3 -m json.tool entries.json > /dev/null` — JSON 合法。
   - 改过 rankings.json 时：`python3 -m json.tool rankings.json > /dev/null`。
   - `python3 -m http.server 8741` + curl 三个 200：`/`、`/entries.json`、新 svg 路径，然后关掉 server。
6. **提交**：`git add -A && git commit`，message 形如
   `feat: add <model>-<thinking> entry`；push 到 main（GitHub Pages 自动发布）。

## 边界

- 不改 prompt、不加主观评语；卡片元数据只有 No.N / model / thinking / date。
- 排名与评测理由只进 rankings.json（`[{file, note}]`），不写进 entries.json、不标在 SVG 里。
- SVG 内容不做"美化"或二次编辑——原样收录各模型的产出，歪了也是数据。
- 生成失败或模型拒答：跳过并在汇报里说明，不留半成品文件。
