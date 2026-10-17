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

## 新增一条目（两条路）

### A. magpie gateway 直连（裸模型，推荐，绕开 harness）

pi / opencode 等工具里跑固定 prompt，模型会带上一堆 harness 的 system prompt、工具定义和
上下文——同一个模型在画廊里会比"裸模型"更强或更弱，横向对比不干净。`just gen` 走 magpie
的本地 gateway（`http://127.0.0.1:3425/v1`，本机免 key），模型只收到这一句 user message。

```bash
magpie healthcheck          # 网关在不在
just gen <provider/model> <thinking>    # 例：just gen opencode-zen-free/beam-free max
just gen-free                           # 所有免费模型 × 全部 thinking 档位
just gen-provider <provider> [args]     # 某个 provider 的全部模型（top / <l,l> / --dry-run）
```

- gateway 地址可用 `MAGPIE_GATEWAY=http://host:port` 覆盖。
- **不要维护模型清单文件**（历史上有个 `free.txt`）：`scripts/gen.py` 从 `/v1/models` 现查
  模型、用模型自己列出的 `supported_reasoning_levels` 定档位；「免费」读
  `~/.config/magpie/plugin-providers.json` 的 `free` 字段（与 magpie UI 同源），不靠名字猜。
- `<thinking>` 只填 gateway 为该模型列出的 effort 档位。
  **gateway 对无效档位静默降级，不报错**——拼错只会悄悄变成默认档，
  所以每次看一眼输出里的 `reasoning_tokens` 随档位是否上升。
- 落盘文件名用 magpie 的 `display_name` 的 slug（如 `Space Bunny Free` → `space-bunny-free`），
  entries.json 的 `model` 用 display_name 原文；无档位的模型填 `none`。
- 同一模型被两个 provider 供（`workbuddy/hy3` 与 `workbuddy-ai/hy3`）时只留一条：
  display_name 相同，不 dedupe 会撞文件名、画廊里也分不出来。

### B. 走 agent 工具（会带 harness 上下文）

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
  "scores": { "cat": 0, "piano": 0, "playing": 0, "scene": 0, "detail": 0 }
}
```

- **`battleStats`**（可选）：对战 ELO 派生数据，由本地评测服务器（`just serve`）写入，
  **不要手写**。字段 `{elo, rd, confidence:"high"|"mid"|"low", games, wins, losses, draws, bad, syncedAt}`。
  新入库条目没有 `battleStats`，页面按 `elo = -1e9` 处理，自然垫底——这是预期行为，不用管。
- **排序**（`index.html`）：**只按对战 ELO**，不再有人工策展序/ `order` 字段。
  `battleStats.elo` 降序；ELO 差 ≤ `ELO_BAND`(40) 时依次比胜率 `wins/(wins+losses+draws)`、胜场、文件名。
  （旧版 `order` fractional 键已废弃，rankings.json 里已无此字段。）
- **`animated`**：可选布尔；`true` 表示 SVG 含动画（CSS `@keyframes` / SMIL `<animate>`）。画廊卡片与放大视图显示「▶ 动画」徽章，仅作标注、不影响排序与评分。
- **`scores`**：五维各 0–10，仅用于放大视图的 Dota 风格雷达图展示，**不参与排序**。
  维度含义：`cat`=猫、`piano`=钢琴、`playing`=演奏、`scene`=场景氛围、`detail`=细节。
  完整分段标准见下方「评分标准」章节。
- **`note`**：点击作品放大时展示的评测理由。**必须与实际渲染图一致**——若原 note 与渲染结果不符
  （如误写"缺琴身"但实际有琴身、夸"姿态正确"实际不像在弹），应据实改写，不要保留错误描述。
## 新增 thinking 级别时：**必须同步 `index.html` 的 `THINK_LABELS`**

`index.html` 里 `THINK_LABELS` 把 thinking 值映射成中文（如 `extend → "扩展思考"`）。
**没有映射的值会 fallback 成 `"thinking: <原值>"`**，而且筛选栏会自动为这个 fallback 串
生成一个按钮——页面上就会出现「thinking: max」这种丑标签（历史上 `claude-sonnet-5-max`
就漏过，`extreme` 也漏过）。

所以入库新 thinking 值时，先在 `THINK_LABELS` 补一行：

```js
var THINK_LABELS = {
  none: "直接生成", high: "深度思考", medium: "中度思考",
  deep: "深度思考", extend: "扩展思考",
  max: "最大思考", extreme: "极致思考",
};
```

用的命名：**medium=中度 / high·deep=深度 / extend=扩展 / max=最大 / extreme=极致**。

## 不在榜内的条目

不在 `rankings.json` 榜单内的条目，页面排序时垫底（elo 视为 -1e9）。

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
（非项目仓库）的 `@resvg/resvg-js` + `sharp` 把 `entries/*.svg` 渲染成 PNG：

```bash
cd ~/.workbuddy/binaries/node/workspace
node render.mjs <svg>...      # 单张 → /tmp/png/<name>.png
node sheet.mjs <svg>...       # 批量对照片：每张 6 个（3×2）带文件名标签 → /tmp/png/sheet-N.jpg
node check.mjs <svg>...       # 只验证能否渲染（resvg 不认没有 xmlns 的根）
```

评分前先用 `sheet.mjs` 拼对照图，**肉眼看图**再按上面「评分标准」填 `scores` 与 `note`——
只看文件名或文字描述会误判（历史上有“有琴身”误写成“缺琴身”、把仓鼠评成猫 9 分）。

脚本一律放 `/tmp` 或隔离工作区，**不要提交进仓库**。

## 坑（避免回归）

### scripts/gen.py（裸模型生成器）

- **`content` 可能是空的**：Beam Free 不发正文，而是发一个 `cat > /tmp/x.svg <<'EOF' …` 的
  tool_call；它的 `function.arguments` 是**转义过的 JSON 字符串**，直接正则找 `<svg>` 会解析失败
  （`not well-formed: line 1, column 11`），必须先 `json.loads` 再找。
- **落盘前必须补 `xmlns`**：模型给的 `<svg>` 常没有命名空间，Python 的 ElementTree 能解析，
  但 resvg 会报 `document does not have a root node`——所以写入的是补过 `xmlns` 的版本，
  不是原文（`validate()` 把补过的文本返回给调用方落盘）。
- **429 是账号级限流**：`workbuddy-ai` 报 `usage exceeds frequency limit …` 时是当天额度用完，
  等到重置时间再跑；同一个 provider 并发不要超过 2～4。
- **“免费”不看名字看 catalog**：`~/.config/magpie/plugin-providers.json` 里每个模型的 `free`
  字段才是权威（跟 magpie UI 一致）。workbuddy 里带 free 名字的一个都没有，
  真正 free=true 的只有 `hy3` / `step-5-preview`（+ workbuddy-ai 的 `deepseek-v4.1-flash`）。
- **同名模型要去重**：`workbuddy/hy3` 与 `workbuddy-ai/hy3` 的 display_name 都是 `Hy3`，
  不去重就会互相覆写同一个 SVG、画廊里也分不出是谁。

### 页面与数据

- **雷达图标签裁切**：`radarSVG` 把轴标签放在半径 `R+14`（中心 110,110），
  右侧「钢琴/演奏」与左侧「场景/细节」会超出默认 `0 0 220 220` viewBox 被静默裁掉。
  必须用够宽的 viewBox，例如 `"-40 -40 300 300"`（width/height 240），
  并按 x 相对中心选 `text-anchor`（start/middle/end）。改雷达图时务必先算标签包围盒。
- **`rankings.json` 是 2 空格缩进、`entries.json` 是 4 空格**（`server.py` 的 `save_json` 用 2），
  手改/脚本改请对齐，否则 diff 全是排版噪声。
- **别在 `just serve` 跑着的时候改 `rankings.json`**：服务器把整份榜单放在内存里，
  每次投票都会重写回磁盘，你的新条目会被丢掉（改完再启动，或先停）。
- **仓库边界**：`scripts/gen.py` 属于仓库（它是项目工具，随仓维护）；
  一次性的迁移 / 批量脚本、渲染中间产物才放 `/tmp` 或 `~/.workbuddy` 隔离区，
  不要提交进仓库。
- **prompt 不变**：固定 prompt 是项目对比的基础，不要为"更好看"而改写。

