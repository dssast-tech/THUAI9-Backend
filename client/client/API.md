# Real-THUAI8 AI 开发者文档

## 环境概述

Real-THUAI8 是一个回合制策略游戏，玩家通过编写 AI 来控制棋子在棋盘上移动、攻击和施法。本文档介绍了开发 AI 时可能用到的主要接口。

## 核心类

### Environment

游戏环境的主类，包含了游戏的所有状态和逻辑。

### strategy_utils（AI / 搜索辅助）

以下函数在 `strategy_utils` 中定义，第一个参数均为 `env: Environment`：

- `get_state_score(env) -> float`：局面启发式评分  
- `get_legal_moves(env, piece=None) -> List[Point]`：合法移动格  
- `get_attackable_targets(env, piece=None) -> List[Piece]`：可攻击目标  
- `simulate_move(env, piece, target) -> bool`：移动是否合法（不修改状态）  
- `simulate_attack(env, attacker, target) -> float`：预期物理伤害估计  
- `step_with_action(env, action)`：按完整回合步进执行动作（用于搜索）  
- `fork_environment(env) -> Environment`：环境深拷贝  

```python
from strategy_utils import (
    fork_environment,
    get_attackable_targets,
    get_legal_moves,
    get_state_score,
    simulate_attack,
    simulate_move,
    step_with_action,
)
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
    targets = get_attackable_targets(env)
    if targets:
        # 有可攻击目标就攻击
        action.attack = True
        action.attack_context = AttackContext()
        action.attack_context.attacker = current_piece
        action.attack_context.target = targets[0]
    else:
        # 没有目标就向敌人移动
        moves = get_legal_moves(env)
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

1. 使用 `fork_environment(env)` 进行状态模拟，不要直接修改环境状态
2. 利用 `get_state_score(env)` 评估局面
3. 考虑高度差和地形的影响
4. 合理分配行动点和法术位
5. 注意攻击范围和移动力的限制

## 调试技巧

1. 使用 `visualize_board()` 查看当前棋盘状态
2. 检查 `is_game_over` 和胜负判定
3. 观察 `action_queue` 中的行动顺序
4. 利用 `simulate_move(env, ...)` 和 `simulate_attack(env, ...)` 预测行动效果