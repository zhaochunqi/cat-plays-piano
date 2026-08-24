---
name: cat-plays-piano
description: >
  用于维护 cat-plays-piano（LLM SVG 对比画廊）项目的技能。固定 prompt 为
  "Generate an SVG of a cat playing a piano."，收集各模型/思考级别的产出，
  经 GitHub Pages 并排展示并按效果排名。在以下场景使用：新增条目、修改
  rankings.json（排序/评分）、调整 index.html 的画廊或放大视图、调试雷达图、
  本地预览。编码了 rankings.json 的 {file, note, scores, order} 约定与
  fractional indexing 排序规则。
---

# cat-plays-piano

LLM 产出对比画廊。固定 prompt，收集不同模型（及思考级别）的纯 SVG 产出，
按模型分组并排展示，并带主观效果评测与五维雷达图。

线上：<https://zhaochunqi.github.io/cat-plays-piano/>

## 固定 prompt（一字不改）

```
Generate an SVG of a cat playing a piano.
```

## 新增一条目

1. 用目标模型（及思考级别）跑上面固定 prompt，拿到**纯 SVG**。
2. 存为 `entries/<model>-<thinking>-<date>.svg`；模型不支持思考级别时用 `none`。
3. 在 `entries.json` 追加：
   ```json
   { "model": "…", "thinking": "…", "date": "YYYY-MM-DD", "file": "entries/…" }
   ```
4. 在 `rankings.json` 追加一条（见下）。
5. commit + push（GitHub Pages 自动构建）。

## rankings.json 约定（核心）

每条对象：

```json
{
  "file": "entries/<model>-<thinking>-<date>.svg",
  "note": "一句话效果评测理由，放大视图展示",
  "scores": { "cat": 0, "piano": 0, "playing": 0, "scene": 0, "detail": 0 },
  "order": 1
}
```

- **`order`**：fractional 排序键，升序越小越靠前（No.1）。改排名只改这一个值，
  无需手动挪数组、无需脚本。插在中间写小数即可，例如插在 #15 与 #16 之间写 `15.37`。
- **`animated`**：可选布尔；`true` 表示 SVG 含动画（CSS `@keyframes` / SMIL `<animate>`）。画廊卡片与放大视图显示「▶ 动画」徽章，仅作标注、不影响排序与评分。
- **`scores`**：五维各 0–10，仅用于放大视图的 Dota 风格雷达图展示，**不参与排序**（排序由 `order` 决定）。
  维度含义：`cat`=猫、`piano`=钢琴、`playing`=演奏、`scene`=场景氛围、`detail`=细节。
  完整分段标准见下方「评分标准」章节。
- **`note`**：点击作品放大时展示的评测理由。**必须与实际渲染图一致**——若原 note 与渲染结果不符
  （如误写"缺琴身"但实际有琴身、夸"姿态正确"实际不像在弹），应据实改写，不要保留错误描述。
- 不在 `rankings.json` 榜单内的条目，页面排序时垫底（order 视为无穷大）。

## 评分标准（判分锚点）

这一题的核心是「猫到底有没有在弹钢琴」，而不是「画得好不好看」。判分前**必须先用 resvg 把 SVG 渲染成 PNG 肉眼核对**，不能只看 `note` 文字——`note` 本身也可能写错（hy3-high 曾把"有琴身"误写成"只有键盘板缺琴身"；又曾因"圆头+小三角耳+纯土黄"画得形似鼠/仓鼠却被评成猫 9 分）。

| 维度 | 判定要点 | 分段 |
| --- | --- | --- |
| `cat` | 猫形态是否准确、像猫、有神采 | 崩坏/像鼠 1–3；过得去 4–6；准确可爱 7–10 |
| `piano` | 是否出现可辨认、结构完整的钢琴（琴身/琴键/琴腿/谱架齐整） | 无钢琴 0–1；仅键盘板缺琴身或结构错乱 2–6；完整立式 7–8；完整三角 9–10 |
| `playing` | **最关键维度**：猫是否真在钢琴前、爪子明确落键、呈弹奏姿态 | 坐/立琴前、双爪明确落键、姿态正确 8–10；姿态对但爪子与琴键关系含糊/未落键、或趴弹 4–5；坐键盘/琴盖上没碰键、悬浮、纯坐无交互 ≤3 |
| `scene` | 氛围、构图、附加元素完整度 | 极简/跑题 1–4；完整有氛围 5–9；最佳 10 |
| `detail` | 线条、纹理、阴影、音符等精细度 | 几乎无 0–3；一般 4–6；丰富 7–10 |

**护栏 1（落键事实）**：`playing>7` 必须有渲染图/事实支撑「爪子明确落键」，否则下调到 4–5。这防止「画得漂亮但没在弹」被高估。

**护栏 2（姿态协调）**：`playing` 不只看爪子是否挨着键，关键看猫是否呈**正常的弹钢琴姿势**——面向键盘、坐琴凳/琴前、双爪自然落键、身体位置能顺理成章够到键（不要求绝对居中，略偏可接受，但姿态须读得出「在弹琴」）。坐侧面、身子转向别处伸手够正面键、爪子悬空在键上方 20px+ 的，不算正常弹奏，落 4–5 档；坐侧面却伸手够正面键（位置与姿势冲突）压到 ≤3。

**审美不忽略**：`cat` / `scene` / `detail` 衡量「画得好不好看」，是本画廊核心乐趣。`playing` 只锚定排序地板，头部名次主要由此三维审美拉开。给「好看且真在弹」打高分、与「丑但勉强在弹」拉开差距，正确且必要。

## index.html 行为

- 排序：`order` 升序；缺失 order 的条目垫底。
- 放大视图（`setViewer`）：展示 note + 五维雷达图（`radarSVG()`）+ 综合评分 `total/50`。
- 雷达图为内联 SVG，无外部依赖。

## 本地预览

项目根目录运行：

```bash
python3 -m http.server 8123
```

访问 <http://127.0.0.1:8123/>。

## 可视化核查（给人眼用）

模型自身无法直接看图。需要肉眼比对时，用已装在**隔离 node 工作区**
（非项目仓库）的 `@resvg/resvg-js` 把 `entries/*.svg` 渲染成 PNG：

```bash
cd ~/.workbuddy/binaries/node/workspace
npm ls @resvg/resvg-js   # 确认已装
# 用 resvg 的 JS API 把每个 svg 输出为 png，再交给用户看
```

脚本一律放 `/tmp` 或隔离工作区，**不要提交进仓库**。

## 坑（避免回归）

- **雷达图标签裁切**：`radarSVG` 把轴标签放在半径 `R+14`（中心 110,110），
  右侧「钢琴/演奏」与左侧「场景/细节」会超出默认 `0 0 220 220` viewBox 被静默裁掉。
  必须用够宽的 viewBox，例如 `"-40 -40 300 300"`（width/height 240），
  并按 x 相对中心选 `text-anchor`（start/middle/end）。改雷达图时务必先算标签包围盒。
- **仓库干净**：所有工具/迁移脚本留在 `/tmp` 或 `~/.workbuddy` 隔离区，仓库只保留
  `index.html`、`entries.json`、`rankings.json`、`entries/`、`README.md` 等源文件。
- **prompt 不变**：固定 prompt 是项目对比的基础，不要为"更好看"而改写。
