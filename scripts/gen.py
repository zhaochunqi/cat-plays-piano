#!/usr/bin/env python3
"""裸模型生成器：直连 magpie 本地 gateway，绕开 agent harness 的 system prompt / 工具注入。

固定 prompt 一字不改（见 SKILL.md）。与 pi / opencode 等工具直连的区别：
模型只看到这一句 user message，没有 harness 的 system prompt、工具定义和上下文。

用法:
    # 按 provider 批量：模型清单和 thinking 档位都从 gateway 的 /v1/models 现查，
    # 不维护任何模型列表文件（模型/档位变了自动跟上）
    uv run scripts/gen.py --provider opencode-zen-free --levels all
    uv run scripts/gen.py --provider opencode-zen-free --levels top --dry-run

    # 单个模型
    uv run scripts/gen.py opencode-zen-free/beam-free max
    uv run scripts/gen.py opencode-zen-free/big-pickle none

选项:
    --free                         只要 catalog 里 free=true 的模型
                                   （读 ~/.config/magpie/plugin-providers.json，和 magpie UI 的
                                   「免费」标记同源，不是靠名字带 -free 猜）
    --levels all|top|none|<l1,l2>   all=该模型列出的全部档位（默认），top=最高档，
                                    none=不带 reasoning，逗号列表=指定档位
    --record                       生成成功的同时追加进 entries.json（幂等）
    --dry-run                      只打印将要跑的任务，不请求
    --force                        忽略 entries.json 里已存在的 (model, thinking) 和已落盘文件
    --parallel N                   并发数（默认 4）

thinking 档位必须以 gateway 列出的为准；gateway 对无效档位会静默降级（不报错），
所以调用后应核对 usage.reasoning_tokens 是否随档位上升。

输出写入 entries/<display-name>-<thinking>-<date>.svg，仅落盘 XML 可解析、
根元素为 <svg> 的文档；失败只报错、不落盘。
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from xml.etree import ElementTree as ET

GW_DEFAULT = "http://127.0.0.1:3425/v1/chat/completions"
PROMPT = "Generate an SVG of a cat playing a piano."
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRIES = os.path.join(HERE, "entries")
INDEX = os.path.join(HERE, "entries.json")


def gateway():
    return os.environ.get("MAGPIE_GATEWAY", GW_DEFAULT)


def models():
    """magpie /v1/models —— id、display_name、列出的 reasoning 档位。"""
    url = gateway().rsplit("/chat/completions", 1)[0] + "/models"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)["data"]


def call(model, thinking, tries=3):
    body = {"model": model, "messages": [{"role": "user", "content": PROMPT}]}
    if thinking and thinking != "none":
        body["reasoning"] = {"effort": thinking}
        body["reasoning_effort"] = thinking
    req = urllib.request.Request(
        gateway(), data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    for n in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=900) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            # 429：同一个 provider 并发打太多会被限流，退避重试
            if e.code != 429 or n == tries - 1:
                raise
            time.sleep(10 * (n + 1))


FENCE = re.compile(r"```(?:svg|xml|html)?\s*(.*?)```", re.S)


def extract_svg(text):
    if not text:
        return None
    for blk in FENCE.findall(text):
        s = blk.strip()
        if s.lstrip().startswith("<svg"):
            return s
    i, j = text.find("<svg"), text.rfind("</svg>")
    if i >= 0 and j > i:
        return text[i:j + 6].strip()
    return None


def validate(svg):
    """XML 可解析、根元素是 <svg>，并且根上带 xmlns（resvg 等渲染器不认没有命名空间的根，
    缺了就补上——补过的版本才是要落盘的版本）。返回 (ok, 原因, 落盘用文本)。"""
    s = svg.strip()
    if not s.startswith("<svg"):
        return False, "not starting with <svg", s
    if not s.endswith("</svg>"):
        return False, "not ending with </svg>", s
    probe = s if "xmlns" in s[:200] else s.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    try:
        root = ET.fromstring(probe)
    except ET.ParseError as e:
        return False, f"xml parse error: {e}", s
    if not root.tag.endswith("svg"):
        return False, f"root tag {root.tag}", s
    return True, "ok", probe


def slug(name):
    """display_name -> entries 文件名用的 slug（与历史条目一致：小写、非字母数字转连字符）。

    "Space Bunny Free" -> space-bunny-free；"Hy3 (X)" -> hy3-x；"Grok-4.7" -> grok-4-7。
    """
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", name.strip().lower())).strip("-")


def levels_of(m, mode):
    """gateway 为模型列出的档位 -> _levels 要跑的任务档位列表。"""
    shown = [e["effort"] for e in (m.get("supported_reasoning_levels") or []) if e.get("effort")]
    if mode == "none":
        return ["none"]
    if mode == "top":
        return [shown[-1]] if shown else ["none"]
    if mode == "all":
        return shown or ["none"]
    return [x.strip() for x in mode.split(",") if x.strip()]


CATALOG = os.path.expanduser("~/.config/magpie/plugin-providers.json")


def free_ids():
    """catalog 里 free=true 的 provider/model —— 与 magpie UI 的「免费」标记同源。"""
    with open(CATALOG) as f:
        cat = json.load(f)
    return {f"{p['id']}/{m['id']}" for p in cat for m in p.get("models", []) if m.get("free")}


def jobs_from_providers(providers, level_mode, only_free):
    out, known = [], {m["id"]: m for m in models()}
    free = free_ids() if only_free else None
    # entries.json 的 model 用的是 display_name：同名模型（如 workbuddy 与 workbuddy-ai
    # 都供 Hy3）在画廊里无法区分，落盘文件名也会撞，只留先出现的那一个。
    seen = set()
    for p in providers:
        hits = [m for i, m in known.items() if i.startswith(p + "/")]
        if not hits:
            print(f"⚠ provider {p}: gateway 没有列出任何模型（magpie provider models {p} 看一眼）")
        for m in hits:
            if free is not None and m["id"] not in free:
                continue
            label = m.get("display_name") or m.get("magpie_label") or m["id"]
            if label in seen:
                print(f"· {m['id']} 与已选条目的 display_name 相同（{label}），跳过")
                continue
            seen.add(label)
            for lv in levels_of(m, level_mode):
                out.append((m["id"], lv))
    return out


def recorded():
    """entries.json 里已有的 (slug, thinking) —— 按文件名口径比，display_name 的大小写/标点差异不影响。"""
    if not os.path.exists(INDEX):
        return set()
    with open(INDEX) as f:
        return {(slug(e["model"]), e["thinking"]) for e in json.load(f)}


def record(entries):
    """把新条目追加进 entries.json（幂等、按落盘顺序）。"""
    if not entries:
        return
    with open(INDEX) as f:
        data = json.load(f)
    have = {(slug(e["model"]), e["thinking"]) for e in data}
    data += [e for e in entries if (slug(e["model"]), e["thinking"]) not in have]
    with open(INDEX, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")


def one(job, names, force, done):
    model, thinking = job
    label = names.get(model, model)
    key = (slug(label), thinking)
    if not force and key in done:
        print(f"· {label} [{thinking}] 已在 entries.json，跳过")
        return None
    fn = f"{slug(label)}-{thinking}-{date.today().isoformat()}.svg"
    if not force and os.path.exists(os.path.join(ENTRIES, fn)):
        print(f"· {fn} 已落盘，跳过")
        return None
    try:
        d = call(model, thinking)
    except Exception as e:
        print(f"✗ {label} [{thinking}] request failed: {e}")
        return None
    msg = d.get("choices", [{}])[0].get("message", {})
    content = msg.get("content") or ""
    if not content:
        # 有的模型（如 Beam Free）不走 content，而是发一个把 SVG 写进文件的 tool_call；
        # arguments 是 JSON 字符串（里面带 \\\" 和 \\n 转义），要先解开再找 <svg>
        parts = []
        for c in msg.get("tool_calls") or []:
            a = (c.get("function") or {}).get("arguments") or ""
            try:
                v = json.loads(a)
                parts += [x for x in (v.values() if isinstance(v, dict) else [v]) if isinstance(x, str)]
            except ValueError:
                parts.append(a)
        content = "\n".join(parts)
        if content:
            print(f"· {label} [{thinking}] content 为空，从 tool_calls 里取（{len(msg.get('tool_calls') or [])} 个）")
    if not content:
        print(f"✗ {label} [{thinking}] empty content; keys={list(msg.keys())}")
        return None
    svg = extract_svg(content)
    if not svg:
        print(f"✗ {label} [{thinking}] no <svg> found; head={content[:120]!r}")
        return None
    ok, why, svg = validate(svg)
    if not ok:
        print(f"✗ {label} [{thinking}] invalid svg: {why}")
        return None
    with open(os.path.join(ENTRIES, fn), "w") as f:
        f.write(svg + "\n")
    rt = (d.get("usage") or {}).get("completion_tokens_details", {}).get("reasoning_tokens")
    print(f"✓ {fn}  {len(svg)}B  served_as={d.get('model')}  reasoning_tokens={rt}")
    return {"model": label, "thinking": thinking, "date": date.today().isoformat(),
            "file": f"entries/{fn}"}


def main():
    ap = argparse.ArgumentParser(add_help=True, description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pairs", nargs="*", metavar="provider/model thinking")
    ap.add_argument("--provider", action="append", default=[], metavar="ID")
    ap.add_argument("--levels", default="all", metavar="all|top|none|l1,l2")
    ap.add_argument("--free", action="store_true")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--parallel", type=int, default=4)
    a = ap.parse_args()

    if a.pairs:
        if len(a.pairs) % 2:
            ap.error("positional 参数要成对：<provider/model> <thinking>")
        jobs = [(a.pairs[i], a.pairs[i + 1]) for i in range(0, len(a.pairs), 2)]
    elif a.provider:
        jobs = jobs_from_providers(a.provider, a.levels, a.free)
    else:
        ap.print_help()
        return 1
    if not jobs:
        print("没有任务")
        return 1

    names = {m["id"]: (m.get("display_name") or m.get("magpie_label") or m["id"]) for m in models()}
    done = recorded()
    if a.dry_run:
        for model, lv in jobs:
            print(f"{model} [{lv}] → {slug(names.get(model, model))}-{lv}-{date.today().isoformat()}.svg")
        print(f"\n{len(jobs)} 个任务（dry-run，未请求）")
        return 0

    with ThreadPoolExecutor(max_workers=max(1, a.parallel)) as ex:
        made = [e for e in ex.map(lambda j: one(j, names, a.force, done), jobs) if e]
    if a.record:
        record(made)
    print(f"\n{len(made)}/{len(jobs)} 落盘" + ("，已写入 entries.json" if a.record else ""))
    return 0 if made else 1


if __name__ == "__main__":
    sys.exit(main())
