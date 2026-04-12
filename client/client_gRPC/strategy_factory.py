from typing import Callable, List
import math
from dataclasses import dataclass
from env import *
from converter import *
from utils import *
from message_pb2 import _InitResponse

# 控制 MCTS 是否输出调试日志，设为 False 可关闭所有 [MCTS] 输出
MCTS_VERBOSE: bool = False

class StrategyFactory:
    """策略工厂类 - 提供不同的游戏策略"""
    
    @staticmethod
    def calculate_distance(p1: Point, p2: Point) -> float:
        """计算两点之间的距离"""
        return abs(p1.x - p2.x) + abs(p1.y - p2.y)

    @staticmethod
    def get_aggressive_init_strategy() -> Callable[['InitGameMessage'], List[PieceArg]]:
        """获取攻击型初始化策略"""
        def strategy(init_message: 'InitGameMessage') -> List[PieceArg]:
            piece_args = []
            
            # 攻击型配置：高力量，中敏捷，低智力
            for i in range(init_message.piece_cnt):
                arg = PieceArg()
                arg.strength = 20      # 高力量
                arg.dexterity = 8      # 中敏捷
                arg.intelligence = 2    # 低智力
                arg.equip = Point(2, 3)  # 短剑+重甲 (高伤害+高防御)
                
                # 设置位置 - 偏向前线位置，确保位置有效
                if init_message.id == 1:  # 第一个玩家
                    # 从前线开始尝试找到有效位置
                    for y in range(5, 0, -1):  # 从前线向后尝试
                        for x in range(2, init_message.board.width - 2):
                            pos = Point(x, y)
                            if (init_message.board.is_within_bounds(pos) and 
                                init_message.board.grid[pos.x][pos.y].state == 1 and  # 确保格子可用
                                y < init_message.board.boarder):  # 确保在边界线以下
                                arg.pos = pos
                                piece_args.append(arg)
                                break
                        if len(piece_args) == i + 1:  # 如果已经找到位置就跳出
                            break
                else:  # 第二个玩家
                    # 从前线开始尝试找到有效位置
                    for y in range(init_message.board.height - 6, init_message.board.height):
                        for x in range(init_message.board.width - 3, 2, -1):
                            pos = Point(x, y)
                            if (init_message.board.is_within_bounds(pos) and 
                                init_message.board.grid[pos.x][pos.y].state == 1 and  # 确保格子可用
                                y > init_message.board.boarder):  # 确保在边界线以上
                                arg.pos = pos
                                piece_args.append(arg)
                                break
                        if len(piece_args) == i + 1:  # 如果已经找到位置就跳出
                            break
                
                # 如果没有找到有效位置，使用默认位置（这种情况不应该发生，因为棋盘应该有足够的空间）
                if len(piece_args) != i + 1:
                    if init_message.id == 1:
                        arg.pos = Point(2 + i * 2, 2)
                    else:
                        arg.pos = Point(init_message.board.width - 3 - i * 2, init_message.board.height - 3)
                    piece_args.append(arg)
            
            return piece_args
        
        return strategy

    @staticmethod
    def get_defensive_init_strategy() -> Callable[['InitGameMessage'], List[PieceArg]]:
        """获取防御型初始化策略"""
        def strategy(init_message: 'InitGameMessage') -> List[PieceArg]:
            piece_args = []
            
            # 防御型配置：中力量，高敏捷，中智力
            for i in range(init_message.piece_cnt):
                arg = PieceArg()
                arg.strength = 5       # 低力量
                arg.dexterity = 15     # 高敏捷
                arg.intelligence = 10   # 中智力
                arg.equip = Point(3, 1)  # 弓+轻甲 (远程+机动性)
                
                # 设置位置 - 偏向后方位置，确保位置有效
                if init_message.id == 1:  # 第一个玩家
                    # 从后方开始尝试找到有效位置
                    for y in range(3, init_message.board.boarder):
                        for x in range(3, init_message.board.width - 3):
                            pos = Point(x, y)
                            if (init_message.board.is_within_bounds(pos) and 
                                init_message.board.grid[pos.x][pos.y].state == 1 and  # 确保格子可用
                                y < init_message.board.boarder):  # 确保在边界线以下
                                arg.pos = pos
                                piece_args.append(arg)
                                break
                        if len(piece_args) == i + 1:  # 如果已经找到位置就跳出
                            break
                else:  # 第二个玩家
                    # 从后方开始尝试找到有效位置
                    for y in range(init_message.board.height - 4, init_message.board.boarder, -1):
                        for x in range(init_message.board.width - 4, 3, -1):
                            pos = Point(x, y)
                            if (init_message.board.is_within_bounds(pos) and 
                                init_message.board.grid[pos.x][pos.y].state == 1 and  # 确保格子可用
                                y > init_message.board.boarder):  # 确保在边界线以上
                                arg.pos = pos
                                piece_args.append(arg)
                                break
                        if len(piece_args) == i + 1:  # 如果已经找到位置就跳出
                            break
                
                # 如果没有找到有效位置，使用默认位置（这种情况不应该发生，因为棋盘应该有足够的空间）
                if len(piece_args) != i + 1:
                    if init_message.id == 1:
                        arg.pos = Point(3 + i * 3, 2)
                    else:
                        arg.pos = Point(init_message.board.width - 4 - i * 3, init_message.board.height - 3)
                    piece_args.append(arg)
            
            return piece_args
        
        return strategy

    @staticmethod
    def get_aggressive_action_strategy() -> Callable[[Environment], ActionSet]:
        """获取攻击型行动策略 - 主动接近并攻击敌人"""
        def strategy(env: Environment) -> ActionSet:
            action = ActionSet()
            current_piece = env.current_piece
            
            # 寻找最近的敌人
            target_enemy = None
            nearest_distance = float('inf')
            
            for piece in env.action_queue:
                if piece.team != current_piece.team and piece.is_alive:
                    distance = StrategyFactory.calculate_distance(
                        Point(current_piece.position.x, current_piece.position.y),
                        Point(piece.position.x, piece.position.y)
                    )
                    if distance < nearest_distance:
                        nearest_distance = distance
                        target_enemy = piece
            
            # 没有敌人，不执行任何动作
            if target_enemy is None:
                action.move = False
                action.attack = False
                action.spell = False
                return action
            
            # 移动决策 - 向目标敌人移动
            # 获取所有合法移动位置
            legal_moves = env.get_legal_moves()
            if legal_moves:
                # 找到最接近敌人的合法移动位置
                best_move = None
                min_distance = float('inf')
                for move in legal_moves:
                    distance = StrategyFactory.calculate_distance(move, target_enemy.position)
                    if distance < min_distance:
                        min_distance = distance
                        best_move = move
                
                if best_move:
                    action.move = True
                    action.move_target = best_move
                else:
                    action.move = False
            else:
                action.move = False
            
            # 如果已经在攻击范围内，则攻击
            if nearest_distance <= current_piece.attack_range:
                action.attack = True
                action.attack_context = AttackContext()
                action.attack_context.attacker = current_piece
                action.attack_context.target = target_enemy
                action.attack_context.attackPosition = current_piece.position
            else:
                action.attack = False
            
            # 暂不使用法术
            action.spell = False
            
            return action
        
        return strategy

    @staticmethod
    def get_defensive_action_strategy() -> Callable[[Environment], ActionSet]:
        """获取防御型行动策略 - 保持距离，使用远程攻击"""
        def strategy(env: Environment) -> ActionSet:
            action = ActionSet()
            current_piece = env.current_piece
            
            # 寻找最近的敌人
            target_enemy = None
            nearest_distance = float('inf')
            
            for piece in env.action_queue:
                if piece.team != current_piece.team and piece.is_alive:
                    distance = StrategyFactory.calculate_distance(
                        Point(current_piece.position.x, current_piece.position.y),
                        Point(piece.position.x, piece.position.y)
                    )
                    if distance < nearest_distance:
                        nearest_distance = distance
                        target_enemy = piece
            
            # 没有敌人，不执行任何动作
            if target_enemy is None:
                action.move = False
                action.attack = False
                action.spell = False
                return action
            
            # 移动决策 - 保持在攻击范围内，但不要太近
            # 获取所有合法移动位置
            legal_moves = env.get_legal_moves()
            if legal_moves:
                # 理想距离是攻击范围的70%
                ideal_distance = current_piece.attack_range * 0.7
                
                # 找到最接近理想距离的合法移动位置
                best_move = None
                min_distance_diff = float('inf')
                
                for move in legal_moves:
                    distance_to_enemy = StrategyFactory.calculate_distance(move, target_enemy.position)
                    distance_diff = abs(distance_to_enemy - ideal_distance)
                    
                    if distance_diff < min_distance_diff:
                        # 如果太近了，只考虑能让我们远离的移动
                        if nearest_distance < ideal_distance - 2:
                            if distance_to_enemy > nearest_distance:
                                min_distance_diff = distance_diff
                                best_move = move
                        # 如果太远了，只考虑能让我们靠近的移动
                        elif nearest_distance > ideal_distance + 2:
                            if distance_to_enemy < nearest_distance:
                                min_distance_diff = distance_diff
                                best_move = move
                        # 如果在理想范围附近，选择最接近理想距离的位置
                        else:
                            min_distance_diff = distance_diff
                            best_move = move
                
                if best_move:
                    action.move = True
                    action.move_target = best_move
                else:
                    action.move = False
            else:
                action.move = False
            
            # 如果在攻击范围内，则攻击
            if nearest_distance <= current_piece.attack_range:
                action.attack = True
                action.attack_context = AttackContext()
                action.attack_context.attacker = current_piece
                action.attack_context.target = target_enemy
                action.attack_context.attackPosition = current_piece.position
            else:
                action.attack = False
            
            # 暂不使用法术
            action.spell = False
            
            return action
        
        return strategy

    @staticmethod
    def get_random_init_strategy() -> Callable[[_InitResponse], List[PieceArg]]:
        """随机选择一个初始化策略"""
        import random
        strategies = [
            StrategyFactory.get_aggressive_init_strategy(),
            StrategyFactory.get_defensive_init_strategy()
        ]
        return random.choice(strategies)

    @staticmethod
    def get_random_action_strategy() -> Callable[[Environment], ActionSet]:
        """随机选择一个行动策略"""
        import random
        strategies = [
            StrategyFactory.get_aggressive_action_strategy(),
            StrategyFactory.get_defensive_action_strategy()
        ]
        return random.choice(strategies)

    @staticmethod
    def get_alpha_beta_action_strategy(max_depth: int = 3) -> Callable[[Environment], ActionSet]:
        """获取基于AlphaBeta剪枝的行动策略
        
        Args:
            max_depth: 最大搜索深度
            
        Returns:
            Callable[[Environment], ActionSet]: 策略函数
        """
        def alpha_beta(env: Environment, depth: int, alpha: float, beta: float, maximizing: bool) -> Tuple[float, Optional[ActionSet]]:
            if depth == 0 or env.is_game_over:
                return env.get_state_score(), None
                
            current_piece = env.current_piece
            if maximizing:
                max_eval = float('-inf')
                best_action = None
                
                # 获取所有可能的行动
                legal_moves = env.get_legal_moves()
                attackable_targets = env.get_attackable_targets()
                
                # 获取当前棋子可用的法术
                spells = env.get_available_spells(current_piece)
                
                # 尝试每个可能的行动组合
                for move in [None] + legal_moves:
                    # 如果已经没有行动点，跳过移动
                    if move is not None and current_piece.action_points <= 0:
                        continue
                        
                    for target in [None] + attackable_targets:
                        # 如果已经没有行动点，跳过攻击
                        if target is not None and current_piece.action_points <= 0:
                            continue
                            
                        for spell in [None] + spells:
                            # 如果已经没有行动点或法术位，跳过法术
                            if spell is not None and (current_piece.action_points <= 0 or current_piece.spell_slots <= 0):
                                continue
                                
                            action = ActionSet()
                            next_env = env.fork()
                            remaining_points = current_piece.action_points
                            
                            # 设置移动
                            if move is not None and remaining_points > 0:
                                action.move = True
                                action.move_target = move
                                remaining_points -= 1
                            else:
                                action.move = False
                            
                            # 设置攻击
                            if target is not None and remaining_points > 0:
                                action.attack = True
                                action.attack_context = AttackContext()
                                action.attack_context.attacker = current_piece
                                action.attack_context.target = target
                                remaining_points -= 1
                            else:
                                action.attack = False
                            
                            # 设置法术
                            if spell is not None and remaining_points > 0 and current_piece.spell_slots > 0:
                                action.spell = True
                                action.spell_context = SpellContext()
                                action.spell_context.caster = current_piece
                                action.spell_context.target = target if target else current_piece  # 如果没有目标就施放在自己身上
                                action.spell_context.spell = spell
                                action.spell_context.target_area = Area(
                                    current_piece.position.x,
                                    current_piece.position.y,
                                    2  # 默认范围
                                )
                                remaining_points -= 1
                            else:
                                action.spell = False
                            
                            # 模拟行动
                            next_env.execute_player_action(action)
                            
                            eval, _ = alpha_beta(next_env, depth - 1, alpha, beta, False)
                            if eval > max_eval:
                                max_eval = eval
                                best_action = action
                                
                            alpha = max(alpha, eval)
                            if beta <= alpha:
                                break
                        if beta <= alpha:
                            break
                    if beta <= alpha:
                        break
                            
                return max_eval, best_action
            else:
                min_eval = float('inf')
                best_action = None
                
                # 获取所有可能的行动
                legal_moves = env.get_legal_moves()
                attackable_targets = env.get_attackable_targets()
                
                # 创建基础法术列表
                spells = []
                if current_piece.spell_slots > 0:
                    spells.extend([
                        Spell("Damage", "Damage", 10, False),
                        Spell("Heal", "Heal", 8, False),
                        Spell("Buff", "Buff", 5, False),
                        Spell("Debuff", "Debuff", 3, False)
                    ])
                
                # 尝试每个可能的行动组合
                for move in [None] + legal_moves:
                    # 如果已经没有行动点，跳过移动
                    if move is not None and current_piece.action_points <= 0:
                        continue
                        
                    for target in [None] + attackable_targets:
                        # 如果已经没有行动点，跳过攻击
                        if target is not None and current_piece.action_points <= 0:
                            continue
                            
                        for spell in [None] + spells:
                            # 如果已经没有行动点或法术位，跳过法术
                            if spell is not None and (current_piece.action_points <= 0 or current_piece.spell_slots <= 0):
                                continue
                                
                            action = ActionSet()
                            next_env = env.fork()
                            remaining_points = current_piece.action_points
                            
                            # 设置移动
                            if move is not None and remaining_points > 0:
                                action.move = True
                                action.move_target = move
                                remaining_points -= 1
                            else:
                                action.move = False
                            
                            # 设置攻击
                            if target is not None and remaining_points > 0:
                                action.attack = True
                                action.attack_context = AttackContext()
                                action.attack_context.attacker = current_piece
                                action.attack_context.target = target
                                remaining_points -= 1
                            else:
                                action.attack = False
                            
                            # 设置法术
                            if spell is not None and remaining_points > 0 and current_piece.spell_slots > 0:
                                # 获取法术可选目标
                                spell_targets = env.get_spell_targets(spell, current_piece)
                                if not spell_targets and not spell.is_area_effect:
                                    continue
                                    
                                action.spell = True
                                action.spell_context = SpellContext()
                                action.spell_context.caster = current_piece
                                action.spell_context.spell = spell
                                
                                # 设置目标和范围
                                if spell.is_area_effect:
                                    # 范围法术以当前位置为中心
                                    action.spell_context.target = None
                                    action.spell_context.target_area = Area(
                                        current_piece.position.x,
                                        current_piece.position.y,
                                        spell.area_radius
                                    )
                                else:
                                    # 单体法术选择最佳目标
                                    best_target = None
                                    if spell.effect_type in [SpellEffectType.DAMAGE, SpellEffectType.DEBUFF]:
                                        # 选择生命值最低的敌人
                                        best_target = min(spell_targets, key=lambda p: p.health)
                                    elif spell.effect_type in [SpellEffectType.HEAL, SpellEffectType.BUFF]:
                                        # 选择生命值损失最多的友军
                                        best_target = min(spell_targets, key=lambda p: p.health / p.max_health)
                                    elif spell.effect_type == SpellEffectType.MOVE:
                                        best_target = current_piece
                                        
                                    action.spell_context.target = best_target
                                    action.spell_context.target_area = Area(
                                        best_target.position.x,
                                        best_target.position.y,
                                        0
                                    )
                                    
                                remaining_points -= 1
                            else:
                                action.spell = False
                            
                            # 模拟行动
                            next_env.execute_player_action(action)
                            
                            eval, _ = alpha_beta(next_env, depth - 1, alpha, beta, True)
                            if eval < min_eval:
                                min_eval = eval
                                best_action = action
                                
                            beta = min(beta, eval)
                            if beta <= alpha:
                                break
                        if beta <= alpha:
                            break
                    if beta <= alpha:
                        break
                            
                return min_eval, best_action
        
        def strategy(env: Environment) -> ActionSet:
            _, best_action = alpha_beta(env, max_depth, float('-inf'), float('inf'), True)
            return best_action if best_action is not None else ActionSet()
            
        return strategy
        
  
    def get_mcts_action_strategy(simulation_count: int = 10) -> Callable[[Environment], ActionSet]:
        """获取基于MCTS的行动策略
        
        Args:
            simulation_count: 每个决策点的模拟次数
            
        Returns:
            Callable[[Environment], ActionSet]: 策略函数
        """
        class MCTSNode:
            def __init__(self, env: Environment, parent=None, action: Optional[ActionSet] = None):
                self.env = env
                self.parent = parent
                self.action = action
                self.children = []
                self.visits = 0
                self.value = 0.0
                
            def expand(self):
                """扩展当前节点"""
                current_piece = self.env.current_piece
                legal_moves = self.env.get_legal_moves()
                attackable_targets = self.env.get_attackable_targets()
                
                # 获取当前棋子可用的法术
                spells = self.env.get_available_spells(current_piece)
                
                # print(f"[MCTS] 开始生成动作组合:")
                # print(f"[MCTS] - 可移动位置: {len(legal_moves)}")
                # print(f"[MCTS] - 可攻击目标: {len(attackable_targets)}")
                # print(f"[MCTS] - 可用法术: {len(spells)}")
                # print(f"[MCTS] - 当前行动点: {current_piece.action_points}")

                # 生成所有可能的行动组合
                for move in [None] + legal_moves:
                    # 如果已经没有行动点，跳过移动
                    if move is not None and current_piece.action_points <= 0:
                        if MCTS_VERBOSE: print("[MCTS] 跳过移动：没有足够的行动点")
                        continue
                        
                    for target in [None] + attackable_targets:
                        # 如果已经没有行动点，跳过攻击
                        if target is not None and current_piece.action_points <= 0:
                            if MCTS_VERBOSE: print("[MCTS] 跳过攻击：没有足够的行动点")
                            continue
                            
                        for spell in [None] + spells:
                            # 如果已经没有行动点或法术位，跳过法术
                            if spell is not None and (current_piece.action_points <= 0 or current_piece.spell_slots <= 0):
                                if MCTS_VERBOSE: print("[MCTS] 跳过法术：没有足够的资源")
                                continue
                                
                            action = ActionSet()
                            next_env = self.env.fork()
                            remaining_points = current_piece.action_points
                            has_action = False  # 标记是否有任何动作
                            
                            # 设置移动
                            if move is not None and remaining_points > 0:
                                action.move = True
                                action.move_target = move
                                remaining_points -= 1
                                has_action = True
                                if MCTS_VERBOSE: print(f"[MCTS] 添加移动到 ({move.x}, {move.y})")
                            else:
                                action.move = False
                            
                            # 设置攻击
                            if target is not None and remaining_points > 0:
                                action.attack = True
                                action.attack_context = AttackContext()
                                action.attack_context.attacker = current_piece
                                action.attack_context.target = target
                                remaining_points -= 1
                                has_action = True
                                if MCTS_VERBOSE: print(f"[MCTS] 添加攻击目标 {target.id}")
                            else:
                                action.attack = False
                            
                            # 设置法术
                            if spell is not None and remaining_points > 0 and current_piece.spell_slots > 0:
                                # 获取法术可选目标
                                spell_targets = self.env.get_spell_targets(spell, current_piece)
                                if not spell_targets and not spell.is_area_effect:
                                    if MCTS_VERBOSE: print("[MCTS] 跳过法术：没有有效目标")
                                    continue
                                    
                                has_action = True
                                    
                                action.spell = True
                                action.spell_context = SpellContext()
                                action.spell_context.caster = current_piece
                                action.spell_context.spell = spell
                                if MCTS_VERBOSE: print(f"[MCTS] 添加法术 {spell.name}")
                                
                                # 设置目标和范围
                                if spell.is_area_effect:
                                    # 范围法术以当前位置为中心
                                    action.spell_context.target = None
                                    action.spell_context.target_area = Area(
                                        current_piece.position.x,
                                        current_piece.position.y,
                                        spell.area_radius
                                    )
                                else:
                                    # 单体法术选择最佳目标
                                    best_target = None
                                    if spell.effect_type in [SpellEffectType.DAMAGE, SpellEffectType.DEBUFF]:
                                        # 选择生命值最低的敌人
                                        best_target = min(spell_targets, key=lambda p: p.health)
                                    elif spell.effect_type in [SpellEffectType.HEAL, SpellEffectType.BUFF]:
                                        # 选择生命值损失最多的友军
                                        best_target = min(spell_targets, key=lambda p: p.health / p.max_health)
                                    elif spell.effect_type == SpellEffectType.MOVE:
                                        best_target = current_piece
                                        
                                    action.spell_context.target = best_target
                                    action.spell_context.target_area = Area(
                                        best_target.position.x,
                                        best_target.position.y,
                                        spell.area_radius
                                    )
                                    
                                remaining_points -= 1
                            else:
                                action.spell = False
                            
                            # 如果有行动点但没有执行任何动作，跳过这个组合
                            if current_piece.action_points > 0 and not has_action:
                                if MCTS_VERBOSE: print("[MCTS] 跳过：有行动点但未执行任何动作")
                                continue
                                
                            # 创建子节点并执行完整的步进
                            if MCTS_VERBOSE: print(f"[MCTS] 尝试动作: {action}")
                            next_env.step_with_action(action)
                            child = MCTSNode(next_env, self, action)
                            self.children.append(child)
                            if MCTS_VERBOSE: print(f"[MCTS] 成功添加子节点，当前共有 {len(self.children)} 个子节点")
                        
            def select(self) -> 'MCTSNode':
                """选择最有希望的子节点"""
                if not self.children:
                    return self
                    
                # UCB1公式选择节点
                def ucb1(node: MCTSNode) -> float:
                    if node.visits == 0:
                        return float('inf')
                    return node.value / node.visits + math.sqrt(2 * math.log(self.visits) / node.visits)
                    
                return max(self.children, key=ucb1)
                
            def simulate(self) -> float:
                """模拟到游戏结束或达到最大步数
                
                Returns:
                    float: 1.0 表示当前行动方胜利，-1.0 表示对手胜利，
                          如果达到最大步数，则根据双方棋子血量总和判断胜负
                """
                sim_env = self.env.fork()
                max_steps = 50  # 最大模拟步数
                initial_team = sim_env.current_piece.team  # 记录当前行动方
                
                while not sim_env.is_game_over and max_steps > 0:
                    # 随机选择行动
                    legal_moves = sim_env.get_legal_moves()
                    attackable_targets = sim_env.get_attackable_targets()
                    
                    action = ActionSet()
                    
                    # 随机移动
                    if legal_moves and random.random() < 0.7:
                        action.move = True
                        action.move_target = random.choice(legal_moves)
                    else:
                        action.move = False
                        
                    # 随机攻击
                    if attackable_targets and random.random() < 0.8:
                        action.attack = True
                        action.attack_context = AttackContext()
                        action.attack_context.attacker = sim_env.current_piece
                        action.attack_context.target = random.choice(attackable_targets)
                    else:
                        action.attack = False
                        
                    action.spell = False
                    
                    # 执行模拟动作
                    sim_env.step_with_action(action)
                    max_steps -= 1
                
                # 如果游戏已经结束，直接根据胜负返回结果
                if sim_env.is_game_over:
                    team1_alive = any(p.is_alive for p in sim_env.player1.pieces)
                    team2_alive = any(p.is_alive for p in sim_env.player2.pieces)
                    if team1_alive and not team2_alive:
                        return 1.0 if initial_team == 1 else -1.0
                    elif team2_alive and not team1_alive:
                        return 1.0 if initial_team == 2 else -1.0
                    else:
                        return 0.0  # 平局
                
                # 如果没有执行任何动作，给予惩罚
                if not (action.move or action.attack or action.spell):
                    return -0.5  # 不行动的惩罚值
                
                # 如果达到最大步数，根据双方棋子血量总和判断
                team1_health = sum(p.health for p in sim_env.player1.pieces if p.is_alive)
                team2_health = sum(p.health for p in sim_env.player2.pieces if p.is_alive)
                
                if team1_health > team2_health:
                    return 1.0 if initial_team == 1 else -1.0
                elif team2_health > team1_health:
                    return 1.0 if initial_team == 2 else -1.0
                else:
                    return 0.0  # 血量相等，平局
                
            def backpropagate(self, value: float):
                """反向传播模拟结果"""
                node = self
                while node is not None:
                    node.visits += 1
                    node.value += value
                    node = node.parent
                    value = -value  # 对抗游戏中，父节点的收益是子节点的相反数
        
        def strategy(env: Environment) -> ActionSet:
            root = MCTSNode(env)
            
            # 运行MCTS
            for _ in range(simulation_count):
                node = root
                
                # 选择
                while node.children:
                    node = node.select()
                    
                # 扩展
                if node.visits > 0:
                    node.expand()
                    if node.children:
                        node = random.choice(node.children)
                        
                # 模拟
                value = node.simulate()
                
                # 反向传播
                node.backpropagate(value)
                
            # 选择访问次数最多的子节点对应的行动
            if not root.children:
                if MCTS_VERBOSE:
                    print("\n[MCTS] 警告: 没有生成任何子节点!")
                    print(f"[MCTS] 当前棋子: ID={env.current_piece.id if env.current_piece else None}")
                    print(f"[MCTS] 可移动位置数量: {len(env.get_legal_moves())}")
                    print(f"[MCTS] 可攻击目标数量: {len(env.get_attackable_targets())}")
                    print(f"[MCTS] 可用法术数量: {len(env.get_available_spells())}")
                    print(f"[MCTS] 当前行动点: {env.current_piece.action_points if env.current_piece else 0}")
                    print(f"[MCTS] 当前法术位: {env.current_piece.spell_slots if env.current_piece else 0}")
                return ActionSet()
                
            if MCTS_VERBOSE:
                print(f"\n[MCTS] 找到 {len(root.children)} 个可能的动作")
            best_child = max(root.children, key=lambda c: c.visits)
            if MCTS_VERBOSE:
                print(f"[MCTS] 选择最佳动作: 访问次数={best_child.visits}, 评分={best_child.value}")
                print(f"[MCTS] 动作详情:\n{best_child.action}")
            return best_child.action
        
        return strategy