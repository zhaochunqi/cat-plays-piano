# cat-plays-piano 本地评测工具

# 启动本地评测服务器（每次投票自动写入 rankings.json）
# 用法：just serve   然后浏览器打开 http://localhost:8123/battle.html
serve:
    @echo "🎹 启动评测服务器 → http://localhost:8123/battle.html"
    @echo "   投票会自动保存到 rankings.json，Ctrl+C 停止"
    uv run server.py

# 启动并自动打开浏览器
serve-open:
    @echo "🎹 启动评测服务器 → http://localhost:8123/battle.html"
    @(open http://localhost:8123/battle.html &) || true
    uv run server.py

# 直连 magpie 本地 gateway 生成（裸模型，绕开 agent harness）· 需 magpie 在跑（magpie healthcheck）
# 模型清单与 thinking 档位都从 gateway 现查，仓库里不存模型列表文件。
# 用法：just gen <provider/model> <thinking>   例：just gen opencode-zen-free/beam-free max
gen MODEL THINKING:
    uv run scripts/gen.py {{MODEL}} {{THINKING}}

# 一个 provider 的全部模型 × 全部档位
# 用法：just gen-provider opencode-zen-free
#       just gen-provider opencode-zen-free top --dry-run   先看任务清单
# 零成本 provider（不耗积分也不付费）：opencode-zen-free
gen-provider PROVIDER *ARGS:
    uv run scripts/gen.py --provider {{PROVIDER}} --record {{ARGS}}

# 所有免费模型 × 全部档位。免费标记取自 magpie catalog 的 free=true（与 UI 同源）
gen-free *ARGS:
    uv run scripts/gen.py --provider opencode-zen-free --provider workbuddy --provider workbuddy-ai --free --record {{ARGS}}

# 从 gateway 看每个模型当前列出的 reasoning 档位（gateway 对无效档位静默降级，别猜）
gen-models:
    curl -s http://127.0.0.1:3425/v1/models | python3 -c "import json,sys; [print(m['id'], '|', ','.join(e['effort'] for e in (m.get('supported_reasoning_levels') or [])) or 'none') for m in json.load(sys.stdin)['data']]"

# 导出当前 votes.json 备份
backup:
    @cp votes.json votes-backup-$(shell date +%Y%m%d-%H%M%S).json 2>/dev/null && echo "已备份 votes.json" || echo "尚无投票数据"

# 清空所有投票记录（重置评测，不可逆）
reset:
    @rm -f votes.json
    @echo "已清空 votes.json（rankings.json 需手动重置为初始顺序）"
