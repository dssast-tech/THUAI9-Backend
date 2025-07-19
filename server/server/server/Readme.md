# 游戏策略函数设计指南

本文档将指导您如何设计自己的策略函数并在游戏中使用不同的输入模式。

## 目录

- [项目概要](#项目概要)
- [输入模式概述](#输入模式概述)
- [如何切换输入模式](#如何切换输入模式)
- [设计自定义策略函数](#设计自定义策略函数)
  - [初始化策略函数](#初始化策略函数)
  - [行动策略函数](#行动策略函数)
- [重要数据结构](#重要数据结构)
- [示例策略](#示例策略)
- [项目整体结构说明](#项目整体结构说明)

## 项目概要
本项目为软件学院THUAI-8的服务器端代码，使用C#语言开发，主要负责游戏逻辑的后端运行，同时也支持本地的调试和游玩。

当前，该server将作为游戏试玩版向选手公布，选手可以修改代码在本地运行自己的AI，或者在cmd中手动熟悉游戏。但是在之后的正式比赛中，选手将使用c++/python编写AI。


## 输入模式概述

游戏系统支持三种不同的输入模式：

1. **控制台输入**：通过命令行交互获取玩家输入
2. **函数式本地输入**：通过自定义策略函数来运行AI输入
3. **远程输入**：适配GRPC框架的远程输入（目前不支持，在最终线上评测时会使用）

## 如何切换输入模式

在`env.cs`文件的`initialize`函数中，您可以通过修改以下代码来切换输入模式：

```csharp
// 默认设置玩家1为控制台输入
inputMethodManager.SetConsoleInputMethod(1);

// 设置玩家2为本地函数输入，使用攻击型策略
inputMethodManager.SetFunctionLocalInputMethod(2, 
    StrategyFactory.GetAggressiveInitStrategy(), 
    StrategyFactory.GetAggressiveActionStrategy());

// 其他可能的设置方式：
// 设置玩家1为本地函数输入，使用防御型策略
// inputMethodManager.SetFunctionLocalInputMethod(1,
//     StrategyFactory.GetDefensiveInitStrategy(),
//     StrategyFactory.GetDefensiveActionStrategy());

// 设置玩家2为本地函数输入，使用法师型策略
// inputMethodManager.SetFunctionLocalInputMethod(2,
//     StrategyFactory.GetMageInitStrategy(),
//     StrategyFactory.GetMageActionStrategy());

// 设置玩家1为本地函数输入，使用随机策略
// inputMethodManager.SetFunctionLocalInputMethod(1,
//     StrategyFactory.GetRandomInitStrategy(),
//     StrategyFactory.GetRandomActionStrategy());

// 设置玩家为远程输入
// inputMethodManager.SetRemoteInputMethod(1);
```

您只需要取消注释相应的行，或者根据需要修改输入方式设置。

## 设计自定义策略函数

### 初始化策略函数

初始化策略函数用于在游戏开始时设置棋子的属性和位置。函数签名如下：

```csharp
Func<InitGameMessage, InitPolicyMessage> 
```

该函数接收一个`InitGameMessage`参数，返回一个`InitPolicyMessage`对象。

#### InitGameMessage包含：

- `pieceCnt`：可放置的棋子数量
- `id`：玩家ID（1或2）
- `board`：棋盘对象，包含棋盘大小和格子状态信息

#### InitPolicyMessage包含：

- `pieceArgs`：棋子参数列表，每个`pieceArg`定义一个棋子的属性

#### pieceArg包含：

- `strength`：力量值（影响物理攻击）
- `intelligence`：智力值（影响法术）
- `dexterity`：敏捷值（影响闪避）
- `equip`：装备选择，格式为`new Point(武器类型, 防具类型)`
  - 武器类型：1-长剑, 2-短剑, 3-弓, 4-法杖
  - 防具类型：1-轻甲, 2-中甲, 3-重甲
- `pos`：初始位置，格式为`new Point(x, y)`

**注意**：
- 所有属性值之和不能超过30
- 法杖(4)只能搭配轻甲(1)
- 玩家1和玩家2应该分别在棋盘的对立面放置棋子

### 行动策略函数

行动策略函数用于在游戏进行中决定棋子的行动。函数签名如下：

```csharp
Func<Env, actionSet>
```

该函数接收游戏环境`Env`对象，返回一个`actionSet`对象。

#### Env包含：

- `current_piece`：当前行动的棋子
- `action_queue`：所有棋子的行动队列
- `board`：棋盘对象
- `player1`/`player2`：玩家对象
- `round_number`：当前回合数

#### actionSet包含：

- `move`：是否移动（布尔值）
- `move_target`：移动目标位置，格式为`new Point(x, y)`
- `attack`：是否攻击（布尔值）
- `attack_context`：攻击上下文，包含攻击者、目标等信息
- `spell`：是否使用法术（布尔值）
- `spell_context`：法术上下文，包含施法者、法术类型等信息

## 重要数据结构

### Point结构

```csharp
struct Point
{
    public int x, y;
}
```

### AttackContext结构

```csharp
struct AttackContext
{
    public Piece attacker;       // 攻击发起者
    public Piece target;         // 攻击目标
    public AttackType attackType;// 攻击类型（物理/法术/卓越等）
    public Point attackPosition; // 攻击发起位置
    // 其他字段略
}
```

### SpellContext结构

```csharp
struct SpellContext
{
    public Piece caster;         // 施法者
    public Spell spell;          // 关联的法术数据模板
    public Piece target;         // 单体目标（当targetType=Single时使用）
    public Area targetArea;      // 区域目标（圆心+半径）
    public bool isDelaySpell;    // 是否为延时法术
    // 其他字段略
}
```

### Spell结构

```csharp
struct Spell
{
    public int id;                      // 法术ID
    public string name;                 // 法术名称
    public string description;          // 法术描述
    public SpellEffectType effectType;  // 法术效果类型
    public int baseValue;               // 基础伤害/治疗/效果值
    public int range;                   // 施法距离
    public int areaRadius;              // 作用半径（0为单体）
    // 其他字段略
}
```

### Area类

```csharp
class Area
{
    public int x { get; set; }
    public int y { get; set; }
    public int radius { get; set; }
}
```

## 示例策略

系统内置了几种预定义的策略，这些策略函数由AI生成，不保证行动合法性，但您可以直接使用以进行简单测试：

1. **攻击型策略**：高力量、中敏捷、低智力，偏向前线位置
   ```csharp
   StrategyFactory.GetAggressiveInitStrategy()
   StrategyFactory.GetAggressiveActionStrategy()
   ```

2. **防御型策略**：中力量、高敏捷、中智力，偏向后方位置
   ```csharp
   StrategyFactory.GetDefensiveInitStrategy()
   StrategyFactory.GetDefensiveActionStrategy()
   ```

3. **法师型策略**：低力量、中敏捷、高智力，中间位置
   ```csharp
   StrategyFactory.GetMageInitStrategy()
   StrategyFactory.GetMageActionStrategy()
   ```

4. **随机策略**：随机选择上述三种策略之一
   ```csharp
   StrategyFactory.GetRandomInitStrategy()
   StrategyFactory.GetRandomActionStrategy()
   ```

您可以查看`LocalInput.cs`中的`StrategyFactory`类了解这些策略的具体实现，并以此为基础设计自己的策略函数。

## 项目整体结构说明

项目由以下主要文件组成，各自承担不同的功能，您不必理解其中全部运行逻辑：

### 核心文件

- **env.cs**: 环境类，游戏的核心控制器，管理所有游戏逻辑和状态。包含游戏初始化、回合步进和主循环的实现。

- **LocalInput.cs**: 输入系统的实现，包含三种输入方法（控制台、函数式本地、远程）和`StrategyFactory`类，提供各种预定义策略。

- **Program.cs**: 程序入口点，启动游戏服务器和gRPC服务。

- **board.cs**: 棋盘类，维护棋盘状态、棋子位置和移动逻辑。包含路径查找算法和高度地图。

- **Player.cs**: 玩家类，管理玩家的棋子集合和初始化逻辑。

- **Piece.cs**: 棋子类，定义棋子的属性、行动能力和状态。

### 辅助文件

- **utils.cs**: 包含各种辅助数据结构，如Point、ActionSet、AttackContext、SpellContext等。

- **GameMessage.cs**: 定义与游戏通信相关的消息结构，用于输入系统和游戏逻辑之间的交互。


### 通信相关（用于远程模式）

- **ProtoConverter.cs**: 负责在不同数据格式之间进行转换

- **ServerCommunicator.cs**: 实现gRPC服务接口，处理远程客户端的请求。

### 前端相关（用于输出前端回放的log文件）

- **LogConverter.cs**: 用于生成和保存游戏日志，记录游戏过程。

- **FrontClasses.cs**: 前端格式的类定义。

### 配置文件

- **BoardCase/**: 包含棋盘布局的文本文件，定义棋盘的大小、地形和高度信息。（目前仅支持一种棋盘）


