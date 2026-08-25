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

# 导出当前 votes.json 备份
backup:
    @cp votes.json votes-backup-$(shell date +%Y%m%d-%H%M%S).json 2>/dev/null && echo "已备份 votes.json" || echo "尚无投票数据"

# 清空所有投票记录（重置评测，不可逆）
reset:
    @rm -f votes.json
    @echo "已清空 votes.json（rankings.json 需手动重置为初始顺序）"
