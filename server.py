#!/usr/bin/env python3
"""本地评测服务器 — cat-plays-piano 双盲对比

每次投票自动：
  1. 追加到 votes.json（原始投票记录，可审计）
  2. 重算所有模型的 ELO 分数
  3. 按 ELO 降序附 battleStats 写回 rankings.json（不再写入 order，排名为单一 ELO 口径）

纯静态 file:// 无法写文件，所以需要一个本地服务器来做自动持久化。
启动：just serve  →  http://localhost:8123/battle.html
"""
import json
import os
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
RANKINGS_PATH = os.path.join(ROOT, "rankings.json")
VOTES_PATH = os.path.join(ROOT, "votes.json")
PORT = int(os.environ.get("PORT", "8123"))
K_FACTOR = 32
MIN_GAMES = 10
# 「都挺烂」固定惩罚：双方每次都扣这么多 ELO，确保沉到很后面
BAD_PENALTY = 100


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default
    return default


def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)  # atomic write


def expected_score(a, b):
    return 1 / (1 + 10 ** ((b - a) / 400))


def compute_state(rankings, votes):
    """重放所有投票，计算每个模型的 ELO 与 W/L/D/bad。"""
    elo = {e["file"]: 1000 for e in rankings}
    stats = {e["file"]: {"wins": 0, "losses": 0, "draws": 0, "bad": 0, "elo": 1000} for e in rankings}
    for v in votes:
        lf, rf, res = v.get("leftFile"), v.get("rightFile"), v.get("result")
        if lf not in elo or rf not in elo or res == "skip":
            continue
        if res == "both-bad":
            # 都挺烂：双方扣固定惩罚，沉到很后面（相对顺序不变）
            stats[lf]["bad"] += 1
            stats[rf]["bad"] += 1
            elo[lf] = round(elo[lf] - BAD_PENALTY)
            elo[rf] = round(elo[rf] - BAD_PENALTY)
            continue
        ea_l = expected_score(elo[lf], elo[rf])
        ea_r = expected_score(elo[rf], elo[lf])
        if res == "left":
            sl, sr = 1, 0
            stats[lf]["wins"] += 1
            stats[rf]["losses"] += 1
        elif res == "right":
            sl, sr = 0, 1
            stats[rf]["wins"] += 1
            stats[lf]["losses"] += 1
        else:  # draw
            sl, sr = 0.5, 0.5
            stats[lf]["draws"] += 1
            stats[rf]["draws"] += 1
        elo[lf] = round(elo[lf] + K_FACTOR * (sl - ea_l))
        elo[rf] = round(elo[rf] + K_FACTOR * (sr - ea_r))
    for f in stats:
        stats[f]["elo"] = elo[f]
    return stats


def confidence(games):
    if games == 0:
        return "none", 350
    rd = round(350 / (1 + (games / 5)) ** 0.5)
    level = "low" if games < 5 else ("mid" if games < MIN_GAMES else "high")
    return level, rd


def regenerate_rankings(rankings, stats):
    """按 ELO 降序附 battleStats，写回 rankings.json（不再写入 order）。"""
    enriched = []
    for e in rankings:
        s = stats.get(e["file"], {"wins": 0, "losses": 0, "draws": 0, "elo": 1000})
        g = s["wins"] + s["losses"] + s["draws"]
        level, rd = confidence(g)
        new_e = dict(e)
        new_e["battleStats"] = {
            "elo": s["elo"], "rd": rd, "confidence": level, "games": g,
            "wins": s["wins"], "losses": s["losses"], "draws": s["draws"],
            "bad": s.get("bad", 0),
            "syncedAt": datetime.now(timezone.utc).isoformat(),
        }
        enriched.append((new_e, s["elo"]))
    enriched.sort(key=lambda x: x[1], reverse=True)
    out = []
    for i, (e, _) in enumerate(enriched):
        # 排名为单一 ELO 口径，不再写入人工 order 键
        out.append(e)
    save_json(RANKINGS_PATH, out)
    return out


def apply_vote(payload):
    rankings = load_json(RANKINGS_PATH, [])
    votes = load_json(VOTES_PATH, [])
    votes.append(payload)
    save_json(VOTES_PATH, votes)
    stats = compute_state(rankings, votes)
    regenerate_rankings(rankings, stats)
    return stats, len(votes)


def delete_vote(payload):
    """撤销：按 time 命中并移除该条投票，重算 ELO 与排名。"""
    rankings = load_json(RANKINGS_PATH, [])
    votes = load_json(VOTES_PATH, [])
    t = payload.get("time")
    new_votes = [v for v in votes if v.get("time") != t]
    removed = len(votes) - len(new_votes)
    save_json(VOTES_PATH, new_votes)
    stats = compute_state(rankings, new_votes)
    regenerate_rankings(rankings, stats)
    return stats, len(new_votes), removed


def utcnow():
    return datetime.now(timezone.utc).isoformat()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/"):
            return self.handle_api_get()
        return super().do_GET()

    def handle_api_get(self):
        if self.path.split("?")[0] == "/api/state":
            rankings = load_json(RANKINGS_PATH, [])
            votes = load_json(VOTES_PATH, [])
            stats = compute_state(rankings, votes)
            # votes 返回完整数组（含 leftFile/rightFile/result/mode/round/time），
            # 供客户端重建 history，从而恢复进度 / 未评测对局 / 重测 模式。
            self._send_json({"votes": votes, "voteCount": len(votes), "stats": stats,
                             "rankings": rankings, "generatedAt": utcnow()})
        elif self.path.split("?")[0] == "/api/health":
            self._send_json({"ok": True})
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path.split("?")[0] == "/api/vote":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return self._send_json({"error": "bad json"}, 400)
            if not payload.get("leftFile") or not payload.get("rightFile"):
                return self._send_json({"error": "missing files"}, 400)
            try:
                stats, count = apply_vote(payload)
            except Exception as ex:  # noqa
                return self._send_json({"error": str(ex)}, 500)
            self._send_json({"ok": True, "votes": count, "stats": stats})
        elif self.path.split("?")[0] == "/api/vote/delete":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return self._send_json({"error": "bad json"}, 400)
            if not payload.get("time"):
                return self._send_json({"error": "missing time"}, 400)
            try:
                stats, count, removed = delete_vote(payload)
            except Exception as ex:  # noqa
                return self._send_json({"error": str(ex)}, 500)
            self._send_json({"ok": True, "removed": removed, "votes": count, "stats": stats})
        else:
            self._send_json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):
        # 简洁日志，只显示 API 调用
        if "api/" in (self.path or ""):
            super().log_message(fmt, *args)


def main():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"🎹 cat-plays-piano 评测服务器已启动")
    print(f"   评测页:  http://localhost:{PORT}/battle.html")
    print(f"   排行榜:  http://localhost:{PORT}/index.html")
    print(f"   投票自动写入 rankings.json + votes.json")
    print(f"   停止: Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
