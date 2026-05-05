# THUAI9 客户端 API 文档

本文档为比赛选手提供客户端 Python 代码的完整 API 参考。

---

## 目录

0. [快速开始指南](#0-快速开始指南)
1. [核心数据结构](#1-核心数据结构)
2. [环境类 (Environment)](#2-环境类-environment)
3. [棋子相关类](#3-棋子相关类)
4. [棋盘类 (Board)](#4-棋盘类-board)
5. [策略辅助函数 (strategy_utils.py)](#5-策略辅助函数-strategy_utilspy)
6. [策略工厂 (strategy_factory.py)](#6-策略工厂-strategy_factorypy)
7. [输入方法](#7-输入方法)
8. [枚举类型](#8-枚举类型)
9. [法术系统](#9-法术系统)

---

## 0. 快速开始指南

### 0.1 文件结构说明

```
client/
├── local_client.py      # 本地测试入口（选手主要使用）
├── main.py              # saiblo评测入口（选手仅需修改选中策略）
├── env.py               # 游戏环境核心类
├── strategy_factory.py  # 策略工厂（选手需要修改的文件）
├── strategy_utils.py    # 策略辅助函数（一些辅助智能体开发的函数，详见第5节，可使用也可修改）
├── utils.py             # 工具类和枚举定义
└── local_input.py       # 输入方法管理
```

### 0.2 如何进行本地测试

#### 方式一：控制台双人对战（测试棋盘和规则）

```bash
cd client/client
python local_client.py --mode local --board ./BoardCase/case1.txt
```

**参数说明：**
| 参数 | 说明 | 可选值 | 默认值 |
|------|------|--------|--------|
| `--mode` | 运行模式 | `local` / `function` | `local` |
| `--board` | 棋盘文件路径 | 任意有效路径 | `./BoardCase/case1.txt` |

#### 方式二：AI 对战（测试你的策略）

```bash
# 使用预定义策略进行 AI 对战
python local_client.py --mode function --strategy aggressive
python local_client.py --mode function --strategy defensive
python local_client.py --mode function --strategy mcts --mcts-simulations 25
```

**参数说明：**
| 参数 | 说明 | 可选值 | 默认值 |
|------|------|--------|--------|
| `--mode` | 运行模式 | `function` | - |
| `--strategy` | AI 策略类型 | `aggressive` / `defensive` / `mcts` | `aggressive` |
| `--mcts-simulations` | MCTS 模拟次数 | 正整数 | 25 |

### 0.3 选手需要修改的文件

**主要修改文件：`strategy_factory.py`**

你需要实现以下两个函数：

1. **初始化策略函数** - 配置你的棋子属性和初始位置
   ```python
   def your_init_strategy(init_message: InitGameMessage) -> List[PieceArg]:
       # 实现你的初始化逻辑
       return piece_args
   ```

2. **行动策略函数** - 决定每个回合的行动
   ```python
   def your_action_strategy(env: Environment) -> ActionSet:
       # 实现你的行动决策逻辑
       return action
   ```

### 0.4 使用自定义策略

选手推荐做法是：**新增一对“自定义策略函数”**，而不是修改仓库自带的示例策略。

#### 第一步：在 `client/client/strategy_factory.py` 新增两个工厂方法

在 `StrategyFactory` 类中新增：
- `get_custom_init_strategy() -> Callable[[InitGameMessage], List[PieceArg]]`
- `get_custom_action_strategy() -> Callable[[Environment], ActionSet]`

示例（只展示结构，具体逻辑由选手实现）：

```python
from typing import Callable, List
from env import Environment, InitGameMessage
from utils import ActionSet, PieceArg

class StrategyFactory:
    @staticmethod
    def get_custom_init_strategy() -> Callable[[InitGameMessage], List[PieceArg]]:
        def strategy(init_message: InitGameMessage) -> List[PieceArg]:
            piece_args: List[PieceArg] = []
            # TODO: 构造 piece_args（长度应为 init_message.piece_cnt）
            return piece_args
        return strategy

    @staticmethod
    def get_custom_action_strategy() -> Callable[[Environment], ActionSet]:
        def strategy(env: Environment) -> ActionSet:
            action = ActionSet()
            # TODO: 填 action.move / action.attack / action.spell 等字段
            return action
        return strategy
```

#### 第二步：让入口使用你的自定义策略


> 下面两处改法都只是在入口里“取策略的地方”替换为 `get_custom_*`，其余流程不变。

**本地对战入口**：`client/client/local_client.py`

把 `main()` 里 function 模式取策略的那行（70行）替换为：

```python
init_strategy = StrategyFactory.get_custom_init_strategy()
action_strategy = StrategyFactory.get_custom_action_strategy()
```

然后保持原来的绑定逻辑：

```python
env.input_manager.set_function_input_method(1, init_strategy, action_strategy)
env.input_manager.set_function_input_method(2, init_strategy, action_strategy)
```

**Saiblo 入口**：`client/client/main.py`

注：Saiblo评测时不依赖命令行参数，因此修改main.py时无需考虑这一部分

把 `run()` 开头“选择策略”的整段（58~66行）替换为：

```python
init_strategy = StrategyFactory.get_custom_init_strategy()
action_strategy = StrategyFactory.get_custom_action_strategy()
```

---

## 1. 核心数据结构

### 1.1 Point - 坐标点

```python
from utils import Point

# 构造函数
Point(x: int, y: int)

# 属性
point.x  # X 坐标
point.y  # Y 坐标
```

### 1.2 ActionSet - 行动集合

表示一个回合中的完整行动（移动、攻击、法术）。

```python
from utils import ActionSet

action = ActionSet()

# 属性
action.move              # bool - 是否移动（注意：实现里该字段不是构造函数必带字段，使用前需要显式赋值，例如 action.move = True/False）
action.move_target       # Point - 移动目标位置
action.attack            # bool - 是否攻击
action.attack_context    # AttackContext - 攻击上下文
action.spell             # bool - 是否施法
action.spell_context     # SpellContext - 法术上下文
```

### 1.3 PieceArg - 棋子初始化参数

```python
from utils import PieceArg

piece_arg = PieceArg()

# 属性
piece_arg.strength      # int - 力量属性 (0-30，总和不超过30)
piece_arg.dexterity     # int - 敏捷属性 (0-30，总和不超过30)
piece_arg.intelligence  # int - 智力属性 (0-30，总和不超过30)
piece_arg.equip         # Point - 装备 (x=武器类型1-4, y=防具类型1-3)
piece_arg.pos           # Point - 初始位置
```

### 1.4 InitGameMessage - 初始化游戏消息

初始化策略函数的输入参数，包含游戏初始化信息。

```python
from utils import InitGameMessage

# 属性
init_message.id           # int - 玩家ID (1 或 2)
init_message.piece_cnt    # int - 棋子数量
init_message.board        # Board - 棋盘对象
```

### 1.5 AttackContext - 攻击上下文

```python
from utils import AttackContext

ctx = AttackContext()

# 属性
ctx.attacker         # Piece - 攻击者
ctx.target           # Piece - 目标
ctx.damage_dealt     # int - 造成的伤害
ctx.attackPosition   # Point - 攻击位置
```

### 1.6 SpellContext - 法术上下文

```python
from utils import SpellContext

ctx = SpellContext()

# 属性
ctx.caster           # Piece - 施法者
ctx.target           # Piece - 目标
ctx.spell            # Spell - 法术对象
ctx.target_area      # Area - 目标区域
ctx.is_delay_spell   # bool - 是否为延时法术
ctx.spell_lifespan   # int - 延时法术持续回合
```

### 1.7 Area - 区域

```python
from utils import Area

area = Area(x: int, y: int, radius: int)

# 方法
area.contains(point: Point) -> bool  # 检查点是否在区域内
```

---

## 2. 环境类 (Environment)

游戏核心控制器，管理整个游戏流程。

### 2.1 构造函数

```python
from env import Environment

# 参数
# local_mode: bool - 是否为本地模式 (默认 True)
# if_log: int - 日志控制，1启用，0禁用 (默认 1)
env = Environment(local_mode=True, if_log=1)
```

### 2.2 初始化方法

```python
# 初始化游戏
env.initialize(board_file: str = "./BoardCase/case1.txt") -> None

# 仅加载棋盘（供外部配置棋子使用）
env.init_board_only(board_file: Optional[str] = None) -> None

# 设置战斗（双方棋子配置后调用）
env.setup_battle_host() -> None
```

### 2.3 游戏流程控制

```python
# 运行完整游戏
env.run(board_file: str = "./BoardCase/case1.txt") -> None

# 单回合步进
env.step() -> None

# 回合开始
env.begin_turn_host() -> None

# 执行行动
env.apply_action_host(action: ActionSet) -> None

# 回合结束
env.end_turn_host() -> None
```

### 2.4 状态查询

```python
# 获取当前行动棋子
env.current_piece  # Piece - 当前行动的棋子

# 获取棋盘
env.board  # Board - 棋盘对象

# 获取玩家
env.player1  # Player - 玩家1
env.player2  # Player - 玩家2

# 获取行动队列
env.action_queue  # np.ndarray - 行动顺序队列

# 游戏状态
env.is_game_over       # bool - 游戏是否结束
env.round_number       # int - 当前回合数
env.is_battle_initialized  # bool - 战斗是否已初始化
```

### 2.5 棋子操作

```python
# 获取当前棋子可用的法术列表
env.get_available_spells(piece: Optional[Piece] = None) -> List[Spell]

# 获取法术可选的目标列表
env.get_spell_targets(spell: Spell, caster: Optional[Piece] = None) -> List[Piece]

# 检查是否在攻击范围内
env.is_in_attack_range(attacker: Piece, target: Piece) -> bool

# 计算优势值（高度+环境）
env.calculate_advantage_value(attacker: Piece, target: Piece) -> float
```

### 2.6 辅助方法

```python
# 投掷骰子
env.roll_dice(n: int, sides: int) -> int

# 可视化棋盘
env.visualize_board() -> None
```

---

## 3. 棋子相关类

### 3.1 Piece - 棋子

```python
from env import Piece

piece = Piece()

# 属性
piece.id              # int - 棋子ID
piece.type            # str - 棋子类型 ("Warrior", "Mage", "Archer")
piece.team            # int - 队伍 (1 或 2)
piece.position        # Point - 当前位置
piece.height          # int - 当前高度

# 生命值
piece.health          # int - 当前生命值
piece.max_health      # int - 最大生命值

# 属性值
piece.strength        # int - 力量
piece.dexterity       # int - 敏捷
piece.intelligence    # int - 智力

# 战斗属性
piece.physical_damage     # int - 物理伤害
piece.physical_resist     # int - 物理抗性
piece.attack_range        # int - 攻击范围

# 资源
piece.action_points       # int - 当前行动点
piece.max_action_points   # int - 最大行动点
piece.spell_slots         # int - 当前法术位
piece.max_spell_slots     # int - 最大法术位
piece.movement            # float - 当前移动力
piece.max_movement        # float - 最大移动力

# 状态
piece.is_alive        # bool - 是否存活
piece.is_in_turn      # bool - 是否在行动中
piece.is_dying        # bool - 是否濒死
piece.death_round     # int - 死亡回合 (-1 表示未死亡)

# 方法
piece.receive_damage(damage: int, damage_type: str) -> None
piece.get_accessor() -> PieceAccessor
piece.set_action_points(action_points: int) -> None
piece.get_action_points() -> int
```

### 3.2 PieceAccessor - 棋子访问器

用于修改棋子属性的安全接口。

```python
accessor = piece.get_accessor()

# 属性设置方法
accessor.set_health_to(value: int)
accessor.set_max_health_to(value: int)
accessor.set_strength_to(value: int)
accessor.set_dexterity_to(value: int)
accessor.set_intelligence_to(value: int)
accessor.set_physical_damage_to(value: int)
accessor.set_physical_resist_to(value: int)
accessor.set_attack_range_to(value: int)
accessor.set_max_movement_to(value: float)
accessor.set_movement_to(value: float)
accessor.set_position(new_pos: Point)
accessor.set_team_to(value: int)
accessor.set_alive(value: bool)

# 属性调整方法
accessor.change_health_by(delta: int)
accessor.change_action_points_by(delta: int)
accessor.change_spell_slots_by(delta: int)
accessor.set_max_movement_by(value: float)
accessor.set_physic_resist_by(value: int)

# 自动设置方法
accessor.set_max_action_points()  # 根据力量自动设置
accessor.set_max_spell_slots()    # 根据智力自动设置
```

### 3.3 Player - 玩家

```python
from env import Player

player = Player()

# 属性
player.id          # int - 玩家ID (1 或 2)
player.pieces      # np.ndarray - 玩家棋子列表
player.piece_num   # int - 棋子数量
player.feature_total  # int - 属性点总和限制 (30)

# 方法
player.set_weapon(weapon: int, piece: Piece)  # 设置武器
player.set_armor(armor: int, piece: Piece)    # 设置防具

# 静态方法
Player.validate_piece_init(board, player_id, arg, index, occupied_same_player)  # 验证棋子初始化
```

---

## 4. 棋盘类 (Board)

```python
from env import Board

board = Board(if_log: int = 1)

# 属性
board.width      # int - 棋盘宽度
board.height     # int - 棋盘高度
board.grid       # 2D array - 格子状态
board.height_map # 2D array - 高度地图
board.boarder    # int - 边界线位置

# 方法
board.get_width() -> int
board.get_height() -> int

# 移动相关
board.valid_target(piece: Piece, movement: float) -> List[List[int]]
# 返回二维数组，表示每个位置的移动消耗，-1表示不可到达

board.move_piece(piece: Piece, to: Point, movement: float) -> Tuple[List[Point], bool]
# 返回 (path, success) - 路径和是否成功

board.find_shortest_path(piece: Piece, start: Point, goal: Point, movement: float) -> Tuple[List[Point], float]
# 返回 (path, cost) - 路径和消耗

# 状态查询
board.is_occupied(point: Point) -> bool
board.get_height(point: Point) -> int
board.is_within_bounds(point: Point) -> bool
board.get_neighbors(point: Point) -> List[Point]

# 棋子管理
board.remove_piece(piece: Piece) -> None
board.init_pieces_location(player1_pieces, player2_pieces) -> None

# 初始化
board.init_from_file(file_path: str) -> None
```

---

## 5. 策略辅助函数 (strategy_utils.py)

这些函数位于 `strategy_utils.py` 中，用于 AI 策略开发。**选手可以直接使用这些函数，也可以根据需要修改它们。**

### 5.1 get_state_score - 局面评分

```python
from strategy_utils import get_state_score

# 获取当前局面的评分
score = get_state_score(env: Environment) -> float

# 参数：
#   env: Environment - 游戏环境对象

# 返回值：
#   float - 局面评分（当前队伍为正，对手为负）

# 评分因素：
#   - 棋子生命值比例 * 10
#   - 高度 * 0.5
#   - 行动点 * 2
#   - 法术位 * 1.5
#   - 伤害值 * 0.3
#   - 抗性值 * 0.2
```

### 5.2 get_legal_moves - 获取合法移动位置

```python
from strategy_utils import get_legal_moves

# 获取当前棋子所有合法的移动位置
moves = get_legal_moves(env: Environment, piece: Optional[Piece] = None) -> List[Point]

# 参数：
#   env: Environment - 游戏环境对象
#   piece: Optional[Piece] - 棋子对象，默认为当前行动棋子

# 返回值：
#   List[Point] - 合法的移动位置列表
```

### 5.3 get_attackable_targets - 获取可攻击目标

```python
from strategy_utils import get_attackable_targets

# 获取当前棋子可攻击的目标列表
targets = get_attackable_targets(env: Environment, piece: Optional[Piece] = None) -> List[Piece]

# 参数：
#   env: Environment - 游戏环境对象
#   piece: Optional[Piece] - 棋子对象，默认为当前行动棋子

# 返回值：
#   List[Piece] - 可攻击的敌方棋子列表
```

### 5.4 simulate_move - 模拟移动

```python
from strategy_utils import simulate_move

# 模拟移动是否可行
can_move = simulate_move(env: Environment, piece: Piece, target: Point) -> bool

# 参数：
#   env: Environment - 游戏环境对象
#   piece: Piece - 棋子对象
#   target: Point - 目标位置

# 返回值：
#   bool - 是否可以移动到目标位置
```

### 5.5 simulate_attack - 模拟攻击

```python
from strategy_utils import simulate_attack

# 模拟攻击并返回预估伤害
damage = simulate_attack(env: Environment, attacker: Piece, target: Piece) -> float

# 参数：
#   env: Environment - 游戏环境对象
#   attacker: Piece - 攻击方棋子
#   target: Piece - 目标棋子

# 返回值：
#   float - 预估伤害值
```

### 5.6 step_with_action - 步进执行行动

```python
from strategy_utils import step_with_action

# 执行一个回合步进（不改变原环境）
step_with_action(env: Environment, action: ActionSet) -> None

# 参数：
#   env: Environment - 游戏环境对象
#   action: ActionSet - 行动集合

# 注意：此函数会修改 env 对象，用于模拟游戏进程
```

### 5.7 fork_environment - 复制环境

```python
from strategy_utils import fork_environment

# 复制一个环境的副本（用于搜索/模拟）
new_env = fork_environment(env: Environment) -> Environment

# 参数：
#   env: Environment - 要复制的游戏环境对象

# 返回值：
#   Environment - 环境的深拷贝

# 用途：用于 Minimax、Alpha-Beta、MCTS 等搜索算法的模拟
```

---

## 6. 策略工厂 (strategy_factory.py)

**这是选手主要需要修改的文件！** 提供预定义的策略函数，当前已经实现了几种简单的策略方法，可直接使用或作为参考。

### 6.1 初始化策略函数

#### get_aggressive_init_strategy - 攻击型初始化策略

```python
from strategy_factory import StrategyFactory

init_strategy = StrategyFactory.get_aggressive_init_strategy()
# 返回: Callable[[InitGameMessage], List[PieceArg]]

# 输入参数：
#   init_message: InitGameMessage - 初始化游戏消息
#       - init_message.id: int - 玩家ID (1 或 2)
#       - init_message.piece_cnt: int - 棋子数量
#       - init_message.board: Board - 棋盘对象

# 返回值：
#   List[PieceArg] - 棋子初始化参数列表

# 策略特点：
#   - 高力量 (20)
#   - 中敏捷 (8)
#   - 低智力 (2)
#   - 装备：短剑+重甲
#   - 位置：前线路
```

#### get_defensive_init_strategy - 防御型初始化策略

```python
init_strategy = StrategyFactory.get_defensive_init_strategy()
# 返回: Callable[[InitGameMessage], List[PieceArg]]

# 策略特点：
#   - 低力量 (5)
#   - 高敏捷 (15)
#   - 中智力 (10)
#   - 装备：弓+轻甲
#   - 位置：后线路
```

#### get_random_init_strategy - 随机初始化策略

```python
init_strategy = StrategyFactory.get_random_init_strategy()
# 返回: Callable[[InitGameMessage], List[PieceArg]]

# 策略特点：
#   - 随机属性分配
#   - 随机装备选择
#   - 随机位置放置
```

### 6.2 行动策略函数

#### get_aggressive_action_strategy - 攻击型行动策略

```python
action_strategy = StrategyFactory.get_aggressive_action_strategy()
# 返回: Callable[[Environment], ActionSet]

# 输入参数：
#   env: Environment - 游戏环境对象

# 返回值：
#   ActionSet - 行动集合

# 策略逻辑：
#   1. 寻找最近的敌人
#   2. 向敌人移动（选择最接近敌人的合法位置）
#   3. 如果在攻击范围内则攻击
#   4. 不使用法术
```

#### get_defensive_action_strategy - 防御型行动策略

```python
action_strategy = StrategyFactory.get_defensive_action_strategy()
# 返回: Callable[[Environment], ActionSet]

# 策略逻辑：
#   1. 寻找最近的敌人
#   2. 保持距离（不进入敌人攻击范围）
#   3. 使用远程攻击（弓）
#   4. 不使用法术
```

#### get_random_action_strategy - 随机行动策略

```python
action_strategy = StrategyFactory.get_random_action_strategy()
# 返回: Callable[[Environment], ActionSet]

# 策略逻辑：
#   - 随机选择移动位置
#   - 随机选择攻击目标
#   - 随机决定是否使用法术
```

#### get_alpha_beta_action_strategy - Alpha-Beta 剪枝策略

```python
action_strategy = StrategyFactory.get_alpha_beta_action_strategy(max_depth: int = 3)
# 参数：
#   max_depth: int - 搜索深度（默认3）
# 返回: Callable[[Environment], ActionSet]

# 输入参数：
#   env: Environment - 游戏环境对象

# 返回值：
#   ActionSet - 行动集合

# 策略逻辑：
#   1. 使用 Alpha-Beta 剪枝搜索
#   2. 评估函数：get_state_score
#   3. 考虑所有合法移动和攻击
```

#### get_mcts_action_strategy - MCTS 策略

```python
action_strategy = StrategyFactory.get_mcts_action_strategy(simulation_count: int = 10)
# 参数：
#   simulation_count: int - 每个决策点的模拟次数（默认10）
# 返回: Callable[[Environment], ActionSet]

# 输入参数：
#   env: Environment - 游戏环境对象

# 返回值：
#   ActionSet - 行动集合

# 策略逻辑：
#   1. 使用蒙特卡洛树搜索 (MCTS)
#   2. 随机展开游戏树
#   3. 选择胜率最高的行动
```

### 6.3 辅助方法

#### calculate_distance - 计算距离

```python
distance = StrategyFactory.calculate_distance(p1: Point, p2: Point) -> float

# 参数：
#   p1: Point - 起点
#   p2: Point - 终点

# 返回值：
#   float - 曼哈顿距离 (|x1-x2| + |y1-y2|)
```

### 6.4 选手自定义策略示例

```python
# 在 strategy_factory.py 中添加你的策略

@staticmethod
def get_my_init_strategy() -> Callable[[InitGameMessage], List[PieceArg]]:
    """我的初始化策略"""
    def strategy(init_message: InitGameMessage) -> List[PieceArg]:
        piece_args = []
        
        for i in range(init_message.piece_cnt):
            arg = PieceArg()
            # 自定义属性分配
            arg.strength = 15
            arg.dexterity = 10
            arg.intelligence = 5
            arg.equip = Point(1, 2)  # 武器1+防具2
            arg.pos = Point(5 + i, 5)  # 自定义位置
            
            piece_args.append(arg)
        
        return piece_args
    
    return strategy


@staticmethod
def get_my_action_strategy() -> Callable[[Environment], ActionSet]:
    """我的行动策略"""
    def strategy(env: Environment) -> ActionSet:
        action = ActionSet()
        current = env.current_piece
        
        # 获取合法移动
        moves = get_legal_moves(env)
        
        # 获取可攻击目标
        targets = get_attackable_targets(env)
        
        # 你的策略逻辑
        if targets:
            action.attack = True
            action.attack_context = AttackContext()
            action.attack_context.attacker = current
            action.attack_context.target = targets[0]
        
        if moves:
            action.move = True
            action.move_target = moves[0]
        
        return action
    
    return strategy
```

---

## 7. 输入方法

### 7.1 输入方法接口

```python
from local_input import IInputMethod, FunctionInputMethod, InputMethodManager

# 创建函数式输入方法
def my_init_handler(init_message):
    # 返回 List[PieceArg]
    pass

def my_action_handler(env):
    # 返回 ActionSet
    pass

input_method = FunctionInputMethod(my_init_handler, my_action_handler)

# 设置到管理器
manager = InputMethodManager(env)
manager.set_function_input_method(player_id, my_init_handler, my_action_handler)
```

### 7.2 InputMethodManager 方法

```python
manager = InputMethodManager(env)

# 设置玩家的输入方法
manager.set_input_method(player_id: int, input_method: IInputMethod)

# 获取玩家的输入方法
method = manager.get_input_method(player_id: int) -> IInputMethod

# 设置控制台输入
manager.set_console_input_method(player_id: int)

# 设置远程输入
manager.set_remote_input_method(player_id: int)

# 检查是否远程输入
is_remote = manager.is_remote_input(player_id: int) -> bool
```

---

## 8. 枚举类型

### 8.1 AttackType - 攻击类型

```python
from utils import AttackType

AttackType.PHYSICAL   # 物理攻击
AttackType.SPELL      # 法术攻击
AttackType.EXCELLENCE # 卓越攻击
```

### 8.2 SpellEffectType - 法术效果类型

```python
from utils import SpellEffectType

SpellEffectType.DAMAGE   # 伤害
SpellEffectType.HEAL     # 治疗
SpellEffectType.BUFF     # 增益
SpellEffectType.DEBUFF   # 减益
SpellEffectType.MOVE     # 移动
```

### 8.3 DamageType - 伤害类型

```python
from utils import DamageType

DamageType.FIRE       # 火焰
DamageType.ICE        # 冰霜
DamageType.LIGHTNING  # 闪电
DamageType.PHYSICAL   # 物理
DamageType.PURE       # 纯粹
DamageType.NONE       # 无
```

### 8.4 TargetType - 目标类型

```python
from utils import TargetType

TargetType.SINGLE   # 单体
TargetType.AREA     # 范围
TargetType.SELF     # 自身
TargetType.CHAIN    # 链式
```

---

## 9. 法术系统

### 9.1 Spell - 法术

```python
from utils import Spell

spell = Spell(
    id=0,
    name="",
    description="",
    effect_type=None,
    damage_type=None,
    base_value=0,
    range_=0,
    area_radius=0,
    spell_cost=0,
    base_lifespan=0,
    is_area_effect=False,
    is_delay_spell=False,
    is_locking_spell=False
)

# 属性
spell.id              # int - 法术ID
spell.name            # str - 法术名称
spell.description     # str - 描述
spell.effect_type     # SpellEffectType - 效果类型
spell.damage_type     # DamageType - 伤害类型
spell.base_value      # int - 基础值
spell.range           # int - 施法范围
spell.area_radius     # int - 范围半径
spell.spell_cost      # int - 法术位消耗
spell.base_lifespan   # int - 持续回合数
spell.is_area_effect  # bool - 是否为范围法术
spell.is_delay_spell  # bool - 是否为延时法术
spell.is_locking_spell # bool - 是否为锁定法术
```

### 9.2 SpellFactory - 法术工厂

```python
from utils import SpellFactory

# 获取所有法术
spells = SpellFactory.get_all_spells() -> List[Spell]

# 根据ID获取法术
spell = SpellFactory.get_spell_by_id(spell_id: int) -> Optional[Spell]

# 获取棋子可用的法术
available_spells = SpellFactory.get_available_spells(piece: Piece) -> List[Spell]
```

### 9.3 内置法术列表

| ID | 名称 | 效果类型 | 伤害类型 | 基础值 | 范围 | 消耗 |
|----|------|----------|----------|--------|------|------|
| 1 | Fireball | DAMAGE | FIRE | 30 | 2 | 1 |
| 2 | Heal | HEAL | NONE | 30 | 2 | 1 |
| 3 | Arrow Hit | DAMAGE | PHYSICAL | 30 | 1 | 1 |
| 4 | Trap | DAMAGE | PHYSICAL | 30 | 1 | 1 |
| 5 | Teleport | MOVE | PHYSICAL | 30 | 100 | 1 |

---

## 附录：属性计算公式

### 生命值
- `max_health = 30 + strength * 2`

### 行动点
- 力量 ≤ 13: 1 点
- 力量 ≤ 21: 2 点
- 力量 > 21: 3 点

### 法术位
- 智力 ≤ 3: 1 个
- 智力 ≤ 7: 2 个
- 智力 ≤ 12: 3 个
- 智力 ≤ 16: 5 个
- 智力 ≤ 21: 8 个
- 智力 > 21: 9 个

### 移动力
- `max_movement = dexterity + 0.5 * strength + 10`

### 武器属性
| 类型 | 名称 | 物理伤害 | 范围 | 备注 |
|------|------|----------|------|------|
| 1 | 长剑 | 8 | 5 | - |
| 2 | 短剑 | 10 | 3 | - |
| 3 | 弓 | 16 | 9 | - |
| 4 | 法杖 | 0 | 12 | 普通攻击造成固定 4 点真实伤害（不扣除抗性） |

### 防具属性
| 类型 | 名称 | 物理抗性 | 移动力影响 |
|------|------|----------|------------|
| 1 | 轻甲 | 8 | +3 |
| 2 | 中甲 | 15 | 0 |
| 3 | 重甲 | 23 | -3 |

---

*文档版本: 2.1 (THUAI9)*
*最后更新: 2026年4月*