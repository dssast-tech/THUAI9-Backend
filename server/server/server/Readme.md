# Warchess Server 项目说明文档

## 项目概述

本项目是一个战棋游戏服务端，基于 **ASP.NET Core + gRPC** 实现，目标框架为 **.NET 8.0**。

服务端负责：
- 管理游戏核心逻辑（地图、棋子、战斗、法术）
- 通过 **gRPC** 与 AI 客户端（玩家 Agent）进行双向通信
- 输出 **JSON 格式的回放日志**供前端渲染使用
- 支持本地输入（控制台/函数策略）和远程输入（gRPC）两种模式

---

## 编译与运行

### 依赖环境

- .NET 8.0 SDK
- NuGet 包（自动还原）：
  - `Google.Protobuf 3.30.2`
  - `Grpc.AspNetCore 2.71.0`
  - `Grpc.Tools 2.71.0`

### 编译

```bash
dotnet build
```

或构建 Release 版本：

```bash
dotnet build -c Release
```

### 运行

```bash
dotnet run
```

默认监听地址：`http://localhost:50051`，可通过命令行参数覆盖：

```bash
dotnet run -- --urls http://0.0.0.0:50051
```

若 `--urls` 的 host 为 `0.0.0.0`，则监听所有网卡；否则仅监听本地回环。

---

## 代码文件结构与职责

| 文件 | 职责说明 |
|------|----------|
| `Program.cs` | 程序入口，配置 Kestrel HTTP/2 服务器、注册 gRPC 服务与 DI 容器，启动游戏主循环 |
| `env.cs` | 游戏核心控制器（`Env` 类），管理行动队列、延时法术、游戏循环、攻击/法术逻辑、轮结算 |
| `Piece.cs` | 棋子类，持有所有棋子属性；通过内部 `Accessor` 类限制对属性的写权限，只允许 `Env` 层修改 |
| `Player.cs` | 玩家类，持有棋子列表，负责棋子初始化验证与装备/属性设置 |
| `board.cs` | 棋盘类，维护地图网格（`Cell[,]`）与高度图（`int[,]`），实现 A* 寻路和棋子位移 |
| `utils.cs` | 辅助数据结构，包含 `Point`、`actionSet`、`AttackContext`、`SpellContext`、`Spell`、`Area`、`SpellFactory`、相关枚举 |
| `GameMessage.cs` | 通信消息结构定义：`InitGameMessage`、`InitPolicyMessage`、`GameMessage`、`PolicyMessage`、`pieceArg` |
| `ServerCommunicator.cs` | gRPC 服务实现（`GameServiceImpl`），处理客户端连接、初始化、行动接收、游戏状态广播；同时包含 `InitWaiter` 和 `ActionWaiter` 同步辅助类 |
| `LocalInput.cs` | 本地输入系统：`IInputMethod` 接口、`ConsoleInputMethod`（控制台输入）、`FunctionLocalInputMethod`（函数策略注入）、`RemoteInputMethod`（gRPC 占位）、`InputMethodManager`、`StrategyFactory`（内置 AI 策略） |
| `ProtoConverter.cs` | Proto 消息与 C# 内部对象的双向转换工具类（`Converter`） |
| `LogConverter.cs` | 将游戏过程序列化为前端消费的 JSON 格式（`log.json`），记录地图、棋子初态、每轮动作与统计 |
| `FrontClasses.cs` | 前端 JSON 数据结构定义：`GameData`、`GameRound`、`BattleAction`、`SoldierData` 等，供 `LogConverter` 序列化使用 |
| `Protos/message.proto` | gRPC 接口定义文件，定义所有消息格式和 `GameService` 服务 |
| `BoardCase/case1.txt` | 地图数据文件，第一行为宽高，后接 grid 状态矩阵和高度图矩阵 |

---

## 接口说明

### 一、gRPC 接口（与 AI 客户端通信）

协议文件：`Protos/message.proto`，服务名 `GameService`，默认端口 **50051**，使用 HTTP/2 明文传输。

#### 1. `SendInit`

客户端连接时第一步调用，获取玩家 ID 和地图信息。

**请求 `_InitRequest`：**

```
message _InitRequest {
    string message = 1;  // 预留字段，当前未使用，填空字符串即可
}
```

**响应 `_InitResponse`：**

```
message _InitResponse {
    int32 pieceCnt = 1;   // 棋子数量（当前固定为 1）
    int32 id = 2;         // 服务端分配的玩家 ID（1 或 2，按连接顺序分配）
    _Board board = 3;     // 地图信息
}
```

`_Board` 结构：

```
message _Board {
    int32 width = 1;              // 地图宽度
    int32 height = 2;             // 地图高度
    repeated _Cell grid = 3;      // 展开为一维的格子数组（行优先），共 width*height 个
    repeated int32 height_map = 4; // 展开为一维的高度图，共 width*height 个
    int32 boarder = 5;            // 分界线 y 坐标（= height / 2）
}
```

`_Cell` 结构：

```
message _Cell {
    int32 state = 1;    // -1:禁止, 1:可行走, 2:被占据
    int32 playerId = 2; // 占据该格的玩家ID（-1表示无人）
    int32 pieceId = 3;  // 占据该格的棋子ID（-1表示无棋子）
}
```

---

#### 2. `SendInitPolicy`

在调用 `SendInit` 之后，客户端发送己方棋子的初始化配置。

**请求 `_InitPolicyRequest`：**

```
message _InitPolicyRequest {
    int32 playerId = 1;             // 玩家 ID（由 SendInit 获得）
    repeated _pieceArg pieceArgs = 2; // 每个棋子的初始化参数列表
}
```

`_pieceArg` 结构：

```
message _pieceArg {
    int32 strength = 1;     // 力量（0~30，三属性之和 ≤ 30）
    int32 intelligence = 2; // 智力
    int32 dexterity = 3;    // 敏捷
    _Point equip = 4;       // 装备：equip.x = 武器类型(1-4)，equip.y = 防具类型(1-3)
    _Point pos = 5;         // 初始坐标：pos.x, pos.y
}
```

武器类型：`1=长剑, 2=短剑, 3=弓, 4=法杖`（法杖必须搭配防具类型 1=轻甲）

防具类型：`1=轻甲, 2=中甲, 3=重甲`

**响应 `_InitPolicyResponse`：**

```
message _InitPolicyResponse {
    bool success = 1;  // 是否成功
    string mes = 2;    // 提示消息
}
```

---

#### 3. `BroadcastGameState`（服务端流）

客户端订阅游戏状态推送。服务端在每个棋子行动前广播当前状态，客户端应在连接后立即调用此方法并保持连接。

**请求 `_GameStateRequest`：**

```
message _GameStateRequest {
    int32 playerID = 1; // 客户端的玩家 ID
}
```

**流式响应 `_GameStateResponse`（持续接收）：**

```
message _GameStateResponse {
    int32 currentRound = 1;             // 当前回合数
    int32 currentPlayerId = 2;          // 当前行动棋子所属玩家 ID
    int32 currentPieceID = 3;           // 当前行动棋子的 ID
    repeated _Piece actionQueue = 4;    // 所有存活棋子的行动队列
    _Board board = 5;                   // 当前地图状态
    repeated _SpellContext delayedSpells = 6; // 当前延时法术列表
    bool isGameOver = 7;                // 是否游戏结束
}
```

`_Piece` 结构见 proto 文件，包含棋子的全部属性（血量、攻击、防御、位置、高度等）。

当 `isGameOver = true` 时，客户端应关闭连接。

---

#### 4. `SendAction`

客户端在收到广播、轮到己方棋子行动时，发送行动指令。

**请求 `_actionSet`：**

```
message _actionSet {
    bool move = 1;                    // 是否执行移动
    _Point move_target = 2;           // 移动目标坐标（move=true 时有效）
    bool attack = 3;                  // 是否执行物理攻击
    _AttackContext attack_context = 4; // 攻击上下文（attack=true 时有效）
    bool spell = 5;                   // 是否施放法术
    _SpellContext spell_context = 6;  // 法术上下文（spell=true 时有效）
    int32 playerId = 7;               // 发送方玩家 ID
}
```

`_AttackContext`：

```
message _AttackContext {
    int32 attacker = 1; // 攻击者棋子 ID
    int32 target = 2;   // 被攻击棋子 ID
}
```

`_SpellContext`：

```
message _SpellContext {
    int32 caster = 1;          // 施法者棋子 ID
    int32 spellID = 2;         // 法术 ID（参见 SpellFactory 定义）
    _TargetType targetType = 4; // 目标类型
    int32 target = 5;          // 单体目标棋子 ID（非锁定法术时为 -1）
    _Area targetArea = 6;      // 目标区域（圆心 + 半径）
    int32 spellLifespan = 7;   // 法术持续回合（延时法术时填）
}
```

**响应 `_actionResponse`：**

```
message _actionResponse {
    bool success = 1;  // 是否被接受（仅在该玩家轮次发送时 true）
    string mes = 2;    // 提示消息
}
```

---

#### gRPC 客户端对接流程

```
1. 调用 BroadcastGameState(playerID)  → 建立长连接，等待状态推送
2. 调用 SendInit("")                  → 获取玩家 ID 和地图
3. 调用 SendInitPolicy(playerId, ...) → 发送棋子初始化配置
4. 循环：
   - 接收 _GameStateResponse 推送
   - 若 currentPlayerId == 己方 ID，则调用 SendAction(...)
   - 若 isGameOver == true，则断开连接
```

---

### 二、前端 JSON 接口（回放日志）

游戏结束后，`LogConverter` 将全局游戏数据序列化为 `log.json`，保存在可执行文件的工作目录中。前端通过读取此文件进行回放渲染。

#### 整体结构 `GameData`

```json
{
  "mapdata": { ... },
  "playerData": { ... },
  "soldiersData": [ ... ],
  "gameRounds": [ ... ]
}
```

---

#### `mapdata`（地图数据）

```json
{
  "mapWidth": 20,
  "rows": [
    { "row": [1, 2, 1, ...] },  // 每行为高度图数据（原始值 + 1）
    ...
  ]
}
```

`rows` 数组长度为地图宽度（`width`），每个 `row` 长度为地图高度（`height`），遍历顺序为 x 维度 → y 维度。高度值已在输出时加 1（即地面为 1，高地为 2、3）。

---

#### `playerData`（玩家信息）

```json
{
  "player1": "Red",
  "player2": "Blue"
}
```

---

#### `soldiersData`（棋子初始信息列表）

```json
[
  {
    "ID": 0,
    "soldierType": "Warrior",    // Warrior / Archer / Mage
    "camp": "Red",               // Red / Blue
    "position": { "x": 3, "y": 1, "z": 5 },  // x/z 为平面坐标，y 为高度（已+1）
    "stats": {
      "health": 60,
      "strength": 15,
      "intelligence": 5
    }
  }
]
```

---

#### `gameRounds`（每回合数据列表）

```json
[
  {
    "roundNumber": 1,
    "actions": [ ... ],   // 本回合所有动作列表
    "stats": [ ... ],     // 本回合结束时所有棋子状态
    "score": {
      "redScore": 0,      // 蓝方已死亡棋子数
      "blueScore": 0      // 红方已死亡棋子数
    },
    "end": "false"        // 是否为最终回合 ("true"/"false")
  }
]
```

---

#### `actions`（动作列表）

每个动作为 `BattleAction` 对象，通过 `actionType` 字段区分类型：

**移动（Movement）：**

```json
{
  "actionType": "Movement",
  "soldierId": 0,
  "path": [
    { "x": 3, "y": 1, "z": 5 },
    { "x": 4, "y": 1, "z": 5 }
  ],
  "remainingMovement": 7
}
```

`path` 为 `Vector3Serializable` 数组，`x/z` 为平面坐标，`y` 为高度（已+1）。

**攻击（Attack）：**

```json
{
  "actionType": "Attack",
  "soldierId": 0,
  "targetId": 1,
  "damageDealt": [
    { "targetId": 1, "damage": 12 }
  ]
}
```

`damage` 为实际命中伤害，未命中时为 0。

**法术（Ability）：**

```json
{
  "actionType": "Ability",
  "soldierId": 0,
  "targetPosition": { "x": 8, "y": 1, "z": 10 },
  "damageDealt": [
    { "targetId": 1, "damage": 30 }   // 正数为伤害，负数为治疗
  ]
}
```

**死亡（Death）：**

```json
{
  "actionType": "Death",
  "soldierId": 1
}
```

---

#### `stats`（回合末棋子状态列表）

```json
[
  {
    "soldierId": 0,
    "survived": "true",
    "position": { "x": 4, "y": 1, "z": 5 },
    "Stats": {
      "health": 48,
      "strength": 15,
      "intelligence": 5
    }
  }
]
```

---

## 地图文件格式（BoardCase）

地图文件为纯文本格式，路径为 `BoardCase/case1.txt`，格式如下：

```
<width> <height>
<空行>
<grid 矩阵，共 height 行，每行 width 个以逗号分隔的整数>
  -1: 不可通行
   1: 可通行
<空行>
<height_map 矩阵，共 height 行，每行 width 个以逗号分隔的整数>
  高度值：0=地面，1=一阶高地，2=二阶高地，-1=不可通行区域的高度（无实义）
```

---

## 内置法术列表（SpellFactory）

| ID | 名称 | 效果类型 | 伤害类型 | 基础值 | 范围 | 区域半径 | 是否延时 | 是否锁定 |
|----|------|---------|---------|-------|------|---------|---------|---------|
| 1 | Fireball | Damage | Fire | 30 | 2 | 5 | 否 | 否 |
| 2 | Heal | Heal | None | 30 | 2 | 4 | 否 | 是 |
| 3 | arrowHit | Damage | Physical | 30 | 1 | 7 | 否 | 是 |
| 4 | trap | Damage | Physical | 30 | 1 | 0 | 是（2回合）| 否 |
| 5 | move | Move | - | - | 100 | 100 | 否 | 是 |

---

## 核心游戏规则概要

- 每轮所有棋子各行动一次，按**先攻值**（`1d20 + 敏捷值`）排序
- 单棋子每轮可执行：移动、攻击、施法（各最多一次，均消耗行动位）
- **物理攻击命中判定**：`1d20 + 力量调整值 + 优势值 > 目标物理豁免 + 目标敏捷调整值`
- 1 大失败，20 大成功（无视判定直接生效）
- 暴击伤害翻倍
- **死亡检定**：血量 ≤ 0 时掷 1d20，20 则回复 1 HP，否则死亡
- 达到最大回合数（100轮）未分胜负时，按双方总剩余血量判定
- 游戏结束后输出 `log.json` 回放文件


## 开发进度与注意点
1. 当前server代码可以编译运行，可与client交互
2. 由于存在多种装备和机制，测试很不完全，存在相当数量的错误，以下为AI总结的部分错误
```
严重错误（会导致运行结果明显错误）
1.Player.cs SetArmor 重甲分支写错了 setter：case 3 调用的是 SetPhysicalDamageTo/SetMagicDamageTo/SetRangeTo，实际应是 SetPhysicalResistTo/SetMagicResistTo/SetMaxMovementBy(-3)，穿重甲的棋子完全无法获得防御加成。
2. env.cs 先攻计算双方用了不同属性：player1 用 intelligence，player2 用 dexterity，双方先攻规则不对等，正确应都用敏捷（dexterity）。
3. env.cs Heal 效果 Math.Max 应为 Math.Min：Math.Max(target.health + baseValue, target.max_health) 逻辑相反，治疗后血量应当不超过上限（Min），当前实现会在某些情况下超出上限或逻辑混乱。
4. ProtoConverter.cs 法术目标未赋值：SpellContext 转换中 if (proto.Target != -1) env.action_queue.Find(...) 的查找结果没有赋值给 temp.target，导致远程模式下所有单体法术目标永远为 null，法术施放时会报空引用。
🟡 设计风险（不一定崩溃，但行为可能偏离预期）
1. RollDice 每次 new Random()，同一毫秒多次调用会产生相同随机数，实际骰子缺乏随机性；且 n（骰子数量）参数未被使用，实际只投了 1 次骰子。
2. 延时法术每个小回合（每个棋子行动后）都倒计时，而非按"轮"处理，法术触发频率可能是预期的若干倍。
3. 移动扣行动位，使得只有 1 个行动位的棋子（力量≤13）无法同时移动和攻击，需确认是否为有意设计。
4. SendInitPolicy gRPC 并发无保护，多棋子场景下有竞态条件风险。
LogConverter 高度图的遍历轴向需与前端对齐确认，外层遍历是 x 维度，每行 row 对应某一 x 列，不是通常意义上的"行"。
``` 