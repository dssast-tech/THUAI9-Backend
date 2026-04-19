# 天赋属性（力量/敏捷/智力）与派生影响（开发细化）

## 0. 适用范围与说明

- 本文档面向 `client/client_gRPC/dev_test` 的 Tkinter 测试端与后端实现对照。
- 目的：把“力量/敏捷/智力”在当前版本后端里**到底影响了哪些数值/公式**讲清楚，并给出代码索引，方便后续在 UI 文案与调参模型中保持一致。
- 注意：服务端（C#）与测试端（Python env.py）在少数地方存在不一致；本文以“可验证的代码实现”为准，并在末尾列出已知差异。

---

## 1. 属性字段与基本含义

三项天赋属性（通常由初始化分配，总和限制由后端校验）：

- `strength`（力量）
- `dexterity`（敏捷）
- `intelligence`（智力）

Python（测试端 env）：字段定义见：
- `THUAI9-Backend-master/client/client_gRPC/env.py:22-54`（`class Piece.__init__` 内 strength/dexterity/intelligence 等字段）

C#（服务端）：字段定义见：
- `THUAI9-Backend-master/server/server/server/Piece.cs:24-33`（`strength/dexterity/intelligence` 字段）

---

## 2. 两类“修正值/调整值”实现（非常关键）

当前代码里同时存在两套“把属性值映射到 1~4 的离散值”的实现：

### 2.1 环境级：Step Modified（用于命中对抗）

这套函数把输入 `num` 映射为 1/2/3/4，阈值是 10/20/30：

- Python：`Environment.step_modified_func`
  - `THUAI9-Backend-master/client/client_gRPC/env.py:838-849`
- C#：`Env.Step_Modified_Func`
  - `THUAI9-Backend-master/server/server/server/env.cs:112-125`

逻辑：
- `num <= 10 -> 1`
- `num <= 20 -> 2`
- `num <= 30 -> 3`
- `else -> 4`

用途（目前明确用在物理命中对抗里）：
- 物理命中：攻击端用力量阶梯，防御端用敏捷阶梯
  - Python：`THUAI9-Backend-master/client/client_gRPC/env.py:1039-1055`
  - C#：`THUAI9-Backend-master/server/server/server/env.cs:174-191`

### 2.2 棋子 Accessor 级：*Adjustment（当前未在核心结算中使用）

`Piece.Accessor` 里也提供了 `StrengthAdjustment / DexterityAdjustment / IntelligenceAdjustment`，阈值是 7/13/16（和上面的 10/20/30 不同）：

- Python：
  - `strength_adjustment / dexterity_adjustment / intelligence_adjustment`
  - `THUAI9-Backend-master/client/client_gRPC/env.py:214-245`
- C#：
  - `StrengthAdjustment / DexterityAdjustment / IntelligenceAdjustment`
  - `THUAI9-Backend-master/server/server/server/Piece.cs:176-183`

现状：这套 Adjustment 在目前的核心“命中/伤害/施法”流程里**没有被调用**（至少在当前仓库这份实现里没有检索到其调用点）。

建议（测试端 UI 文案）：
- 若 UI 要展示“命中对抗”相关的属性修正，应以 `step_modified_func / Step_Modified_Func` 为准。
- 若未来要统一改为 `*Adjustment`（阈值 7/13/16），需要后端明确规则并统一替换调用点。

---

## 3. 已确认的派生数值（初始化时由属性计算）

### 3.1 最大生命（Max HP）

- `max_health = 30 + strength * 2`
- Python 初始化位置：`THUAI9-Backend-master/client/client_gRPC/env.py:934-936`
- C# 初始化位置：`THUAI9-Backend-master/server/server/server/Player.cs:186-187`

### 3.2 最大行动位（Max Action Points）

力量分段决定上限：
- `strength <= 13 -> 1`
- `strength <= 21 -> 2`
- `else -> 3`

- Python：`PieceAccessor.set_max_action_points`
  - `THUAI9-Backend-master/client/client_gRPC/env.py:126-134`
- C#：`Piece.Accessor.SetMaxActionPoints`
  - `THUAI9-Backend-master/server/server/server/Piece.cs:122-127`

### 3.3 最大法术位（Max Spell Slots）

智力分段决定上限：
- `intelligence <= 3 -> 1`
- `<= 7 -> 2`
- `<= 12 -> 3`
- `<= 16 -> 5`
- `<= 21 -> 8`
- `else -> 9`

- Python：`PieceAccessor.set_max_spell_slots`
  - `THUAI9-Backend-master/client/client_gRPC/env.py:136-156`
- C#：`Piece.Accessor.SetMaxSpellSlots`
  - `THUAI9-Backend-master/server/server/server/Piece.cs:128-136`

### 3.4 最大行动力（Max Movement）

- `max_movement = dexterity + 0.5 * strength + 10`
- Python 初始化位置：`THUAI9-Backend-master/client/client_gRPC/env.py:940-941`
- C# 初始化位置：`THUAI9-Backend-master/server/server/server/Player.cs:190-191`

---

## 4. 已确认的结算影响（回合/行动中的实际使用）

### 4.1 先攻 / 行动顺序

测试端 Python 实现：双方统一使用敏捷（属性值直接相加，不是阶梯值）：
- `priority = d20 + piece.dexterity`
- `THUAI9-Backend-master/client/client_gRPC/env.py:887-907`

### 4.2 物理攻击：命中判定（是否命中）

Python `execute_attack`：
- `THUAI9-Backend-master/client/client_gRPC/env.py:1011-1065`

规则摘要（按代码实际逻辑）：
- 掷 `d20`；`1` 必失败，`20` 必成功且暴击
- 否则：
  - `attack_throw = d20 + Step(力量) + 优势值`
  - `defense_value = physical_resist + Step(敏捷)`
  - 命中条件：`attack_throw > defense_value`

其中 `Step(x)` 指 `step_modified_func(x)`，详见 2.1。

### 4.3 物理伤害：减伤（豁免/抗性）

服务端 C# 的扣血逻辑在 `Piece.receiveDamage`：
- `THUAI9-Backend-master/server/server/server/Piece.cs:56-86`

规则摘要：
- 物理伤害：`real = max(0, raw_damage - physical_resist)`
- 法术伤害：`real = max(0, raw_damage - magic_resist)`

注意：这里的减伤只使用 `physical_resist / magic_resist`，不包含“敏捷阶梯调整值”。也就是说：
- **敏捷的阶梯调整值只用于“是否命中”的对抗，不参与“减伤”。**

---

## 5. 与装备（武器/防具）的关系（与天赋属性并列影响强度）

装备直接决定基础伤害与基础豁免（抗性）：

- 武器（物伤/法伤/范围）：`THUAI9-Backend-master/server/server/server/Player.cs:15-66`
- 防具（物理豁免/法术豁免/行动力修正）：`THUAI9-Backend-master/server/server/server/Player.cs:68-98`

现状提示：当前后端代码里“力量直接加物理伤害”并不存在（物理伤害主要由武器表决定）。

---

## 6. 已知差异与待统一点

### 6.1 服务端先攻实现存在不一致（后端 bug，按约定由后端修复）

服务端 `SetupBattle` 里：玩家1 使用了 `d20 + intelligence`，玩家2 使用 `d20 + dexterity`：
- `THUAI9-Backend-master/server/server/server/env.cs:60-87`

按当前约定：先攻应统一按敏捷（与 Python 测试端一致）。该问题由后端修复，测试端不在此处兜底改写规则。

### 6.2 “普通法术攻击”的命中/对抗口径

当前后端 `executeSpell / ApplySpellEffect` 没有做“命中对抗/豁免对抗”，伤害效果直接按 `baseValue` 扣血：
- Python：`THUAI9-Backend-master/client/client_gRPC/env.py:1216-1233`
- C#：`THUAI9-Backend-master/server/server/server/env.cs:360-409`

若玩法希望存在“法术命中/法术豁免对抗”，需要后端明确并补齐：
- 使用哪种属性修正（智力阶梯？）
- 防御端用 `magic_resist` 还是 `magic_resist + 某属性阶梯`
- 是否存在大成功/大失败

---

## 7. UI 建议（dev_test 属性设置/行动设置）

- UI 展示“命中对抗”相关公式时，应引用 2.1 的 Step Modified（阈值 10/20/30）这一套。
- UI 展示“行动位/法术位”时，建议同时展示“当前/上限”，因为上限由力量/智力派生（见第 3 章）。
