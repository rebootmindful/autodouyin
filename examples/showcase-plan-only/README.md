<!--
[INPUT]: 依赖 {examples/brief/minimal-douyin-video.json} 的 {公开展示样例}
[OUTPUT]: 对外提供 {审核包 showcase 的来源说明}
[POS]: {examples/showcase-plan-only} 的 {showcase 索引}
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Showcase Plan Only

这个目录由下面的命令生成：

```bash
python scripts/run_pipeline.py --brief examples/brief/minimal-douyin-video.json --output-dir examples/showcase-plan-only
```

它代表 AutoDouyin 最核心的公开卖点：

- 先把 brief 编译成完整审核包
- 停在 `pending-review`
- 不越过审核关口直接执行
