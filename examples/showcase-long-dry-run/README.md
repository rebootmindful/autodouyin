<!--
[INPUT]: 依赖 {examples/brief/ultra-long-workflow.json} 的 {长视频 dry-run showcase}
[OUTPUT]: 对外提供 {approve -> generate dry-run 样例说明}
[POS]: {examples/showcase-long-dry-run} 的 {showcase 索引}
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Showcase Long Dry Run

这个目录由下面的命令链生成：

```bash
python scripts/run_pipeline.py --brief examples/brief/ultra-long-workflow.json --output-dir examples/showcase-long-dry-run
python scripts/run_pipeline.py --dir examples/showcase-long-dry-run --approve --model seedance-2.0-fast
python scripts/run_pipeline.py --dir examples/showcase-long-dry-run --generate
```

它用来展示两件事：

- 长视频会被收敛到 `scene-split-edit-pipeline`
- 审核批准后，执行层状态会写回 `generation-report.json` 与 `run-ledger.json`
