# 职业系统设计与现状对照（开发细化）

## 0. 适用范围与说明

- 本文档只讨论“职业（Warrior/Mage/Archer）”在玩法侧的期望语义，以及后端（C#）与 Python `env.py` 的当前落地情况。
- 目标：
  - 把“职业由什么决定、影响哪些属性/限制”总结成可实现的清单。
  - 对比玩法文档与当前实现，标注缺口与潜在 bug，便于你后续迭代职业系统。

---

## 1. 玩法文档中的职业定义（期望）

> 来源：根目录 `warchess_plan (1).md`

### 1.1 职业是什么

- “人物的职业（取决于所选武器）”。
- 初始化流程强调：
  - **一定要先选择武器再选择防具**。
  - **通过武器限制防具选择**。
  - **武器实际上决定棋子的职业，必须限制其防御属性**。

### 1.2 职业影响哪些内容（文档层面）

文档原话更偏“由武器/防具/属性共同决定战斗力”，职业在文档里更像“武器类型的别名”，主要会影响：

- 攻击范围、伤害类型与伤害值（由武器决定）。
- 防具可选范围（由职业/武器决定）。
- “能发动的法术列表”（文档描述里更强调由智力决定，职业影响较弱/甚至不区分职业）。

---

## 2. 后端与 Python 当前实现：职业从哪里来

### 2.1 C# 后端（server）

#### 2.1.1 职业字段

- `Piece.type` 为字符串（例如 `"Warrior"/"Mage"/"Archer"`）。
- 映射逻辑在 `server/server/server/Piece.cs`：
  - `weapon==1 or 2` → `Warrior`
  - `weapon==3` → `Archer`
  - `weapon==4` → `Mage`

#### 2.1.2 武器对属性的影响

- 在 `server/server/server/Player.cs` 的 `SetWeapon`：

| weapon | 名称 | 物伤 | 法伤 | 范围 |
| --- | --- | ---:| ---:| ---:|
| 1 | 长剑 | 18 | 0 | 5 |
| 2 | 短剑 | 24 | 0 | 3 |
| 3 | 弓 | 16 | 0 | 9 |
| 4 | 法杖 | 0 | 22 | 12 |

> 这组数值和 Python `env.py` 保持一致（见 2.2）。

#### 2.1.3 防具对属性的影响（注意：疑似有 bug）

- `Player.cs` 的 `SetArmor` 注释期望：轻甲/中甲/重甲分别提供不同的物抗/法抗与移动修正。
- 但 `Player.cs` 里 **armor==3 的分支写成了修改 physical_damage/magic_damage/range**（看起来像复制粘贴错误），而不是 resist/movement：
  - 这会导致“重甲”把伤害/射程改坏，且并未提升抗性。

建议：职业系统继续开发前先确认 `SetArmor` 的真实意图（以玩法文档和 Python 实现为准），再决定修复。

### 2.2 Python 后端（client_gRPC/env.py）

#### 2.2.1 职业字段

- `Piece.type` 也是字符串。
- 映射逻辑在 `PieceAccessor.set_type_to`：
  - `1/2 → Warrior`，`3 → Archer`，`4 → Mage`

#### 2.2.2 武器与防具

- `Player.set_weapon` 与 `Player.set_armor`：

武器表（同 C#）：

| weapon | 名称 | 物伤 | 法伤 | 范围 |
| --- | --- | ---:| ---:| ---:|
| 1 | 长剑 | 18 | 0 | 5 |
| 2 | 短剑 | 24 | 0 | 3 |
| 3 | 弓 | 16 | 0 | 9 |
| 4 | 法杖 | 0 | 22 | 12 |

防具表（Python 侧实现符合注释期望）：

| armor | 名称 | 物抗 | 法抗 | 移动力影响 |
| --- | --- | ---:| ---:| ---:|
| 1 | 轻甲 | 8 | 10 | +3 |
| 2 | 中甲 | 15 | 13 | 0 |
| 3 | 重甲 | 23 | 17 | -3 |

并且 Python 初始化输入里明确限制：
- **法杖（weapon=4）只能配轻甲（armor=1）**。

---

## 3. 职业与“可用法术列表”的实现现状

> 关键点：目前“职业差异”在代码里主要体现在 `SpellFactory.get_available_spells(piece)` 的筛选逻辑。

### 3.1 Python `utils.py` 的职业筛选

- `SpellFactory.get_available_spells(piece)`：
  - Warrior：筛 physical（或 BUFF）
  - Mage：筛 fire/ice/lightning（或 DAMAGE/DEBUFF）
  - Archer：只允许 `Arrow Hit`、`Trap`、或 `MOVE`
- 然后再按智力限制可用法术数量：
  - `max_spells = piece.intelligence // 5 + 1`

### 3.2 与玩法文档的差异

- 玩法文档里更强调“智力越高法术越多更强”，但没有强制“职业决定法术类型”。
- 当前实现已经把“职业 → 可用法术集合”写死了（并且筛选条件包含一些目前不存在的法术类型，如 BUFF/DEBUFF、ICE/LIGHTNING）。

建议：
- 先决定“职业是否真的限制法术池”这一玩法立场。
  - 若是：需要补齐 BUFF/DEBUFF、冰/雷系法术，才能体现 Mage 的设计。
  - 若否：应把 `get_available_spells` 改为主要按智力限制数量/强度，而不是强筛类型。

---

## 4. dev_test 可视化侧（当前支持情况）

- 左上信息面板：会显示 `Piece.type`（战士/法师/弓手）。
- 棋盘棋子标签：会用 emoji 显示职业（⚔️/🪄/🏹）。
- 法术下拉：目前处于“测试补齐全量法术池”的策略（保证调试不缺选项）。

---

## 5. 对照总结：已实现 vs 缺失

### 已实现（可用）

- 职业字段 `Piece.type`：C# 与 Python 都已具备，且由武器选择决定。
- 武器数值表：C# 与 Python 基本一致。
- Python 侧“法杖只能轻甲”限制：已实现。

### 主要缺口/风险

- C# `SetArmor` 疑似实现错误（重甲分支改的是伤害/射程而不是抗性/移速）。
- 职业对法术池的限制逻辑与玩法文档立场不一致（目前更强约束、且依赖未实现的法术类型）。

---

## 6. 参考来源

- 玩法文档：`warchess_plan (1).md`
- C#：`THUAI9-Backend-master/server/server/server/Piece.cs`
- C#：`THUAI9-Backend-master/server/server/server/Player.cs`
- Python：`THUAI9-Backend-master/client/client_gRPC/env.py`
- Python：`THUAI9-Backend-master/client/client_gRPC/utils.py`
