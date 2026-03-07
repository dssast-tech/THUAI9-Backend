# Real-THUAI8 AI 开发者文档

## 环境概述

Real-THUAI8 是一个回合制策略游戏，玩家通过编写 AI 来控制棋子在棋盘上移动、攻击和施法。本文档介绍了开发 AI 时可能用到的主要接口。

## 核心类

### Environment

游戏环境的主类，包含了游戏的所有状态和逻辑。

#### 状态查询

```python
def get_state_score(self) -> float:
    """获取当前游戏状态的评分
    
    评分考虑因素：
    1. 双方棋子的生命值
    2. 棋子的位置优势（基于高度和控制区域）
    3. 剩余行动点和法术位
    4. 装备和属性加成
    
    Returns:
        float: 状态评分。正值表示对当前行动方有利，负值表示不利
    """

def get_legal_moves(self, piece: Piece = None) -> List[Point]:
    """获取指定棋子（或当前棋子）的所有合法移动位置
    
    Args:
        piece: 要检查的棋子，如果为None则使用当前行动棋子
        
    Returns:
        List[Point]: 所有合法的移动目标位置
    """

def get_attackable_targets(self, piece: Piece = None) -> List[Piece]:
    """获取指定棋子（或当前棋子）可攻击的所有目标
    
    Args:
        piece: 要检查的棋子，如果为None则使用当前行动棋子
        
    Returns:
        List[Piece]: 所有可攻击的目标棋子
    """
```

#### 状态模拟

```python
def simulate_move(self, piece: Piece, target: Point) -> bool:
    """模拟移动棋子（用于AI决策树搜索），不改变实际游戏状态
    
    Args:
        piece: 要移动的棋子
        target: 目标位置
        
    Returns:
        bool: 移动是否合法
    """

def simulate_attack(self, attacker: Piece, target: Piece) -> float:
    """模拟攻击（用于AI决策树搜索），返回预期伤害
    
    Args:
        attacker: 攻击方棋子
        target: 防守方棋子
        
    Returns:
        float: 预期伤害值
    """

def fork(self) -> 'Environment':
    """创建当前环境的深拷贝，用于模拟和搜索
    
    Returns:
        Environment: 一个新的、独立的环境副本
    """
```

### Board

棋盘类，处理地形、移动和位置相关的逻辑。

```python
def valid_target(self, piece: Piece, movement: float) -> List[List[int]]:
    """获取有效目标位置
    
    Args:
        piece: 要移动的棋子
        movement: 可用的移动力
        
    Returns:
        List[List[int]]: 二维数组，表示每个位置的移动消耗。-1表示不可到达
    """

def is_in_attack_range(self, attacker: Piece, target: Piece) -> bool:
    """检查目标是否在攻击范围内
    
    Args:
        attacker: 攻击方棋子
        target: 防守方棋子
        
    Returns:
        bool: 是否在攻击范围内
    """

def get_height(self, point: Point) -> int:
    """获取指定位置的高度
    
    Args:
        point: 要查询的位置
        
    Returns:
        int: 该位置的高度值
    """
```

### Piece

棋子类，包含棋子的所有属性和状态。

```python
class Piece:
    health: int          # 当前生命值
    max_health: int      # 最大生命值
    physical_resist: int # 物理抗性
    magic_resist: int    # 魔法抗性
    physical_damage: int # 物理伤害
    magic_damage: int    # 魔法伤害
    action_points: int   # 当前行动点
    spell_slots: int     # 当前法术位
    movement: float      # 当前移动力
    position: Point      # 当前位置
    height: int         # 当前高度
    attack_range: int   # 攻击范围
    team: int           # 队伍编号
    is_alive: bool      # 是否存活
```

## 策略开发

### 策略接口

所有策略都应该实现以下接口：

```python
def strategy(env: Environment) -> ActionSet:
    """根据当前环境状态决定行动
    
    Args:
        env: 当前游戏环境
        
    Returns:
        ActionSet: 决定执行的行动
    """
```

### ActionSet

行动集合类，描述一个完整的行动。

```python
class ActionSet:
    move: bool                    # 是否移动
    move_target: Optional[Point]  # 移动目标位置
    attack: bool                  # 是否攻击
    attack_context: AttackContext # 攻击上下文
    spell: bool                   # 是否施法
    spell_context: SpellContext   # 法术上下文
```

## 示例策略

### 1. 简单进攻策略

```python
def aggressive_strategy(env: Environment) -> ActionSet:
    action = ActionSet()
    current_piece = env.current_piece
    
    # 获取最近的敌人
    targets = env.get_attackable_targets()
    if targets:
        # 有可攻击目标就攻击
        action.attack = True
        action.attack_context = AttackContext()
        action.attack_context.attacker = current_piece
        action.attack_context.target = targets[0]
    else:
        # 没有目标就向敌人移动
        moves = env.get_legal_moves()
        if moves:
            action.move = True
            action.move_target = moves[0]
            
    return action
```

### 2. AlphaBeta 策略

参见 `StrategyFactory.get_alpha_beta_action_strategy()`

### 3. MCTS 策略

参见 `StrategyFactory.get_mcts_action_strategy()`

## 开发建议

1. 使用 `fork()` 进行状态模拟，不要直接修改环境状态
2. 利用 `get_state_score()` 评估局面
3. 考虑高度差和地形的影响
4. 合理分配行动点和法术位
5. 注意攻击范围和移动力的限制

## 调试技巧

1. 使用 `visualize_board()` 查看当前棋盘状态
2. 检查 `is_game_over` 和胜负判定
3. 观察 `action_queue` 中的行动顺序
4. 利用 `simulate_move()` 和 `simulate_attack()` 预测行动效果