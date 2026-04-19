# 通用行动与系统设置自定义（开发细化）

## 0. 适用范围与说明

- 本文档面向 `client/client_gRPC/dev_test` 的 Tkinter 测试端（下称“测试端”）。
- 目标不是“为每个新行动/新法术写专属 UI”，而是提供一套**通用配置框架**，让后端玩法快速试验、调参、复盘。
- 约束与边界：
  - **优先纯测试端实现**（不依赖后端新增通用接口）。
  - 对后端现有实现仅做“对照、提示、兼容”，除非确认是后端 bug 且需要修复对齐玩法。
- 本文档只定义：
  - “行动设置/属性设置”里可调整的**数值与公式系数**。
  - “系统设置”里未来要新增的：**自定义攻击 / 自定义法术 / 延时法术两种承载体 / 预置 debuff / 自定义濒死机制**。

---

## 1. 术语与总览

### 1.1 行动（Action）

- 行动：玩家在回合内触发的一次结算（攻击、施法、位移等）。
- 行动的共性字段（建议最小集合）：

| 字段 | 含义 | 备注 |
| --- | --- | --- |
| `name` | 显示名 | UI 下拉/日志 |
| `kind` | 类型 | `Attack` / `Spell` / `CustomAttack` / `CustomSpell` |
| `cost_ap` | 行动点消耗 | 一般为 1 |
| `cost_sp` | 法术点消耗 | 攻击通常为 0 |
| `target_mode` | 选点方式 | `Lock`（选单位）/ `Area`（选区域中心）/ `Self` |
| `range` | 施法/攻击距离 | 施法者到“目标/施法点” |
| `area_radius` | 作用半径 | 非范围行动可为 0 |
| `delay` | 延时配置 | `0` 瞬发；`>0` 延时 |
| `effect` | 结算效果 | Damage / Heal / Move / ApplyStatus / SpawnEntity（延时） |

### 1.2 两类设置入口（必须划清边界）

- **行动设置（对局内调参）**：
  - 调整“攻击公式/系数/阈值”等**攻击数值体系**。
  - 调整“已有法术（SpellFactory 已存在的那些）”的**数值参数**（如 baseValue/range/cost/lifespan）。
  - 典型用途：平衡性试验、快速复现后端改动后的强度差异。

- **系统设置（对局外扩展能力）**：
  - 新增一种自定义“攻击”（CustomAttack 模板）。
  - 新增一种自定义“法术”（CustomSpell 模板）。
  - 延时法术的两种承载体：棋盘实体（Board Entity）与棋子状态（Piece Status）。
  - 预置 debuff（可选模板库）。
  - 后端未完善机制的测试端自定义实现（例如“濒死”）。

---

## 2. 行动设置：攻击数值/公式/系数可自定义

> 需求原意：把“攻击”的强度与命中模型做成参数化，而不是写死在某个实现里。

### 2.1 建议可配置项（最小可用）

攻击建议拆为两段：**命中判定**与**伤害结算**。所有数值均可在行动设置中调整。

- 命中判定（可选开关）：
  - 是否启用 `d20`（关闭则视为必定命中，便于压测/调参）。
  - `hit_throw = d20 + hit_bonus`
  - `hit_def = target_def`
  - 命中条件：`hit_throw > hit_def`
  - 大成功/大失败：
    - `d20 = 1`：必失败
    - `d20 = 20`：必成功

- 伤害结算（建议可配置）：
  - 伤害类型：`Physical` / `Magic`
  - `raw = base + coeff_str * STR_mod + coeff_dex * DEX_mod + flat_bonus`
  - 抗性结算口径：
    - 物理：`real = max(0, raw - target.physical_resist)`
    - 法术：`real = max(0, raw - target.magic_resist)`

> 注：这里的 `base` 可以来源于“当前武器表”，也可以由行动设置覆盖。

### 2.2 与“属性设置”的边界

- 属性设置：改角色面板上的属性（STR/DEX/INT、抗性、HP 等）。
- 行动设置：改“用这些属性怎么结算”的公式（系数、阈值、是否启用 d20 等）。

### 2.3 推荐配置结构（示例）

- 建议把行动设置存成一份 JSON（可按对局保存/加载），核心是 `attack_model`：

```json
{
  "attack_model": {
    "enable_d20": true,
    "auto_hit_if_disable": true,
    "hit": {
      "bonus_flat": 0,
      "use_str_mod": true,
      "use_dex_mod": false,
      "coeff_str": 1.0,
      "coeff_dex": 0.0,
      "crit_on_20": true,
      "fail_on_1": true
    },
    "damage": {
      "base_from_weapon": true,
      "base_override": null,
      "flat_bonus": 0,
      "coeff_str": 1.0,
      "coeff_dex": 0.0,
      "resist_mode": "subtract"
    }
  }
}
```

---

## 3. 行动设置：已有法术出伤逻辑与相关数值可自定义

> “已有法术”指：已在后端/工具侧存在定义的法术模板（可参考 devel_details/spell.md 的清单）。

### 3.1 可调整的法术参数（建议最小集）

- 建议允许在行动设置中覆盖以下字段（不改变法术“效果类型”）：
  - `baseValue`
  - `range`
  - `areaRadius`
  - `spellCost`
  - `baseLifespan`
  - `isAreaEffect`
  - `isDelaySpell`
  - `isLockingSpell`

### 3.2 建议覆盖策略

- 默认：使用 SpellFactory 的原始模板。
- 若行动设置提供 override：只覆盖数值字段；效果类型（Damage/Heal/Move）不变。
- 覆盖优先级（建议）：
  1) 行动设置 override
  2) 工厂模板默认值

### 3.3 推荐配置结构（示例）

```json
{
  "spell_overrides": {
    "1": { "baseValue": 30, "range": 2, "areaRadius": 5, "spellCost": 1 },
    "4": { "baseValue": 20, "baseLifespan": 3 }
  }
}
```

---

## 4. 系统设置：新增自定义攻击（CustomAttack）

> 目标：当玩法想测试“完全不同的一种普攻/特殊攻击”时，不需要改后端，也不需要写死在 UI 里。

### 4.1 CustomAttack 最小模板字段

- `name`
- `damage_type`：Physical/Magic
- `target_mode`：Lock/Area/Self
- `range` / `area_radius`
- `cost_ap`（通常 1）
- `formula_ref`：引用某个攻击模型（见 2 章）或内联一份模型

### 4.2 建议限制（避免变成脚本系统）

- CustomAttack 只允许调用“通用攻击模型”（命中 + 伤害）。
- 不引入任意脚本执行；扩展效果（例如 debuff）放到自定义法术或预置 debuff（见 6 章）。

---

## 5. 系统设置：新增自定义法术（CustomSpell）与延时法术两种承载体

### 5.1 CustomSpell 最小模板字段

- `name`
- `effect_type`：Damage / Heal / Move / ApplyStatus
- `damage_type`：Physical/Magic（仅 Damage 需要）
- `baseValue`
- `range` / `area_radius`
- `cost_ap` / `cost_sp`
- `target_mode`：Lock/Area/Self
- `delay`：0=瞬发；>0=延时回合数
- `carrier`（仅延时法术）：`BoardEntity` / `PieceStatus`

### 5.2 延时承载体 A：棋盘实体（Board Entity）

适合：陷阱、地面持续区、延时爆炸点。

- 生成一个“棋盘实体”放在某格：
  - 具有 `position`、`lifespan`、`owner/camp`、`spell_template`。
  - 每回合末（或指定时机）`lifespan -= 1`，到 0 时触发并移除。
- 触发时目标筛选建议：按“触发时区域内单位”（动态）。
- UI 展示：实体应该能在棋盘上可视化（图标/寿命），便于测试人员复盘。

### 5.3 延时承载体 B：挂在棋子上的状态（Piece Status）

适合：中毒、燃烧、定时炸弹、标记类技能。

- 给目标棋子挂一个 `Status`：
  - `status_id/name`、`remaining_turns`、`tick_timing`（回合开始/结束）、`payload`。
  - 每回合按 timing 执行一次 tick 或在到期时执行 expire。
- UI 展示：信息面板需要能看到状态与剩余回合数（便于验证）。

### 5.4 两种承载体共用的“延时结算接口”（建议）

- 统一的“延时队列”更新点：回合末（与现有延时法术语义更接近）。
- 两种载体都应输出一致格式的日志：
  - 创建：谁创建、在哪里/挂在谁身上、寿命多久
  - 触发：命中谁、结算值多少、是否致死
  - 移除：自然到期/被驱散/被触发

---

## 6. 系统设置：预置 debuff（模板库）

> 目标：不改后端的情况下，测试端能快速给“自定义法术/自定义机制”复用一套通用 debuff。

### 6.1 建议的最小 debuff 集

- `Poison`：每回合结算固定伤害（或按系数）
- `Burn`：每回合结算伤害（可与 Poison 区分为法术伤害类型）
- `Slow`：降低移动力（影响 max_movement/movement 的口径需要写死）

> 注：先把“状态显示 + 生命周期 + 结算时机”跑通，再扩展更多种类。

### 6.2 建议的 debuff 模板字段

- `name`
- `duration_turns`
- `tick_timing`：turn_start/turn_end
- `effect`：damage_per_tick / movement_delta / 等
- `stacking`：none/refresh/stack（建议先做 none 或 refresh）

---

## 7. 系统设置：自定义濒死机制（测试端实现）

> 背景：后端机制尚未完善或与玩法文档存在差异（例如死亡检定规则）。测试端需要能“选择一套规则”用于玩法测试，而不是强依赖后端。

### 7.1 建议提供的开关与参数

- 是否启用濒死系统（关闭则沿用“HP<=0 直接死亡”的简化口径）。
- 死亡检定模型（建议参数化）：
  - `dc`（阈值）
  - 成功/失败计数上限（例如 3 成功稳定、3 失败死亡）
  - `d20=1` 与 `d20=20` 的特殊规则（是否两次失败/直接稳定）
- 濒死时允许的行动（例如只能等待/不能攻击/不能施法）。

### 7.2 与 UI/日志的交互要求

- 信息面板必须能看见：濒死状态、成功/失败次数、下一次检定触发点。
- 日志必须能复盘：每次 d20 值、应用了哪套规则、最终结论。

---

## 8. 落地建议：配置加载/保存与代码集成点

### 8.1 配置持久化建议

- 行动设置（对局内调参）：建议支持“本局临时配置”，可导出为 JSON 供复盘。
- 系统设置（能力扩展）：建议支持“用户级配置”，默认随测试端长期保存。

> 实现上可以都落到 `dev_test/data/` 下的 json，但需要在 UI 中明确“本局 vs 全局”。

### 8.2 推荐集成点（按现有目录结构）

- UI：`client/client_gRPC/dev_test/ui/main_ui.py`
  - 增加两个入口按钮（若已存在则对齐命名）：行动设置 / 系统设置
- 逻辑层：`client/client_gRPC/dev_test/logic/controller.py`
  - 统一接入“行动模板 -> 结算器”的调用
- 数据层：`client/client_gRPC/dev_test/core/data_provider.py`
  - 读取/写入配置、向 UI 提供当前生效配置快照

---

## 9. 最小实现顺序（MVP）

1. 行动设置：落地 `attack_model` 的配置读写与结算引用（先只影响测试端攻击）。
2. 行动设置：对 SpellFactory 产出的法术模板做“数值 override”（不改 effect_type）。
3. 系统设置：CustomAttack（只复用 attack_model）。
4. 系统设置：CustomSpell（瞬发 + ApplyStatus）。
5. 延时法术承载体：先做 BoardEntity，再做 PieceStatus（两种日志格式统一）。
6. 系统设置：濒死机制（可切换规则集 + 信息面板展示）。
