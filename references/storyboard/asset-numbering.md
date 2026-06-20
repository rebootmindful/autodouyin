<!--
[INPUT]: 依赖 {素材清单与分镜引用} 的 {编号规则}
[OUTPUT]: 对外提供 {C/S/P 素材体系}
[POS]: {references/storyboard} 的 {素材编号参考}
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
-->

# Asset Numbering

## ID Classes

- `C01-C99`：角色
- `S01-S99`：场景
- `P01-P99`：道具

## Rules

1. `asset_id` 必须稳定，不随文案变化漂移。
2. 分镜里引用素材时，只引用 `asset_id`，不直接引用模糊名称。
3. `asset-manifest` 是素材的单一事实源。

## Example

- `C01`：主角正面全身
- `S01`：夜景办公桌
- `P01`：手机 / 平板 / 麦克风
